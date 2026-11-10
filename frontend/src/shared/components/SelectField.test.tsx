import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { SelectField, type SelectOption } from './SelectField';

const sites: SelectOption[] = [
  { value: 'vedado', label: 'Sede Vedado' },
  { value: 'playa', label: 'Sede Playa' },
];

describe('SelectField', () => {
  it('links the label and renders every option', () => {
    renderWithProviders(<SelectField label="Sede de entrenamiento" options={sites} />);

    const select = screen.getByLabelText('Sede de entrenamiento');
    expect(select.tagName).toBe('SELECT');
    expect(screen.getAllByRole('option')).toHaveLength(2);
  });

  it('shows the placeholder first and does not let the user pick it', () => {
    renderWithProviders(
      <SelectField
        label="Sede de entrenamiento"
        options={sites}
        placeholder="Selecciona tu sede"
        defaultValue=""
      />,
    );

    const placeholder = screen.getByRole('option', { name: 'Selecciona tu sede' });
    expect(placeholder).toBeDisabled();
    expect(screen.getByLabelText('Sede de entrenamiento')).toHaveValue('');
  });

  it('reports the chosen value through onChange', async () => {
    const onChange = vi.fn();
    const { user } = renderWithProviders(
      <SelectField label="Sede de entrenamiento" options={sites} onChange={onChange} />,
    );

    const select = screen.getByLabelText('Sede de entrenamiento');
    await user.selectOptions(select, 'playa');

    expect(select).toHaveValue('playa');
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('shows the error and marks the select as invalid', () => {
    renderWithProviders(
      <SelectField label="Sede de entrenamiento" options={sites} error="Elige una sede." />,
    );

    const select = screen.getByLabelText('Sede de entrenamiento');
    expect(select).toHaveAttribute('aria-invalid', 'true');
    expect(select).toHaveAccessibleDescription('Elige una sede.');
  });

  it('shows the hint when there is no error', () => {
    renderWithProviders(
      <SelectField label="Sede" options={sites} hint="Puedes cambiarla después." />,
    );

    expect(screen.getByLabelText('Sede')).toHaveAccessibleDescription('Puedes cambiarla después.');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
