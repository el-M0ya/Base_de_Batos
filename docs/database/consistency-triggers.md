# Consistency Trigger Documentation

**Module:** Database and SQL Infrastructure (Epic 1)  
**Issue:** E1-08 — Implement the model consistency triggers  
**SQL Script:** `backend/database/scripts/007_consistency_triggers.sql`  

---

## 1. Overview

This document describes the active integrity mechanisms (triggers and PL/pgSQL functions) implemented directly in PostgreSQL to guarantee consistency within the gym system's domain model.

These triggers act as a safety barrier in the database, preventing transactions containing inconsistent data or violations of business rules from being committed to persistent storage, regardless of the consuming application.

---

## 2. Implemented Triggers

### 2.1 Consistency Between User Role and Specialization

#### Context

The model applies 1:1 relational inheritance between `app_user` (the parent table containing credentials and system role) and its `trainer` and `client` specializations.

#### Triggers and Functions

1. **`check_trainer_user_role()` / `trg_check_trainer_user_role`**
   * **Target table:** `trainer`
   * **Timing:** `BEFORE INSERT OR UPDATE`
   * **Rule:** Verifies that `id_trainer` exists in `app_user` and has the `'TRAINER'` role.
   * **Error behavior:** Raises an exception (`RAISE EXCEPTION`) and cancels the transaction if the user does not exist or has a different role (`'CLIENT'` or `'ADMIN'`).

2. **`check_client_user_role()` / `trg_check_client_user_role`**
   * **Target table:** `client`
   * **Timing:** `BEFORE INSERT OR UPDATE`
   * **Rule:** Verifies that `id_client` exists in `app_user` and has the `'CLIENT'` role.
   * **Error behavior:** Raises an exception if the user does not exist or has the `'TRAINER'` or `'ADMIN'` role.

---

### 2.2 Lifecycle Synchronization and Routine Validation

#### Context

A routine transitions through different states (`DRAFT`, `PENDING_REVIEW`, `APPROVED`, `REJECTED`). The review process performed by the Head of Room or an authorized trainer records a row in the `validate` table.

#### Trigger and Function

* **`sync_routine_status_on_validation()` / `trg_sync_routine_status`**
  * **Target table:** `validate`
  * **Timing:** `BEFORE INSERT OR UPDATE`
  * **Rules:**
    1. Verifies that the referenced routine is currently in the `'PENDING_REVIEW'` state. Routines in draft or already processed cannot be validated.
    2. Automatically updates the `routine.status` field with the result from `NEW.decision` (`'APPROVED'` or `'REJECTED'`).
  * **Error behavior:** Stops the insertion if the routine is not ready for review or if the entered decision is invalid.

---

### 2.3 Consistency When Resolving Routine Adjustments

#### Context

When a client or trainer requests an adjustment to a routine in progress (`request`), a responsible trainer is assigned. The technical resolution of the adjustment is recorded in `adjustment_result`.

#### Trigger and Function

* **`verify_adjustment_trainer_match()` / `trg_verify_adjustment_trainer`**
  * **Target table:** `adjustment_result`
  * **Timing:** `BEFORE INSERT OR UPDATE`
  * **Rule:** Validates that the `id_trainer` signing the result in `adjustment_result` exactly matches the `id_trainer` assigned to the request in `request`.
  * **Error behavior:** Cancels the operation if the trainer attempting to resolve the adjustment is not the trainer assigned to the request.

---

## 3. Verification Matrix and Test Cases

| Test Case | Input / Operation | Expected Result |
| :--- | :--- | :--- |
| **TP-01: Valid Trainer Insertion** | Insert into `trainer` an `id_user` whose `role = 'TRAINER'`. | Transaction succeeds. |
| **TP-02: Invalid Trainer Insertion** | Insert into `trainer` an `id_user` whose `role = 'CLIENT'`. | **Trigger Error:** Exception *"must be TRAINER to be added to trainer table"*. |
| **TP-03: Valid Client Insertion** | Insert into `client` an `id_user` whose `role = 'CLIENT'`. | Transaction succeeds. |
| **TP-04: Valid Routine Validation** | Insert into `validate` with decision `'APPROVED'` for a routine in `'PENDING_REVIEW'`. | Transaction succeeds. The routine's status is automatically updated to `'APPROVED'`. |
| **TP-05: Validation with Invalid Status** | Attempt to validate a routine in the `'DRAFT'` state. | **Trigger Error:** Exception *"only routines in PENDING_REVIEW can be validated"*. |
| **TP-06: Adjustment with Correct Trainer** | Create an `adjustment_result` with the same `id_trainer` as the `request`. | Transaction succeeds. |
| **TP-07: Adjustment with Invalid Trainer** | Create an `adjustment_result` with an `id_trainer` different from the one assigned to the `request`. | **Trigger Error:** Exception *"resolving the adjustment does not match Trainer ID assigned to request"*. |

---

## 4. Maintenance and Idempotency

* All functions use the `CREATE OR REPLACE FUNCTION` clause.
* Triggers are proactively removed before being recreated using `DROP TRIGGER IF EXISTS`, ensuring that the script can be executed multiple times without creating duplicate triggers or causing execution failures.
* The script is wrapped in an explicit transaction block (`BEGIN; ... COMMIT;`).
