"""
Sistema de gestión de sesiones para el Analista AI.

Este módulo maneja:
- Sesiones de usuario únicas
- Historial de conversaciones por sesión
- Almacenamiento de imágenes por sesión
- Contexto para análisis de seguimiento
"""

import uuid
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json


@dataclass
class Message:
    """Representa un mensaje en la conversación."""
    id: str
    role: str  # 'user' o 'assistant'
    content: str
    timestamp: datetime
    images: List[Dict[str, str]] = None  # Lista de imágenes asociadas al mensaje
    
    def to_dict(self) -> dict:
        """Convierte el mensaje a diccionario."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Crea un mensaje desde un diccionario."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Conversation:
    """Representa una conversación completa."""
    session_id: str
    messages: List[Message]
    created_at: datetime
    last_activity: datetime
    
    def add_message(self, role: str, content: str, images: List[Dict[str, str]] = None) -> Message:
        """Agrega un nuevo mensaje a la conversación."""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            images=images or []
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
        return message
    
    def get_context_messages(self, max_messages: int = 10) -> List[Message]:
        """Obtiene los últimos mensajes para contexto."""
        return self.messages[-max_messages:] if self.messages else []
    
    def to_dict(self) -> dict:
        """Convierte la conversación a diccionario."""
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }


class SessionManager:
    """
    Gestiona sesiones de conversación y almacenamiento de imágenes por sesión.
    """
    
    def __init__(self, session_timeout_hours: int = 24):
        self.sessions: Dict[str, Conversation] = {}
        self.session_images: Dict[str, Dict[str, Dict[str, str]]] = {}  # session_id -> image_id -> image_data
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def create_session(self) -> str:
        """Crea una nueva sesión y retorna el ID."""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        self.sessions[session_id] = Conversation(
            session_id=session_id,
            messages=[],
            created_at=now,
            last_activity=now
        )
        self.session_images[session_id] = {}
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Conversation]:
        """Obtiene una sesión por ID."""
        self._cleanup_expired_sessions()
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, images: List[Dict[str, str]] = None) -> Optional[Message]:
        """Agrega un mensaje a una sesión."""
        conversation = self.get_session(session_id)
        if not conversation:
            return None
        
        message = conversation.add_message(role, content, images)
        return message
    
    def get_conversation_context(self, session_id: str, max_messages: int = 6) -> List[Dict[str, str]]:
        """
        Obtiene el contexto de la conversación para el agente.
        
        Args:
            session_id: ID de la sesión
            max_messages: Máximo número de mensajes a incluir (por defecto 6 = 3 pares pregunta-respuesta)
            
        Returns:
            Lista de mensajes formateados para el contexto del agente
        """
        conversation = self.get_session(session_id)
        if not conversation:
            return []
        
        context_messages = conversation.get_context_messages(max_messages)
        
        # Formatear mensajes para el contexto
        formatted_context = []
        for msg in context_messages:
            formatted_context.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return formatted_context
    
    def store_image(self, session_id: str, image_base64: str, title: str, chart_type: str) -> str:
        """
        Almacena una imagen en la sesión específica.
        
        Args:
            session_id: ID de la sesión
            image_base64: String base64 de la imagen
            title: Título de la gráfica
            chart_type: Tipo de gráfica
            
        Returns:
            ID único para referenciar la imagen
        """
        if session_id not in self.session_images:
            self.session_images[session_id] = {}
        
        image_id = str(uuid.uuid4())[:8]
        self.session_images[session_id][image_id] = {
            'data': image_base64,
            'title': title,
            'type': chart_type
        }
        
        return image_id
    
    def get_session_images(self, session_id: str) -> Dict[str, Dict[str, str]]:
        """Obtiene todas las imágenes de una sesión."""
        return self.session_images.get(session_id, {}).copy()
    
    def clear_session_images(self, session_id: str):
        """Limpia las imágenes de una sesión específica."""
        if session_id in self.session_images:
            self.session_images[session_id].clear()
    
    def delete_session(self, session_id: str):
        """Elimina completamente una sesión."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_images:
            del self.session_images[session_id]
    
    def _cleanup_expired_sessions(self):
        """Limpia sesiones expiradas."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, conversation in self.sessions.items():
            if current_time - conversation.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión."""
        conversation = self.get_session(session_id)
        if not conversation:
            return {}
        
        return {
            'session_id': session_id,
            'created_at': conversation.created_at.isoformat(),
            'last_activity': conversation.last_activity.isoformat(),
            'message_count': len(conversation.messages),
            'images_count': len(self.session_images.get(session_id, {}))
        }
    
    def format_context_for_agent(self, session_id: str) -> str:
        """
        Formatea el contexto de la conversación para incluir en el prompt del agente.
        
        Returns:
            String formateado con el contexto de la conversación
        """
        context_messages = self.get_conversation_context(session_id)
        
        if not context_messages:
            return ""
        
        formatted_context = "\n🔄 CONTEXTO DE CONVERSACIÓN PREVIA:\n"
        formatted_context += "=" * 40 + "\n"
        
        for msg in context_messages:
            role_indicator = "👤 USUARIO" if msg['role'] == 'user' else "🤖 ASISTENTE"
            formatted_context += f"\n{role_indicator}: {msg['content']}\n"
        
        formatted_context += "\n" + "=" * 40 + "\n"
        formatted_context += "💡 INSTRUCCIÓN: Considera este contexto al responder la nueva pregunta del usuario.\n"
        formatted_context += "Si la pregunta actual se relaciona con análisis previos, haz referencia a ellos y construye sobre esa información.\n"
        formatted_context += "Si es un tema completamente nuevo, puedes ignorar el contexto previo.\n\n"
        
        return formatted_context


# Instancia global del gestor de sesiones
session_manager = SessionManager() 