/// <reference types="vite/client" />

/** Variables de entorno públicas del frontend (ver `.env.example`). */
interface ImportMetaEnv {
  /** URL base de la API de FastAPI, sin barra final. */
  readonly VITE_API_BASE_URL?: string;
  /** `real` para usar el backend, `mock` para los datos simulados del navegador. */
  readonly VITE_API_MODE?: 'real' | 'mock';
  /** Ruta base desde la que se sirve la aplicación. */
  readonly VITE_BASE_PATH?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
