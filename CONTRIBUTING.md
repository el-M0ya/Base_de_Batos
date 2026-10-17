# Guía de contribución

Esta guía define un flujo sencillo para trabajar en equipo. Si una convención aún no está automatizada por GitHub, debe seguirse manualmente.

## 1. Antes de empezar

1. Busca una Issue existente o crea una con la plantilla adecuada: **Funcionalidad**, **Error o defecto** o **Tarea técnica**.
2. Comprueba que el objetivo, los criterios de aceptación y los requisitos relacionados estén claros.
3. Evita duplicar trabajo. Si el alcance cambia de forma importante, actualiza la Issue antes de continuar.

## 2. Convención de ramas

Crea una rama por Issue y evita trabajar directamente sobre `main`. Usa nombres cortos y descriptivos:

- `feature/<numero>-<resumen>`: nueva funcionalidad.
- `fix/<numero>-<resumen>`: corrección de un defecto.
- `task/<numero>-<resumen>`: tarea técnica o documentación.
- `chore/<numero>-<resumen>`: configuración y mantenimiento del repositorio.

Ejemplos: `feature/24-plan-entrenamiento`, `fix/31-validacion-formulario`, `task/18-documentar-api`.

Usa minúsculas, guiones y el número de Issue cuando exista.

## 3. Convención de commits

Usa mensajes breves, en español o inglés, que indiquen la intención del cambio con un prefijo:

- `feat: agregar generación de planes`
- `fix: corregir validación de ejercicios`
- `docs: actualizar instrucciones de instalación`
- `test: cubrir cálculo de duración`
- `refactor: simplificar servicio de planificación`
- `chore: configurar plantillas de GitHub`

Añade el número de Issue cuando aporte claridad, por ejemplo: `docs: documentar instalación (#24)`. Cada commit debe representar un cambio coherente; evita mensajes vagos como `cambios`, `arreglos` o `final`.

## 4. Pull Requests y revisión

1. Abre un Pull Request desde tu rama hacia `main`.
2. Completa la plantilla: objetivo, Issue relacionada, cambios, pruebas y pasos de verificación.
3. Enlaza la Issue con `Closes #N` cuando el PR la complete; usa `Relates to #N` si solo está relacionado.
4. Solicita revisión a la persona responsable del área. Consulta `.github/CODEOWNERS` para identificar propietarios.
5. Para repartir revisiones manualmente, alterna el revisor principal:
   - **Frontend:** Bryan (@el-M0ya) y Fabio (@Fabio-Pilot), alternando en cada PR.
   - **Backend:** Cuervo (@AlexCuervo), Héctor (@HectorDuarte911) y Gabriel (@GaboPS1016), siguiendo ese orden.
   - **Base de datos:** Gabriel (@GaboPS1016).
   - **QA y documentación:** Alejandro (@Kaik0405).
6. Atiende los comentarios, realiza los cambios necesarios y espera las aprobaciones exigidas por las reglas del repositorio antes de integrar el PR.

CODEOWNERS puede ayudar a solicitar revisiones, pero no alterna revisores automáticamente. La exigencia de aprobaciones depende de la configuración de protección de `main`.

## 5. Pruebas y calidad

- Ejecuta las pruebas relevantes para el cambio y anota sus resultados en el PR.
- Si no puedes ejecutar una prueba, indícalo y explica la razón; no afirmes que pasó.
- Verifica manualmente los cambios de interfaz o flujos cuando corresponda.
- Actualiza documentación y ejemplos afectados.
- No subas contraseñas, tokens, claves privadas, datos personales sensibles ni archivos locales de configuración con secretos.

## 6. Criterios de finalización

Una tarea está lista para revisión cuando cumple sus criterios de aceptación, tiene pruebas o una explicación de las pruebas pendientes, y la documentación necesaria está actualizada. Se considera terminada cuando los cambios han sido revisados e integrados y la Issue queda actualizada o cerrada según corresponda.

## 7. Mantener la guía útil

Si el equipo acuerda cambiar nombres de ramas, convenciones de commits o el flujo de revisión, actualiza este documento y comunica el cambio. Mantén las reglas simples y aplicables al tamaño del equipo.
