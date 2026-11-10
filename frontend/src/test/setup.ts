// Preparación común de todas las pruebas de Vitest.
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Sin `globals: true`, Testing Library no limpia el DOM por sí sola entre pruebas.
afterEach(() => {
  cleanup();
});

// jsdom does not implement the <dialog> methods (real browsers do).
// Minimal test-only versions: they just toggle the `open` attribute.
HTMLDialogElement.prototype.showModal ??= function showModal(this: HTMLDialogElement) {
  this.setAttribute('open', '');
};
HTMLDialogElement.prototype.close ??= function close(this: HTMLDialogElement) {
  this.removeAttribute('open');
};
