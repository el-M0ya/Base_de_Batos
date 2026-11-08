# Arquitectura del frontend

## Estructura de carpetas

```
frontend/src/
├── app/          # Enrutamiento, layouts y providers globales
├── features/     # Módulos por funcionalidad (auth, exercises, reports, …)
└── shared/       # Componentes, hooks, utils, tipos y API reutilizables
```

## Regla de dependencias

- `features/*` puede importar de `shared/*`.
- `features/*` **no** puede importar de otra feature.
- `app/*` puede importar de `features/*` y `shared/*`.
- `shared/*` no depende de `features/*` ni de `app/*`.

## Separación de responsabilidades

Cada feature separa:

- **Tipos de dominio** (`types.ts`) mapeados desde los esquemas de la API.
- **Capa de datos** (`*Api.ts` + `*Api.mock.ts`) detrás de una interfaz común.
- **Hooks** (`use*.ts`) que consumen la capa de datos y gestionan estado de servidor.
- **Páginas/componentes presentacionales** que solo reciben props y emiten eventos.

## Capa de API

Toda feature accede a los datos a través de una interfaz tipada con dos implementaciones
intercambiables seleccionadas al arranque según `VITE_API_MODE` (`real` o `mock`). Esto
permite la demo estática sin backend (ver ADR-003).

## Enrutamiento

Se usa un router basado en hash para que todas las rutas sobrevivan a una recarga en
hosting estático (GitHub Pages). Las entradas de navegación se declaran en un único
archivo de configuración con los roles permitidos.