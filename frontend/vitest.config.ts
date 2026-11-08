import { defineConfig } from 'vitest/config';

/**
 * Vitest configuration for the frontend test suite.
 *
 * @returns The resolved Vitest configuration.
 */
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
    css: true,
  },
});