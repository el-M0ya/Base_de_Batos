import { AuthProvider } from './shared/auth/AuthContext';
import { Router } from './app/router';

/**
 * Componente raíz de la aplicación.
 *
 * @remarks
 * Envía toda la aplicación en `AuthProvider` para que la sesión esté disponible
 * en cualquier punto, y monta el enrutador (`Router`) con el application shell,
 * la navegación y las rutas protegidas por rol/capacidad.
 */
export function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  );
}

export default App;
