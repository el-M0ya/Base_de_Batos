La **Capa de Casos de Uso (** **src/use_cases/** **)** o *Capa de Reglas de Negocio de la Aplicación* coordina el flujo de datos desde y hacia las entidades del dominio.

### Principios Fundamentales de esta Capa:

1. **Dependencia hacia adentro:** Solo importa el **Dominio (** **src/domain/** **)**. No importa FastAPI, ni SQLModel, ni controladores de base de datos.
2. **Inversión de Dependencias (DIP):** No accede a PostgreSQL directamente. En su lugar, define **interfaces/contratos abstractos** (Puertos) de lo que necesita de la base de datos.
3. **Desacoplamiento con DTOs:** No expone las entidades puras del dominio hacia el exterior; utiliza **Objetos de Transferencia de Datos (DTOs)** para recibir entradas y devolver respuestas.

A continuación vamos a construir y explicar detenidamente los tres archivos que integran esta capa para el módulo de usuarios y sedes.

---

### 1. Los Objetos de Transferencia de Datos (`src/use_cases/dtos.py`)

Los **DTOs** (*Data Transfer Objects*) son estructuras simples que definen **qué datos entran a la aplicación y qué datos salen de ella**. Utilizaremos **Pydantic V2** para garantizar una validación estricta de tipos de entrada.

### 2. Los Puertos de Repositorio (`src/use_cases/ports/repositories.py`)

Un **Puerto** en Clean Architecture es una **interfaz abstracta (ABC)**. Especifica los métodos que el caso de uso necesita que realice la base de datos, sin importar si por dentro usa PostgreSQL, MySQL o archivos JSON.

### 3. El Caso de Uso Interactor (`src/use_cases/gestionar_usuarios.py`)

Esta clase ejecuta las **reglas de la aplicación**: coordina las entidades del dominio, invoca las validaciones, solicita el hasheo de contraseñas y delega el guardado al repositorio.