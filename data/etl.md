# Propuesta de Esquema de Base de Datos Normalizado para Datos de Inseguridad Alimentaria

## 1. Introducción a la Normalización

La normalización de bases de datos es un proceso que organiza las columnas y tablas de una base de datos relacional para minimizar la redundancia de datos y mejorar la integridad de los datos. El objetivo es aislar los datos para que las adiciones, eliminaciones y modificaciones de un campo solo tengan que hacerse en un lugar de la base de datos. Esto reduce la posibilidad de inconsistencias y anomalías. Generalmente, se busca alcanzar al menos la Tercera Forma Normal (3NF), que asegura que:

1.  No hay grupos repetitivos de columnas.
2.  Todas las columnas no clave dependen de la clave primaria completa.
3.  Todas las columnas no clave dependen directamente de la clave primaria y no de otras columnas no clave.

## 2. Análisis de Entidades y Relaciones

Para diseñar un esquema normalizado, primero identificamos las entidades clave y sus relaciones a partir de los archivos Excel proporcionados:

*   **Entidades Geográficas:**
    *   **Nacional:** Un único nivel (Colombia).
    *   **Regional:** Varias regiones (e.g., Región Atlántica, Región Central).
    *   **Departamental:** Múltiples departamentos (e.g., Antioquia, Atlántico).
    *   **Municipal:** Múltiples municipios, cada uno perteneciente a un departamento.
*   **Entidades de Medición:**
    *   **Indicador:** La métrica que se está midiendo (e.g., "Inseguridad Alimentaria Grave", "Inseguridad Alimentaria Moderado o Grave", "Prevalencia de hogares en inseguridad alimentaria").
    *   **Tipo de Dato:** La naturaleza del valor (e.g., "Porcentaje", "Número").
    *   **Tipo de Medida:** La metodología o unidad (e.g., "Prevalencia").
*   **Valores de Datos:** Los valores numéricos (`dato_departamento`, `dato_municipio`, `dato_region`, `dato_nacional`) asociados a un indicador, un año y una entidad geográfica específica.

### Relaciones Identificadas:

*   Un `Municipio` pertenece a un `Departamento`.
*   Un `Departamento` puede pertenecer a una `Región` (aunque esta relación no es explícita en los datos actuales, es una jerarquía geográfica común).
*   Cada `Dato` se asocia a un `Año`, un `Indicador`, un `Tipo de Dato`, un `Tipo de Medida` y una entidad geográfica (Nacional, Regional, Departamental o Municipal).

## 3. Propuesta de Esquema Normalizado

Basándonos en el análisis anterior, proponemos el siguiente esquema de base de datos SQLite, diseñado para minimizar la redundancia y facilitar consultas eficientes.

### 3.1. Tabla `geografia`

Esta tabla almacenará la jerarquía geográfica de manera normalizada, evitando la repetición de nombres de departamentos, municipios y regiones. Se puede expandir para incluir IDs geográficos estándar si se dispone de ellos.

| Columna         | Tipo de Dato | Descripción                                     |
| :-------------- | :----------- | :---------------------------------------------- |
| `id_geografia`  | INTEGER      | Clave primaria (autoincremental).               |
| `nivel`         | TEXT         | Nivel geográfico (e.g., 'Nacional', 'Regional', 'Departamental', 'Municipal'). |
| `nombre`        | TEXT         | Nombre de la entidad geográfica (e.g., 'Colombia', 'Antioquia', 'Medellín', 'Región Atlántica'). |
| `id_padre`      | INTEGER      | Clave foránea a `id_geografia` para el nivel superior (e.g., el ID del departamento para un municipio, el ID de la región para un departamento). NULL para el nivel nacional. |
| `codigo_dane`   | TEXT         | (Opcional) Código DANE si está disponible.      |

**Ejemplo de datos:**

| id_geografia | nivel       | nombre             | id_padre | codigo_dane |
| :----------- | :---------- | :----------------- | :------- | :---------- |
| 1            | Nacional    | Colombia           | NULL     | NULL        |
| 2            | Regional    | Región Atlántica   | 1        | NULL        |
| 3            | Departamental | Antioquia          | 1        | NULL        |
| 4            | Departamental | Atlántico          | 2        | NULL        |
| 5            | Municipal   | Medellín           | 3        | NULL        |
| 6            | Municipal   | Barranquilla       | 4        | NULL        |

### 3.2. Tabla `indicadores`

