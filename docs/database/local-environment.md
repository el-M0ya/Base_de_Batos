# Entorno local de PostgreSQL

> Referencia: issue **#19** — *E1-01 Configure PostgreSQL for the Development
> Environment*.
>
> Este documento explica cómo levantar la base de datos del proyecto en un
> equipo de desarrollo, qué variables la configuran, cómo se conservan los
> datos y qué hacer cuando algo falla.
>
> Fuente del diseño: informe de diseño de base de datos del proyecto
> (*4_Base de Batos*, sección 3 «Diseño de la base de datos»).

---

## 1. Qué define esta configuración

| Aspecto | Decisión |
|---|---|
| Motor relacional | PostgreSQL 17 (`postgres:17-alpine`) |
| Versión | Fijada de forma explícita en la etiqueta de la imagen: es la que ya usaba la configuración del repositorio y la que declara el README. Queda pendiente de confirmación formal por el equipo (issue #19) |
| Almacenes | Dos, con roles distintos: núcleo relacional (PostgreSQL) y caché de la rutina activa (Redis). La estructura variable de bloques se almacena en PostgreSQL con JSONB, tal como indica la issue #23 |
| Fuente de verdad | Únicamente el núcleo relacional: las 21 relaciones del esquema + `routine_structure` con JSONB |
| Orquestación | Docker Compose, fichero `compose.yaml` de la raíz |
| Configuración | Variables de entorno desde `.env` (plantilla en `.env.example`) |
| Persistencia | Volúmenes con nombre: `postgres-data`, `redis-data` |
| Creación de tablas | Scripts SQL numerados en `backend/database/scripts/` |
| Credenciales | Sólo valores de desarrollo, públicos; ninguna credencial real en el repositorio |

---

## 2. Arquitectura de almacenamiento

Los datos se reparten en dos almacenes, con roles distintos:

| Almacén | Qué guarda | Papel |
|---|---|---|
| **PostgreSQL** | Las 21 relaciones del esquema relacional (`USER` … `ADJUSTMENTRESULT`) más `routine_structure` con columna **JSONB** para la jerarquía anidada de bloques | **Fuente de verdad.** Es el único lugar donde se validan las 3FN, la PLJ y la PPDF. La rutina y su estructura se guardan en **una sola transacción** (issue #23). |
| **Redis** | La rutina activa que el cliente está ejecutando, con clave `ref_estructura` y TTL corto | Caché de lectura. **No es fuente de verdad**: el estado de la rutina y de su asignación se sigue leyendo del núcleo relacional. Su actualización se controla desde el esquema relacional (RI-29). |

Notas del modelo (MERX actualizado):

- **Intensidad**: el nivel/intensidad pasa a ser un **atributo de la rutina** (no solo de otros elementos), y debe reflejarse en el esquema de `routine` según lo acordado en el nuevo MERX.
- **Room Chief (Jefe de Sala)**: es un **tipo específico de entrenador**. Su función es **validar rutinas y orientar la creación de otras**, **pero no crea rutinas directamente**. Esto debe respetarse en las reglas de negocio, en los disparadores (`007_`) y en las autorizaciones (`AUTHORISES`).

Consecuencias prácticas para el entorno:

- No se necesita un almacén documental externo: todo queda en PostgreSQL.
- Redis se levanta siempre: es el mecanismo que da respuesta inmediata al
  requerimiento no funcional RNF-03.
- La invalidación de la caché se produce desde el disparador que actualiza el
  estado de la rutina, es decir, desde PostgreSQL (script `007_`).

### 2.1. Las 21 relaciones del núcleo relacional

| # | Relación (informe) | Tabla (issues) | Script | Issue |
|---|---|---|---|---|
| R1 | `USER` (superentidad, con el atributo `rol`) | `user` | `001_` | #20 |
| R2 | `TRAINER` | `trainer` | `001_` | #20 |
| R3 | `ROOMCHIEF` | `room_chief` | `001_` | #20 |
| R4 | `SITE` (catálogo) | `site` | `001_` | #20 |
| R5 | `CLIENT` | `client` | `001_` | #20 |
| R6 | `WORKOUTPROGRAM` | `workout_program` | `002_` | #21 |
| R7 | `COVERS` | `covers` | `002_` | #21 |
| R8 | `MUSCLEGROUP` (catálogo) | `muscle_group` | `002_` | #21 |
| R9 | `EXERCISETYPE` (catálogo) | `exercise_type` | `002_` | #21 |
| R10 | `INTENSITYLEVEL` (catálogo) | `intensity_level` | `002_` | #21 |
| R11 | `EXERCISE` | `exercise` | `003_` | #22 |
| R12 | `AUTHORISES` | `authorises` | `003_` | #22 |
| R13 | `INSCRIBED` | `inscribed` | `003_` | #22 |
| R14 | `ROUTINE` (conserva `ref_estructura`, con **intensidad como atributo de la rutina**) | `routine` | `004_` | #23 |
| R15 | `PARAMETERSROUTINE` (entidad débil) | `parameters_routine` | `004_` | #23 |
| R16 | `CONTAINS` | `contains` | `004_` | #23 |
| R17 | `VALIDATE` | `validate` | `005_` | #24 |
| R18 | `ASSIGNMENT` | `assignment` | `005_` | #24 |
| R19 | `SESION` | `session` | `005_` | #24 |
| R20 | `REQUEST` | `request` | `005_` | #24 |
| R21 | `ADJUSTMENTRESULT` | `adjustment_result` | `005_` | #24 |

Notas de diseño que conviene tener presentes:

- El **rol es un atributo de `USER`**, no una tabla aparte: la generalización
  `USER` → `TRAINER` / `ROOMCHIEF` / `CLIENT` se resuelve con claves primarias
  idénticas, sin duplicar atributos.
- **Room Chief**: es un tipo específico de **TRAINER**. Su función es **validar rutinas y orientar la creación de otras**, pero **no crea rutinas directamente**. Debe aplicarse esta restricción en reglas de negocio y disparadores.
- `SESSION` **no** guarda el cliente: se llega a él por
  `SESION → ASSIGNMENT → id_client`. Guardarlo allí introduciría la
  dependencia transitiva `id_sesion → id_assignment → id_client` y rompería la
  tercera forma normal.
- `ASSIGNMENT` conserva su propio identificador aunque la combinación de
  rutina y cliente sea única: es lo que permite registrar sesiones contra una
  asignación concreta.
- El esquema declara **31 claves foráneas**; los scripts de creación deben
  respectarlas para que la integridad referencial se cumpla desde el inicio.

---

## 3. Requisitos

- Docker Engine 24 o superior.
- Docker Compose v2 (incluido en Docker Desktop). Verificar con:

  ```bash
  docker --version
  docker compose version
  ```

En Windows y macOS, Docker Desktop incluye ambos. En Linux, instale
`docker-compose-plugin` del repositorio oficial.

---

## 4. Preparación del fichero `.env`

```bash
cp .env.example .env
```

`.env` queda en el `.gitignore`: es configuración local y **nunca** se sube al
repositorio. `.env.example` sí se versiona y contiene únicamente valores de
desarrollo, que son públicos por diseño para que cualquier integrator pueda
levantar la pila sin pedir credenciales.

Variables que consume `compose.yaml`:

| Variable | Valor por defecto | Para qué sirve |
|---|---|---|
| `POSTGRES_DB` | `basedebatos` | Nombre de la base de datos inicial |
| `POSTGRES_USER` | `basedebatos` | Usuario propietario de la base de datos |
| `POSTGRES_PASSWORD` | `basedebatos` | Contraseña del usuario anterior |
| `POSTGRES_PORT` | `5432` | Puerto del host para acceder al servidor |
| `REDIS_PORT` | `6379` | Puerto del host para la caché de la rutina activa |
| `FRONTEND_PORT` | `8080` | Puerto del host para el frontend compilado |

> **Importante:** `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` sólo
> se aplican en el **primer arranque**. Si el volumen `postgres-data` ya
> existe, el contenedor los ignora y conserva los valores con los que se
> creó la base de datos. Ver §9.

---

## 5. Puesta en marcha

```bash
# Levanta PostgreSQL y Redis (el núcleo: es lo habitual durante el desarrollo)
docker compose up -d --wait

# Sigue la salida de PostgreSQL
docker compose logs -f postgres
```

La pila queda disponible en:

| Servicio | URL / puerto | Perfil |
|---|---|---|
| PostgreSQL | `localhost:5432` | siempre |
| Redis | `localhost:6379` | siempre |
| Frontend compilado | `localhost:8080` | `full` |

El arranque no termina hasta que el *healthcheck* responde
(`pg_isready` con el usuario y la base de datos reales). Para esperar
explícitamente:

```bash
docker compose up -d --wait
```

### Detener y volver a levantar

```bash
docker compose stop        # Detiene los contenedores, conserva los volúmenes
docker compose start       # Vuelve a levantarlos sin recrearlos
docker compose restart     # Reinicia sólo PostgreSQL
docker compose down        # Elimina los contenedores, CONSERVA los volúmenes
docker compose down -v     # Elimina los contenedores Y los volúmenes (borra los datos)
```

`docker compose down` **no** borra los datos: el volumen `postgres-data` es
independiente del ciclo de vida de los contenedores. Sólo `down -v` los
destruye.

---

## 6. Conexión y verificación

Desde el host, con el cliente `psql` instalado:

```bash
psql -h localhost -p 5432 -U basedebatos -d basedebatos
```

Sin cliente instalado, se puede entrar en el contenedor:

```bash
docker compose exec postgres psql -U basedebatos -d basedebatos
```

Comprobaciones mínimas:

```sql
-- Versión del motor (debe ser 17)
SELECT version();

-- Base de datos y tablas existentes
\dt

-- Las 21 relaciones del núcleo relacional deben estar presentes
SELECT count(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

La columna `STATUS` de `docker compose ps` debe mostrar `healthy` para
`basedebatos-postgres`.

---

## 7. Estructura de bloques de la rutina: JSONB en PostgreSQL

Según la **issue #23** y la actualización del **MERX**:

- La estructura variable de bloques de cada rutina se almacena en PostgreSQL como **JSONB**.
- Se crea la tabla **`routine_structure`** con relación **uno a uno** con `routine`.
- **Rutina y estructura se guardan en una sola transacción** de PostgreSQL.
- **No se usa almacén externo**: todo queda en el núcleo relacional.
- El atributo `ref_estructura` de `ROUTINE` sigue existiendo según corresponda al diseño.

No hay almacenamiento documental externo necesario para este punto. Redis sigue siendo la caché de la rutina activa (no autoritativa), con TTL corto y su actualización/invalidez controlada desde el esquema relacional.

---

## 8. Scripts de inicialización del esquema

El esquema **no** se crea desde la aplicación: se crea con scripts SQL
numerados, que son la fuente de verdad del modelo de datos.

```
backend/database/scripts/
├── 001_identity_and_sites.sql              # user, trainer, room_chief, site, client
├── 002_catalogs_and_programs.sql           # workout_program, muscle_group, exercise_type,
│                                           # intensity_level, covers
├── 003_exercises_authorisations_enrolments.sql  # exercise, authorises, inscribed
├── 004_routines_and_structure.sql          # routine, parameters_routine, contains,
│                                           # routine_structure (JSONB, ver §7)
├── 005_validation_assignments_sessions_adjustments.sql  # validate, assignment, session,
│                                           # request, adjustment_result
├── 006_integrity_constraints.sql           # U-1..U-12, CHECK y restricciones temporales
├── 007_consistency_triggers.sql            # disparadores de consistencia e invalidación
│                                           # de la caché de la rutina activa
└── 008_catalog_seeds.sql                    # datos iniciales de los catálogos
```

El directorio está montado en `/docker-entrypoint-initdb.d` del contenedor, de
modo que **la imagen oficial de PostgreSQL ejecuta los scripts en orden
alfabético, que coincide con el orden numérico, y se detiene en el primer
error** (`ON_ERROR_STOP`).

Consecuencias prácticas:

- Sólo se ejecutan **una vez**, cuando el volumen está vacío.
- Un script que falla detiene la inicialización: hay que mirar el log
  (`docker compose logs postgres`) y volver a intentarlo con el volumen
  limpio (§9).
- Añadir un script nuevo a la carpeta **no** cambia una base de datos ya
  creada. Para aplicar cambios sobre una base existente se ejecutan los
  scripts a mano con `psql`; el procedimiento está en
  `backend/database/scripts/README.md` (issue #28).

---

## 9. Recrear la base de datos desde cero

Durante el desarrollo es normal querer empezar de cero, por ejemplo tras
cambiar un script de inicialización:

```bash
docker compose down -v          # elimina contenedores y volúmenes
docker compose up -d --wait     # vuelve a levantar; se ejecutan los scripts
```

Para borrar **sólo** la base de datos y conservar el resto:

```bash
docker compose exec postgres psql -U basedebatos -d postgres \
  -c "DROP DATABASE IF EXISTS basedebatos WITH (FORCE);" \
  -c "CREATE DATABASE basedebatos OWNER basedebatos;"
```

### Cambiar la contraseña del usuario

La contraseña se fija al crear el volumen. Para cambiarla:

```bash
docker compose exec postgres psql -U basedebatos -d basedebatos \
  -c "ALTER USER basedebatos WITH PASSWORD 'nueva-clave';"
```

y se actualiza `POSTGRES_PASSWORD` en el `.env` local para que coincida con lo
que usan las aplicaciones.

---

## 10. Copias de seguridad

```bash
# Volcado de la base de datos
docker compose exec postgres pg_dump -U basedebatos -d basedebatos \
  > respaldos/basedebatos-$(date +%Y%m%d).sql

# Restauración
docker compose exec -T postgres psql -U basedebatos -d basedebatos \
  < respaldos/basedebatos-20261021.sql
```

Los volcados son datos del proyecto, no código: se guardan fuera del
repositorio (la carpeta `respaldos/` está cubierta por las reglas de
`.gitignore` para artefactos de base de datos) o en el almacenamiento que el
equipo acuerde. La estructura de bloques queda incluida en el volcado de
PostgreSQL (JSONB).

---

## 11. Resolución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `port is already allocated` | Ya hay un PostgreSQL en el puerto 5432 | Cambiar `POSTGRES_PORT` en `.env` o detener el servicio que lo ocupa |
| El contenedor reinicia en bucle | Volumen con datos de otra versión de la imagen | `docker compose down -v && docker compose up -d --wait` |
| `password authentication failed` | La contraseña del `.env` no coincide con la guardada en el volumen | Usar la original, o la de §9 |
| `database "basedebatos" does not exist` | El volumen ya existía con otro `POSTGRES_DB` | Recrear el volumen (§9) |
| `relation "..." does not exist` tras crear un script nuevo | Los scripts sólo corren con el volumen vacío | Aplicar el script a mano con `psql` (§8) |
| Los scripts no se ejecutan | El directorio montado está vacío o el volumen ya existe | Revisar `docker compose logs postgres` y §9 |
| La caché devuelve datos viejos | Entrada de Redis sin TTL o sin invalidar | Revisar el TTL de la aplicación y el disparador de `routine` (§2) |

Diagnóstico general:

```bash
docker compose ps                # estado y salud de los contenedores
docker compose logs postgres     # log del servidor de base de datos
docker compose config            # configuración resuelta, con los valores aplicados
```

`docker compose config` es la forma más rápida de confirmar qué valores ha
resuelto Compose a partir de `.env`.

---

## 12. Política de credenciales

- `.env` está en `.gitignore`. No se sube, no se pega en tickets ni en el chat.
- `.env.example` se versiona y **sólo** contiene valores de desarrollo
  públicos.
- Las contraseñas de producción viajan como secretos del entorno de
  despliegue, nunca en ficheros del repositorio.
- Los datos de prueba de la base (`fixtures`) van en
  `backend/database/scripts/`, y no contienen información personal real.

---

## 13. Relación con el resto del proyecto

| Issue | Tarea | Fichero | Relación con este documento |
|---|---|---|---|
| #19 | E1-01 Configurar PostgreSQL para el entorno de desarrollo | `compose.yaml`, `.env.example`, este documento | Este documento |
| #20 | E1-02 Tablas de usuario, rol y sede | `001_identity_and_sites.sql` | §2.1, §8 |
| #21 | E1-03 Tablas de programa y catálogos | `002_catalogs_and_programs.sql` | §2.1, §8 |
| #22 | E1-04 Tablas de ejercicios, autorizaciones e inscripciones | `003_exercises_authorisations_enrolments.sql` | §2.1, §8 |
| #23 | E1-05 Tablas de rutina, parámetros, composición y estructura (JSONB en PostgreSQL) | `004_routines_and_structure.sql` | §2, §7 |
| #24 | E1-06 Tablas de validación, asignación, sesión y ajustes | `005_validation_assignments_sessions_adjustments.sql` | §2.1, §8 |
| #25 | E1-07 Restricciones de integridad y unicidad | `006_integrity_constraints.sql`, `docs/database/integrity-constraints.md` | §8 |
| #26 | E1-08 Disparadores de consistencia del modelo | `007_consistency_triggers.sql`, `docs/database/consistency-triggers.md` | §2, §8 (invalidación de la caché) |
| #27 | E1-09 Datos iniciales de catálogos | `008_catalog_seeds.sql` | §8 |
| #28 | E1-10 Script de inicialización desde cero | `backend/scripts/setup_dev_db.sh`, `backend/database/scripts/README.md` | §8, §9 |
| #35 | E2-06 Conexión directa de Python a PostgreSQL | — | Reutiliza `POSTGRES_*` para construir `DATABASE_URL` |

El diseño físico completo y su correspondencia con el MERX se documenta en
el informe de diseño del proyecto; este documento cubre únicamente el entorno
de trabajo.
