import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { Button } from './Button';

describe('Button', () => {
  it('muestra su texto y es de tipo "button" por defecto', () => {
    renderWithProviders(<Button>Entrar</Button>);

    const boton = screen.getByRole('button', { name: 'Entrar' });
    expect(boton).toBeInTheDocument();
    // Por defecto NO es "submit", para no enviar formularios sin querer.
    expect(boton).toHaveAttribute('type', 'button');
  });

  it('llama a onClick al pulsarlo', async () => {
    const alPulsar = vi.fn();
    const { user } = renderWithProviders(<Button onClick={alPulsar}>Guardar</Button>);

    await user.click(screen.getByRole('button', { name: 'Guardar' }));

    expect(alPulsar).toHaveBeenCalledTimes(1);
  });

  it('se puede activar con el teclado (Tab + Enter)', async () => {
    const alPulsar = vi.fn();
    const { user } = renderWithProviders(<Button onClick={alPulsar}>Guardar</Button>);

    await user.tab();
    expect(screen.getByRole('button', { name: 'Guardar' })).toHaveFocus();
    await user.keyboard('{Enter}');

    expect(alPulsar).toHaveBeenCalledTimes(1);
  });

  it('mientras carga está desactivado, marcado como ocupado y no responde', async () => {
    const alPulsar = vi.fn();
    const { user } = renderWithProviders(
      <Button isLoading onClick={alPulsar}>
        Entrar
      </Button>,
    );

    const boton = screen.getByRole('button', { name: 'Entrar' });
    expect(boton).toBeDisabled();
    expect(boton).toHaveAttribute('aria-busy', 'true');

    await user.click(boton);
    expect(alPulsar).not.toHaveBeenCalled();
  });

  it('aplica la clase de la variante elegida', () => {
    renderWithProviders(<Button variant="ghost">Volver a inicio</Button>);

    expect(screen.getByRole('button', { name: 'Volver a inicio' })).toHaveClass('ghost');
  });
});
