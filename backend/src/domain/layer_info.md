La **Capa de Dominio (** **src/domain/** **)** es el **núcleo absoluto** de Clean Architecture.

Su regla de oro es la **independencia total**: este código no sabe (ni le importa) si el backend usa FastAPI, Flask, PostgreSQL, MongoDB o si corre desde una consola de comandos. Solo utiliza **Python nativo puro** (biblioteca estándar) para definir qué es nuestro negocio y qué reglas son inviolables.

### 1\. El Archivo de Excepciones del Dominio (`src/domain/exceptions.py`)

En Clean Architecture, el dominio no debe lanzar errores HTTP (como `HTTPException(400)` de FastAPI), porque los conceptos de "HTTP" o "Páginas Web" no existen dentro del dominio. En su lugar, el dominio define sus **propias excepciones de negocio**.


### 2\. El Archivo de Entidades (`src/domain/entities.py`)

Aquí se definen las estructuras de datos y objetos centrales del gimnasio usando **@dataclass** de Python.