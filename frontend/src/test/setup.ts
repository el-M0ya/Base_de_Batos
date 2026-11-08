// Preparación común de todas las pruebas de Vitest.
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Sin `globals: true`, Testing Library no limpia el DOM por sí sola entre pruebas.
afterEach(() => {
  cleanup();
});
