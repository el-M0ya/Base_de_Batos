import { render, type RenderOptions } from '@testing-library/react';
import type { ReactElement } from 'react';

/**
 * Options accepted by the shared test render helper.
 */
export type CustomRenderOptions = Omit<RenderOptions, 'wrapper'>;

/**
 * Renders a React element with the application's shared providers.
 *
 * @param ui - The element to render.
 * @param options - Extra render options forwarded to Testing Library.
 * @returns The Testing Library render result.
 */
export function renderWithProviders(ui: ReactElement, options?: CustomRenderOptions) {
  return render(ui, { ...options });
}

export { screen, fireEvent, waitFor, within, cleanup } from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';