/**
 * Todos los textos visibles de la interfaz, en español.
 *
 * @remarks
 * Centralizarlos aquí permite revisar la ortografía en un solo lugar
 * (requisito de las Orientaciones Metodológicas). Se completa en E3-04.
 */
export const messages = {
  app: {
    name: 'Base de Batos',
    tagline: 'Gestión para la generación automática de planes de entrenamiento',
  },
  textField: {
    showPassword: 'Mostrar contraseña',
    hidePassword: 'Ocultar contraseña',
  },
  alert: {
    dismiss: 'Descartar',
  },
  states: {
    loading: 'Cargando…',
    errorTitle: 'No se pudieron cargar los datos',
    errorDescription: 'Comprueba tu conexión e inténtalo de nuevo.',
    retry: 'Reintentar',
  },
  login: {
    brand: 'FORJA',
    backToHome: 'Volver a inicio',
    title: 'Inicia sesión',
    emailLabel: 'Correo electrónico',
    emailPlaceholder: 'tu.correo@gmail.com',
    passwordLabel: 'Contraseña',
    passwordPlaceholder: '••••••••••••',
    forgotPassword: '¿Has olvidado tu contraseña?',
    submit: 'Entrar',
    noAccount: '¿Aún no tienes cuenta?',
    createAccount: 'Crear cuenta',
    errors: {
      emailRequired: 'Introduce tu correo electrónico.',
      emailInvalid: 'El correo no tiene un formato válido.',
      passwordRequired: 'Introduce tu contraseña.',
      invalidCredentials: 'Correo o contraseña incorrectos. Verifica tus credenciales.',
    },
    demoSuccess: 'Credenciales correctas. La sesión real llegará con E3-06.',
  },
} as const;
