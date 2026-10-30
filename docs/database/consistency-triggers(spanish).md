# Documentación de Disparadores de Coherencia (Consistency Triggers)

**Módulo:** Base de Datos e Infraestructura SQL (Épica 1)  
**Issue:** E1-08 — Implementar los disparadores de coherencia del modelo  
**Script SQL:** `backend/database/scripts/007_consistency_triggers.sql`  

---

## 1. Visión General

Este documento describe los mecanismos de integridad activa (disparadores o *triggers* y funciones PL/pgSQL) implementados directamente en PostgreSQL para garantizar la coherencia del modelo de dominio del sistema de gimnasio.

Estos disparadores actúan como una barrera de seguridad en la base de datos, impidiendo que transacciones con datos incongruentes o violaciones de reglas de negocio se consoliden en la persistencia, independientemente de la aplicación consumidora.

---

## 2. Disparadores Implementados

### 2.1 Coherencia entre Rol de Usuario y Especialización

#### Contexto
El modelo aplica herencia relacional 1:1 entre `app_user` (tabla padre con credenciales y rol de sistema) y sus especializaciones `trainer` y `client`.

#### Disparadores y Funciones:
1. **`check_trainer_user_role()` / `trg_check_trainer_user_role`**
   * **Tabla objetivo:** `trainer`
   * **Momento:** `BEFORE INSERT OR UPDATE`
   * **Regla:** Verifica que el `id_trainer` exista en `app_user` y posea el rol `'TRAINER'`.
   * **Comportamiento ante error:** Lanza una excepción (`RAISE EXCEPTION`) cancelando la transacción si el usuario no existe o tiene un rol diferente (`'CLIENT'` o `'ADMIN'`).

2. **`check_client_user_role()` / `trg_check_client_user_role`**
   * **Tabla objetivo:** `client`
   * **Momento:** `BEFORE INSERT OR UPDATE`
   * **Regla:** Verifica que el `id_client` exista en `app_user` y posea el rol `'CLIENT'`.
   * **Comportamiento ante error:** Lanza una excepción si el usuario no existe o tiene rol `'TRAINER'` o `'ADMIN'`.

---

### 2.2 Sincronización del Ciclo de Vida y Validación de Rutinas

#### Contexto
Una rutina transita por distintos estados (`DRAFT`, `PENDING_REVIEW`, `APPROVED`, `REJECTED`). El proceso de revisión por parte del Jefe de Sala o Entrenador autorizador registra una fila en la tabla `validate`.

#### Disparador y Función:
* **`sync_routine_status_on_validation()` / `trg_sync_routine_status`**
  * **Tabla objetivo:** `validate`
  * **Momento:** `BEFORE INSERT OR UPDATE`
  * **Reglas:**
    1. Comprueba que la rutina referenciada esté actualmente en estado `'PENDING_REVIEW'`. No se permite validar rutinas en borrador o ya procesadas.
    2. Actualiza automáticamente el campo `routine.status` con el resultado de `NEW.decision` (`'APPROVED'` o `'REJECTED'`).
  * **Comportamiento ante error:** Detiene la inserción si la rutina no está lista para revisión o si la decisión ingresada no es válida.

---

### 2.3 Coherencia en la Resolución de Ajustes de Rutinas

#### Contexto
Cuando un cliente o entrenador solicita un ajuste sobre una rutina en ejecución (`request`), se asigna un entrenador responsable. La resolución técnica del ajuste se registra en `adjustment_result`.

#### Disparador y Función:
* **`verify_adjustment_trainer_match()` / `trg_verify_adjustment_trainer`**
  * **Tabla objetivo:** `adjustment_result`
  * **Momento:** `BEFORE INSERT OR UPDATE`
  * **Regla:** Valida que el `id_trainer` que firma el resultado en `adjustment_result` coincida exactamente con el `id_trainer` asignado a la solicitud en `request`.
  * **Comportamiento ante error:** Cancela la operación si el entrenador que intenta resolver el ajuste no es el designado en la solicitud.

---

## 3. Matriz de Verificación y Casos de Prueba

| Caso de Prueba | Entrada / Operación | Resultado Esperado |
| :--- | :--- | :--- |
| **TP-01: Inserción de Entrenador Válida** | Insertar en `trainer` un `id_user` cuyo `role = 'TRAINER'`. | Transacción exitosa. |
| **TP-02: Inserción de Entrenador Inválida** | Insertar en `trainer` un `id_user` cuyo `role = 'CLIENT'`. | **Error de Trigger:** Exception *"must be TRAINER to be added to trainer table"*. |
| **TP-03: Inserción de Cliente Válida** | Insertar en `client` un `id_user` cuyo `role = 'CLIENT'`. | Transacción exitosa. |
| **TP-04: Validación de Rutina Válida** | Insertar en `validate` con decisión `'APPROVED'` sobre rutina en `'PENDING_REVIEW'`. | Transacción exitosa. Estado de la rutina actualizado automáticamente a `'APPROVED'`. |
| **TP-05: Validación sobre Estado Inválido** | Intentar validar una rutina en estado `'DRAFT'`. | **Error de Trigger:** Exception *"only routines in PENDING_REVIEW can be validated"*. |
| **TP-06: Ajuste con Entrenador Correcto** | Registrar `adjustment_result` con el mismo `id_trainer` de la `request`. | Transacción exitosa. |
| **TP-07: Ajuste con Entrenador Invalido** | Registrar `adjustment_result` con un `id_trainer` distinto al asignado en `request`. | **Error de Trigger:** Exception *"resolving the adjustment does not match Trainer ID assigned to request"*. |

---

## 4. Mantenimiento e Idempotencia

* Todas las funciones utilizan la cláusula `CREATE OR REPLACE FUNCTION`.
* Los disparadores se eliminan preventivamente antes de recrearse mediante `DROP TRIGGER IF EXISTS`, asegurando que el script pueda ser ejecutado múltiples veces sin causar duplicación de triggers ni fallos de ejecución.
* El script está envuelto en un bloque transaccional explícito (`BEGIN; ... COMMIT;`).
