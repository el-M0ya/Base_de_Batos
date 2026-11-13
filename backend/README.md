# Backend

## Instalación

Desde `backend/`, crea un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Base de datos

Configura las variables `POSTGRES_*` en el `.env` de la raíz y levanta
PostgreSQL:

```powershell
docker compose up -d --wait
```

Los scripts de `backend/database/scripts/` se ejecutan automáticamente cuando
el volumen de PostgreSQL se crea por primera vez. Para reinicializar la base de
datos desde cero, elimina el volumen de desarrollo y vuelve a ejecutar Compose.

## Arranque

```powershell
python -m uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`, con documentación en
`/docs`.

## Tests

Desde la raíz del repositorio:

```powershell
$env:PYTHONPATH = "backend"
python -m unittest discover -s backend/tests -t backend/tests
```

Los tests de integración requieren PostgreSQL disponible y se omiten cuando la
infraestructura no está levantada.