Esta tabla almacenará las definiciones únicas de los indicadores, sus tipos de datos y tipos de medida.

| Columna          | Tipo de Dato | Descripción                                                                 |
| :--------------- | :----------- | :-------------------------------------------------------------------------- |
| `id_indicador`   | INTEGER      | Clave primaria (autoincremental).                                           |
| `nombre_indicador` | TEXT         | Nombre completo del indicador (e.g., "Inseguridad Alimentaria Grave", "Inseguridad Alimentaria Moderado o Grave", "Prevalencia de hogares en inseguridad alimentaria"). |
| `tipo_dato`      | TEXT         | Tipo de valor (e.g., "Porcentaje", "Número").                               |
| `tipo_de_medida` | TEXT         | Metodología o unidad de medida (e.g., "Prevalencia").                     |

**Ejemplo de datos:**

| id_indicador | nombre_indicador                                   | tipo_dato  | tipo_de_medida |
| :----------- | :------------------------------------------------- | :--------- | :------------- |
| 1            | Inseguridad Alimentaria Grave                      | Porcentaje | Prevalencia    |
| 2            | Inseguridad Alimentaria Moderado o Grave           | Porcentaje | Prevalencia    |
| 3            | Prevalencia de hogares en inseguridad alimentaria | porcentaje | Prevalencia    |

### 3.3. Tabla `datos_medicion`

Esta es la tabla de hechos principal, que contendrá los valores de los indicadores para cada combinación de geografía, año e indicador. Aquí es donde se almacenarán los `dato_departamento`, `dato_municipio`, `dato_region` y `dato_nacional` de manera eficiente.

| Columna         | Tipo de Dato | Descripción                                                                 |
| :-------------- | :----------- | :-------------------------------------------------------------------------- |
| `id_medicion`   | INTEGER      | Clave primaria (autoincremental).                                           |
| `id_geografia`  | INTEGER      | Clave foránea a `geografia.id_geografia` (representa el nivel de la medición: nacional, regional, departamental o municipal). |
| `id_indicador`  | INTEGER      | Clave foránea a `indicadores.id_indicador`.                                 |
| `año`           | INTEGER      | Año de la medición.                                                         |
| `valor`         | REAL         | El valor numérico del indicador para la `id_geografia` y `año` dados. Este campo reemplaza `dato_departamento`, `dato_municipio`, `dato_region`. |
| `valor_nacional`| REAL         | El valor del indicador a nivel nacional para el mismo `año` e `indicador`. Este campo es el `dato_nacional` de los archivos originales. |

**Ejemplo de datos (simplificado):**

| id_medicion | id_geografia | id_indicador | año  | valor    | valor_nacional |
| :---------- | :----------- | :----------- | :--- | :------- | :------------- |
| 1           | 3 (Antioquia)| 1 (IAG)      | 2022 | 0.033197 | 0.048614       |
| 2           | 5 (Medellín) | 2 (IAMoG)    | 2022 | 0.19305  | 0.280791       |
| 3           | 2 (Región Atlántica) | 3 (PHIS) | 2015 | 0.650    | 0.542          |
| 4           | 1 (Colombia) | 1 (IAG)      | 2022 | 0.048614 | 0.048614       |
| 5           | 1 (Colombia) | 2 (IAMoG)    | 2022 | 0.280791 | 0.280791       |
| 6           | 1 (Colombia) | 3 (PHIS)     | 2015 | 0.542    | 0.542          |

### 3.4. Racionalización de `dato_departamento` y `dato_nacional`

En el esquema propuesto, la redundancia de `dato_departamento` y `dato_nacional` se elimina de la siguiente manera:

*   **`dato_departamento` (en `Municipal.xlsx`):** Este valor representaba el dato a nivel departamental para el contexto de un municipio. En el nuevo esquema, si se necesita el valor departamental para un municipio, se puede obtener mediante una consulta que una `datos_medicion` con `geografia` (para el municipio) y luego con `geografia` nuevamente (para el departamento padre) y `datos_medicion` (para el valor del indicador a nivel departamental). Alternativamente, y para simplificar la consulta si el `dato_departamento` es un valor *específico* asociado a la fila municipal y no una agregación, se podría considerar que este `dato_departamento` es un `valor` más en la tabla `datos_medicion` asociado a la `id_geografia` del departamento. Sin embargo, la forma más limpia es que `valor` en `datos_medicion` siempre se refiera al nivel de `id_geografia`.

    Para evitar la redundancia, el `dato_departamento` que aparece en el archivo municipal para cada fila de municipio, si es el mismo valor que el `dato_departamento` del archivo departamental, se manejaría así:
    *   El valor del indicador a nivel departamental se almacenaría una única vez en la tabla `datos_medicion` asociado a la `id_geografia` del departamento correspondiente y el `id_indicador` relevante (que sería el de `Inseguridad Alimentaria Moderado o Grave`).
    *   Cuando se consulte un municipio, se puede hacer un `JOIN` para obtener el valor departamental correspondiente.

