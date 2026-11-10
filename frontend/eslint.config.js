// @ts-check
import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsdoc from 'eslint-plugin-jsdoc';
import prettier from 'eslint-config-prettier';

/**
 * Reglas de calidad del frontend (E3-01, RNF-07):
 * - sin variables sin usar ni `any` implícito o explícito;
 * - dependencias completas en los hooks;
 * - comentarios estructurados (TSDoc) en componentes, hooks y utilidades exportados.
 * Prettier se encarga del formato, por eso va al final y desactiva las reglas de estilo.
 */
export default tseslint.config(
  { ignores: ['dist', 'coverage', 'node_modules'] },

  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.strict],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      jsdoc,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-hooks/exhaustive-deps': 'error',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': 'error',

      // TSDoc obligatorio solo en lo que se exporta.
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: true,
          require: {
            FunctionDeclaration: true,
            ArrowFunctionExpression: true,
            FunctionExpression: true,
            ClassDeclaration: true,
          },
          contexts: ['TSInterfaceDeclaration', 'TSTypeAliasDeclaration'],
        },
      ],
      'jsdoc/require-description': 'error',
      'jsdoc/check-tag-names': ['error', { definedTags: ['remarks', 'example'] }],
    },
  },

  // Pruebas y configuración: sin exigir TSDoc ni la regla de Fast Refresh.
  {
    files: ['**/*.test.{ts,tsx}', 'src/test/**', '*.config.{ts,js}'],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: {
      'jsdoc/require-jsdoc': 'off',
      'react-refresh/only-export-components': 'off',
    },
  },

  prettier,
);
