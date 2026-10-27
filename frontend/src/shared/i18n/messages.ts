/**
 * All user-facing Spanish strings live here for review in a single place.
 */
export const messages = {
  app: {
    title: 'Planificador de Rutinas de Gimnasio',
  },
  common: {
    loading: 'Cargando…',
    retry: 'Reintentar',
    cancel: 'Cancelar',
    save: 'Guardar',
    create: 'Crear',
    edit: 'Editar',
    delete: 'Eliminar',
    close: 'Cerrar',
    search: 'Buscar',
    confirm: 'Confirmar',
    back: 'Volver',
    next: 'Siguiente',
    previous: 'Anterior',
    noResults: 'Sin resultados',
  },
  form: {
    required: 'Este campo es obligatorio.',
    invalidEmail: 'Introduce un correo electrónico válido.',
    minLength: 'Debe tener al menos {min} caracteres.',
  },
  states: {
    loadingTitle: 'Cargando información',
    loadingDescription: 'Estamos preparando los datos.',
    emptyTitle: 'Sin resultados',
    emptyDescription: 'No hay información para mostrar.',
    errorTitle: 'Algo salió mal',
    errorDescription: 'No se pudo cargar la información. Inténtalo de nuevo.',
  },
  button: {
    primary: 'Acción principal',
  },
  modal: {
    closeLabel: 'Cerrar ventana',
  },
  alert: {
    info: 'Información',
    success: 'Éxito',
    warning: 'Advertencia',
    error: 'Error',
  },
} as const;

export type Messages = typeof messages;