*   **`dato_nacional` (en todos los archivos):** Este valor también se almacenaría una única vez en la tabla `datos_medicion` asociado a la `id_geografia` del nivel 'Nacional' y el `id_indicador` y `año` correspondientes. La columna `valor_nacional` en `datos_medicion` es una excepción a la normalización estricta para facilitar consultas comunes, pero se podría eliminar y siempre obtener el valor nacional mediante un `JOIN` a la fila nacional correspondiente en `datos_medicion`.

    **Revisión de `valor_nacional`:** Para una normalización aún más estricta, `valor_nacional` debería eliminarse de `datos_medicion`. El valor nacional para un indicador y año específicos siempre se obtendría consultando `datos_medicion` donde `id_geografia` corresponda al nivel 'Nacional'. Esto elimina la última redundancia significativa.

    **Esquema `datos_medicion` (Revisado para máxima normalización):**

    | Columna         | Tipo de Dato | Descripción                                                                 |
    | :-------------- | :----------- | :-------------------------------------------------------------------------- |
    | `id_medicion`   | INTEGER      | Clave primaria (autoincremental).                                           |
    | `id_geografia`  | INTEGER      | Clave foránea a `geografia.id_geografia` (representa el nivel de la medición: nacional, regional, departamental o municipal). |
    | `id_indicador`  | INTEGER      | Clave foránea a `indicadores.id_indicador`.                                 |
    | `año`           | INTEGER      | Año de la medición.                                                         |
    | `valor`         | REAL         | El valor numérico del indicador para la `id_geografia` y `año` dados. |

    Con este esquema revisado, el `valor_nacional` se obtendría consultando `datos_medicion` para `id_geografia` = ID de Colombia y el `id_indicador` y `año` deseados.

## 4. Beneficios del Esquema Normalizado

*   **Reducción de Redundancia:** Los nombres de lugares, indicadores y sus atributos se almacenan una sola vez.
*   **Mejora de la Integridad de Datos:** Los cambios en un nombre de departamento, por ejemplo, solo necesitan hacerse en un lugar (`geografia` tabla).
*   **Consultas Flexibles y Eficientes:** Permite realizar consultas complejas y eficientes que combinan datos de diferentes niveles geográficos y tipos de indicadores sin ambigüedad.
*   **Escalabilidad:** El modelo puede manejar fácilmente la adición de nuevos departamentos, municipios, regiones o indicadores sin reestructurar la base de datos.

## 5. Proceso ETL Adaptado al Esquema Normalizado

El proceso ETL (Extract, Transform, Load) deberá adaptarse para poblar este nuevo esquema:

1.  **Extract:** Leer los archivos `.xlsx` originales.
2.  **Transform:**
    *   **Poblar `geografia`:** Extraer todos los nombres únicos de departamentos, municipios y regiones de los tres archivos. Asignarles un `nivel` y un `id_padre` (ej. Colombia es padre de departamentos/regiones, departamentos son padres de municipios). Esto se haría una vez.
    *   **Poblar `indicadores`:** Extraer todos los nombres únicos de indicadores, `tipo_dato` y `tipo_de_medida` de los tres archivos. Esto también se haría una vez.
    *   **Poblar `datos_medicion`:** Para cada fila de cada archivo original:
        *   Obtener el `id_geografia` correspondiente de la tabla `geografia` (o insertarlo si no existe).
        *   Obtener el `id_indicador` correspondiente de la tabla `indicadores` (o insertarlo si no existe).
        *   Insertar el `año` y el `valor` (que sería `dato_departamento`, `dato_municipio`, `dato_region` según la fuente) en `datos_medicion`.
        *   Para el `dato_nacional` de cada fila original, se insertaría como un registro separado en `datos_medicion` con el `id_geografia` correspondiente a 'Colombia' y el `id_indicador` y `año` relevantes.

Este enfoque garantiza que cada pieza de información se almacene de manera óptima, evitando la redundancia y facilitando un análisis de datos robusto y escalable.

