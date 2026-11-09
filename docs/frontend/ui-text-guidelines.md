# UI Text Guidelines

How to write every piece of text a user can see or hear in the frontend: labels, buttons, titles, messages, placeholders and screen-reader text.

**Goal:** the application reads as if one person wrote it, with correct Spanish spelling, and is ready to support more languages later.

## 1. Language split

| What                                                           | Language    |
| -------------------------------------------------------------- | ----------- |
| Text shown to users (UI)                                       | **Spanish** |
| Code, identifiers, file names, comments, commit messages, docs | **English** |

`messages.ts` keys are code, so they are in English; their values are UI text, so they are in Spanish:

```ts
login: {
  submit: 'Entrar',              // key in English, value in Spanish
  forgotPassword: '¿Has olvidado tu contraseña?',
},
```

## 2. Where text lives: `messages.ts` only

All UI text lives in [`frontend/src/shared/i18n/messages.ts`](../../frontend/src/shared/i18n/messages.ts). Components import it; they never contain literal UI text.

```tsx
// ✅ Do
<Button>{messages.login.submit}</Button>

// ❌ Don't
<Button>Entrar</Button>
```

This applies to **invisible** text too: `aria-label`, `title`, `alt`, and anything a screen reader announces.

Why:

- Spelling and tone can be reviewed in one file.
- The same sentence is never written twice in two slightly different ways.
- Translating the app later means translating one file (see section 8).

Organisation:

- Group keys by screen or component: `login`, `alert`, `modal`, `states`…
- Name keys after their purpose, not their text: `emailRequired`, not `introduceTuCorreo`.
- Keep the object `as const`, so TypeScript catches misspelled keys.

**Exception:** test files may use literal Spanish strings in queries such as `getByRole('button', { name: 'Entrar' })`. A test that reads the text the user sees also checks that the text is right.

## 3. Spelling and typography

- **Accents and `ñ` are mandatory:** _sesión, contraseña, aún, está, válido, número_.
  - Common traps: **aún** ("still": _¿Aún no tienes cuenta?_) vs **aun** ("even"); **sólo/solo** → always write _solo_.
- **Opening marks are mandatory:** _¿…?_ and _¡…!_
- **Ellipsis:** use the single character `…`, not three dots: _Cargando…_
- **Quotes:** use Spanish angle quotes for names inside a sentence: _¿Eliminar «Press de banca»?_
- **Capitalisation:** use sentence case. Only the first word and proper nouns are capitalised.
  - ✅ _Crear cuenta_, _Banco de ejercicios_
  - ❌ _Crear Cuenta_, _BANCO DE EJERCICIOS_. If uppercase is wanted visually, do it in CSS (`text-transform`), never in the text.
- **Final period:** full sentences (descriptions, error messages) end with a period. Labels, buttons and titles do not.

## 4. Tone

- **Address the user as _tú_**, never _usted_, as the FORJA mockups do: _Introduce **tu** correo_, _Verifica **tus** credenciales_.
- Be short, clear and friendly. Avoid jargon such as _registro_, _entidad_, _request_ or _payload_.
- Never blame the user. Prefer _El correo no tiene un formato válido_ over _Has escrito mal el correo_.

## 5. Text by element

| Element                    | Rule                                                                              | Examples                                                                      |
| -------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Buttons**                | A verb in the **infinitive** + object when needed. Says exactly what will happen. | _Entrar_, _Crear cuenta_, _Registrar ejercicio_, _Reintentar_                 |
| **Destructive buttons**    | Name the action itself, never a generic _Aceptar_ / _Sí_.                         | _Eliminar_, not _Aceptar_                                                     |
| **Screen and card titles** | Short noun phrase, or an imperative for a single-task screen.                     | _Banco de ejercicios_, _Inicia sesión_                                        |
| **Field labels**           | Noun, no colon, always visible.                                                   | _Correo electrónico_, _Sede de entrenamiento_                                 |
| **Placeholders**           | An **example**, never the only instruction (they disappear when typing).          | _tu.correo@gmail.com_                                                         |
| **Hints**                  | Short requirement, shown before the user fails it.                                | _Mínimo 8 caracteres_                                                         |
| **Empty states**           | Title says what is missing; description says what to do.                          | _Aún no hay ejercicios_ / _Registra el primero para empezar a crear rutinas._ |
| **Loading**                | _Cargando…_, or more specific: _Cargando ejercicios…_                             |                                                                               |

## 6. Error messages

An error message answers two questions: **what happened** and **what the user can do**.

| ❌ Don't                                   | ✅ Do                                                                          |
| ------------------------------------------ | ------------------------------------------------------------------------------ |
| _Error 401_                                | _Correo o contraseña incorrectos. Verifica tus credenciales._                  |
| _Network error_                            | _No se pudieron cargar los datos. Comprueba tu conexión e inténtalo de nuevo._ |
| _Duplicate key violates unique constraint_ | _Ya existe un ejercicio con ese nombre en este grupo muscular._                |
| _Campo inválido_                           | _Introduce tu correo electrónico._                                             |

Rules:

- **Never show technical details** (status codes, exception names, SQL, stack traces). They go to the browser console for developers.
- **Field errors** go under their field, through the `error` prop of `TextField` / `SelectField`.
- **Errors of a whole action** (login rejected, save failed) go in an `Alert` above the form.
- **A screen that could not load** shows `ErrorState` with a retry button.
- Map the backend's stable error codes to messages in **one place** per feature, never inside views.

## 7. Accessibility text

- Icon-only buttons need an `aria-label` from `messages.ts`: _Cerrar_, _Descartar_, _Mostrar contraseña_.
- Decorative icons get `aria-hidden="true"` and no text.
- Do not repeat what is already visible: a button with the text _Entrar_ needs no `aria-label`.

## 8. Future: multiple languages

Long-term goal: **English by default, Spanish selectable in the settings.** Not part of the current issues, but today's rules keep that change small. When it is done:

1. Split `messages.ts` into `frontend/src/shared/i18n/locales/en.ts` and `es.ts`. Both are typed with the same shape, so TypeScript reports any missing translation.
2. Add a language provider and a `useMessages()` hook. Components call `useMessages()` instead of importing `messages` directly.
3. Save the chosen language (for example in `localStorage`) and default to English.
4. Update `<html lang>` when the language changes, so screen readers pronounce the text correctly.
5. Format dates and numbers with `Intl` and the active locale, never by hand.

Until then, the only requirement is the one in section 2: **no UI text outside `messages.ts`.**

## 9. Review checklist

Before opening a pull request that adds or changes UI text:

- [ ] All new UI text (including `aria-label` and `title`) is in `messages.ts`.
- [ ] Accents, `ñ`, `¿` and `¡` are correct.
- [ ] Sentence case; no text written in uppercase.
- [ ] _tú_ form throughout.
- [ ] Buttons say exactly what they do.
- [ ] Error messages say what happened and what to do, with no technical details.
