import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
// Estilos globales (incluyen los tokens). Se importan una sola vez, aquí.
import './shared/styles/global.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('No se encontró el elemento #root en index.html');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
