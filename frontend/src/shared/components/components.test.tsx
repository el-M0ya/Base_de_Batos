import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Alert } from './Alert';
import { Button } from './Button';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { LoadingState } from './LoadingState';
import { Modal } from './Modal';
import { SelectField } from './SelectField';
import { TextField } from './TextField';

describe('Button', () => {
  it('renders and responds to clicks', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Guardar</Button>);
    await user.click(screen.getByRole('button', { name: 'Guardar' }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe('TextField', () => {
  it('renders label and updates value', async () => {
    const user = userEvent.setup();
    render(<TextField label="Nombre" />);
    const input = screen.getByLabelText('Nombre');
    await user.type(input, 'Press');
    expect(input).toHaveValue('Press');
  });

  it('shows error message', () => {
    render(<TextField label="Nombre" error="Campo obligatorio" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Campo obligatorio');
  });
});

describe('SelectField', () => {
  it('renders options and changes selection', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <SelectField
        label="Grupo"
        options={[
          { value: 'a', label: 'Pecho' },
          { value: 'b', label: 'Espalda' },
        ]}
        onChange={onChange}
      />,
    );
    const select = screen.getByLabelText('Grupo');
    await user.selectOptions(select, 'b');
    expect(onChange).toHaveBeenCalled();
  });
});

describe('Modal', () => {
  it('renders when open and closes on escape', () => {
    const onClose = vi.fn();
    render(
      <Modal open title="Ventana" onClose={onClose}>
        Contenido
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('does not render when closed', () => {
    render(
      <Modal open={false} onClose={() => undefined}>
        Contenido
      </Modal>,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

describe('Alert', () => {
  it('renders message', () => {
    render(<Alert variant="error">Fallo</Alert>);
    expect(screen.getByRole('alert')).toHaveTextContent('Fallo');
  });
});

describe('LoadingState', () => {
  it('renders title', () => {
    render(<LoadingState />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('renders title and action', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<EmptyState action={<button onClick={onClick}>Crear</button>} />);
    await user.click(screen.getByRole('button', { name: 'Crear' }));
    expect(onClick).toHaveBeenCalled();
  });
});

describe('ErrorState', () => {
  it('calls retry handler', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    await user.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(onRetry).toHaveBeenCalled();
  });
});