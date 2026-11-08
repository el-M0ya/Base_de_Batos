import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Configuración de Vite.
 *
 * `VITE_BASE_PATH` permite publicar la aplicación bajo un subdirectorio
 * (por ejemplo `/Base_de_Batos/` en GitHub Pages, ver E3-10). En desarrollo
 * y en el contenedor se sirve desde la raíz.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [react()],
    css: {
      modules: {
        // Permite escribir `styles.primaryButton` para la clase `.primary-button`.
        localsConvention: 'camelCaseOnly',
      },
    },
    server: {
      port: 5173,
    },
  };
});
