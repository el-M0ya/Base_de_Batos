import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.ts';

/**
 * Configuración de Vitest. Reutiliza la de Vite (plugins, CSS Modules) y añade
 * el entorno jsdom, el fichero de preparación y la cobertura que publica la CI.
 */
export default defineConfig((env) =>
  mergeConfig(viteConfig(env), {
    test: {
      environment: 'jsdom',
      // Tests always run as if no .env.local existed: an empty VITE_API_MODE keeps
      // every API on its mock and the regular router ('mock' would switch to the
      // hash router used by the static demo). The exercises module has its own
      // switch (VITE_EXERCISE_API), so it is forced to the mock as well.
      env: { VITE_API_MODE: '', VITE_EXERCISE_API: 'mock' },
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      css: { modules: { classNameStrategy: 'non-scoped' } },
      restoreMocks: true,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov'],
        reportsDirectory: './coverage',
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['src/**/*.test.{ts,tsx}', 'src/test/**', 'src/main.tsx', 'src/**/*.d.ts'],
      },
    },
  }),
);
