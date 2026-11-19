import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExportPdfButton } from './ExportPdfButton';
import type { PdfExportOptions } from '../export/exportToPdf';

const mocks = vi.hoisted(() => ({ exportToPdf: vi.fn() }));
vi.mock('../export/exportToPdf', () => ({ exportToPdf: mocks.exportToPdf }));

const options: PdfExportOptions = {
  title: 'Ejercicios',
  fileName: 'ejercicios',
  table: { head: ['Nombre'], body: [['Sentadilla']] },
};

beforeEach(() => {
  mocks.exportToPdf.mockReset();
});

describe('ExportPdfButton', () => {
  it('asks for the export data at click time and exports it', async () => {
    const user = userEvent.setup();
    mocks.exportToPdf.mockResolvedValue(undefined);
    const getExport = vi.fn(() => options);
    render(<ExportPdfButton getExport={getExport} />);

    expect(getExport).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Exportar PDF' }));

    expect(getExport).toHaveBeenCalledTimes(1);
    expect(mocks.exportToPdf).toHaveBeenCalledWith(options);
  });

  it('shows a busy state while the PDF is generated', async () => {
    const user = userEvent.setup();
    let finish: () => void = () => {};
    mocks.exportToPdf.mockReturnValue(new Promise<void>((resolve) => (finish = resolve)));
    render(<ExportPdfButton getExport={() => options} />);

    await user.click(screen.getByRole('button', { name: 'Exportar PDF' }));
    const busy = screen.getByRole('button', { name: 'Exportando…' });
    expect(busy).toBeDisabled();

    finish();
    expect(await screen.findByRole('button', { name: 'Exportar PDF' })).toBeEnabled();
  });

  it('shows an error alert when the export fails', async () => {
    const user = userEvent.setup();
    mocks.exportToPdf.mockRejectedValue(new Error('boom'));
    render(<ExportPdfButton getExport={() => options} />);

    await user.click(screen.getByRole('button', { name: 'Exportar PDF' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo generar el PDF.');
    expect(screen.getByRole('button', { name: 'Exportar PDF' })).toBeEnabled();
  });

  it('can be disabled by the page', () => {
    render(<ExportPdfButton getExport={() => options} disabled />);

    expect(screen.getByRole('button', { name: 'Exportar PDF' })).toBeDisabled();
  });
});
