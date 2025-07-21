# Prueba técnica Desarrollador/a de Inteligencia Artificial y Visualización de Datos para Colombia

**Duración estimada:** 1-3 horas

**Enfoque:** Backend, procesamiento de datos, integración con APIs de lenguaje natural

**Entrega:** Enviar un enlace a un video (YouTube, Loom, Drive, etc.) explicando el código, el proceso seguido y mostrando el resultado obtenido. También enviar link a repositorio con el código

---

### Objetivo general

Esta prueba busca evaluar la capacidad de la persona de forma básica para procesar datos tabulares, integrarse con APIs de lenguaje natural, y generar resultados útiles desde un enfoque automatizado e inteligente. 

---

### 1️⃣ PARTE 1 – Análisis de texto con modelo de lenguaje

Se entregarán uno o varios archivos `.csv` que contienen datos relacionados con alimentación y nutrición en Colombia. El objetivo es que, a partir de estos datos, la persona candidata diseñe un flujo que permita:

- Recibir preguntas formuladas en lenguaje natural (por ejemplo: *¿Cuáles fueron los departamentos con mayor inseguridad alimentaria en 2023?*, *¿Qué tendencia se observa en el acceso a programas de alimentación escolar?*) y entregar respuestas automáticas basadas en los datos.
- Generar un resumen general con insights principales derivados de los datos.
- Extraer de manera automática entre 5 y 10 palabras clave relevantes.

**Las preguntas deben poder ser formuladas de manera manual por el usuario, a través de un endpoint o función definida.** No deben ser generadas automáticamente.

### Archivos de entrada

Se entregarán como insumo uno o más archivos `.csv` con estructuras similares a las siguientes columnas:

```
departamento, municipio, año, indicador, valor, unidad
```

La persona podrá agregar ejemplos, transformar el formato o filtrar la información si lo considera necesario para cumplir el objetivo.

### Algunas APIs que puedes usar de forma gratuita:

- **OpenAI GPT-3.5 (vía OpenRouter):**
    
    https://openrouter.ai/docs (requiere clave gratuita)
    
- **Hugging Face Inference API (modelo `distilbart-cnn-12-6` o similar para resumen):**
    
    https://huggingface.co/docs/api-inference/index
    
- **Cohere API (text summarization, embeddings):**
    
    https://docs.cohere.com/docs/summarize
    
- **TextRazor (análisis semántico y extracción de keywords):**
    
    https://www.textrazor.com/
    

> ⚠️ Asegúrate de revisar los límites gratuitos o de prueba que ofrezca cada API. No es necesario ningún pago.
> 

---

### 2️⃣ PARTE 2 – Endpoint y flujo de procesamiento

Se debe crear un **script o pequeño API** que permita:

- Formular preguntas en lenguaje natural y recibir respuestas basadas en los datos entregados.
- Obtener un resumen general del conjunto de datos.
- Extraer automáticamente palabras clave relevantes.
- Consultar estadísticas básicas: número de registros, valores faltantes, indicadores disponibles, etc.

Se sugiere implementar el sistema usando **Python**, preferiblemente con **Flask** o **FastAPI**.

---

### 📤 Entrega

- Enlace de acceso a un repositorio público con el código fuente (GitHub, GitLab, etc.).
- Enlace a **video corto** (máx. 10 minutos) donde se:
    - Explique el enfoque y decisiones tomadas.
    - Justifiquen las herramientas utilizadas.
    - Demuestre el resultado y funcionamiento de la solución.
