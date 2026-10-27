# ADR-003 — Arquitectura del frontend

- **Estado:** Aceptado
- **Fecha:** 2026-10-27

## Contexto

El frontend del MVP debe funcionar con y sin backend, publicarse como demo estática en
GitHub Pages y mantenerse desacoplado del backend (RNF-05).

## Decisión

1. **Estructura por feature** con áreas `app`, `features` y `shared`. Regla de
   dependencias: las features solo pueden usar `shared`.
2. **Enrutamiento:** React Router con `HashRouter`.
3. **Estado de servidor:** TanStack Query para caché, carga y manejo de errores.
4. **Gráficos:** Recharts.
5. **Exportación PDF:** jsPDF (con jspdf-autotable para tablas).
6. **Capa de API:** cada feature expone una interfaz tipada con implementación real
   y mock, seleccionadas al arranque por `VITE_API_MODE`. El modo mock sirve datos
   en memoria sin backend.
7. **Estilos:** tokens CSS compartidos (`shared/styles/tokens.css`) derivados del
   diseño de Google Stitch.
8. **Textos de usuario:** módulo único `shared/i18n/messages.ts` en español.

## Consecuencias

- La demo estática usa únicamente datos simulados y muestra un banner visible.
- Toda nueva funcionalidad debe seguir la regla de dependencias y la separación
  presentacional/datos/tipos.
- Las librerías elegidas se instalan en los issues correspondientes (E3-05, E3-07,
  E3-09).