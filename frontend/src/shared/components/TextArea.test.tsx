import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { TextArea } from './TextArea';

describe('TextArea', () => {
  it('links the label to the textarea', () => {
    renderWithProviders(<TextArea label="Descripción" />);

    // Finding the field by its label only works if they are linked.
    expect(screen.getByLabelText('Descripción').tagName).toBe('TEXTAREA');
  });

  it('lets the user type several lines', async () => {
    const { user } = renderWithProviders(<TextArea label="Descripción" />);

    const textarea = screen.getByLabelText('Descripción');
    await user.type(textarea, 'Primera línea{Enter}Segunda línea');

    expect(textarea).toHaveValue('Primera línea\nSegunda línea');
  });

  it('uses 4 rows by default and accepts another value', () => {
    const { unmount } = renderWithProviders(<TextArea label="Descripción" />);
    expect(screen.getByLabelText('Descripción')).toHaveAttribute('rows', '4');
    unmount();

    renderWithProviders(<TextArea label="Descripción" rows={2} />);
    expect(screen.getByLabelText('Descripción')).toHaveAttribute('rows', '2');
  });

  it('shows the error, marks the textarea as invalid and links the message', () => {
    renderWithProviders(<TextArea label="Descripción" error="La descripción es obligatoria." />);

    const textarea = screen.getByLabelText('Descripción');
    expect(textarea).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent('La descripción es obligatoria.');
    expect(textarea).toHaveAccessibleDescription('La descripción es obligatoria.');
  });

  it('shows the hint when there is no error', () => {
    renderWithProviders(<TextArea label="Descripción" hint="Opcional" />);

    expect(screen.getByLabelText('Descripción')).toHaveAccessibleDescription('Opcional');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
