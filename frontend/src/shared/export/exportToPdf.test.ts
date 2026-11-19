import { beforeEach, describe, expect, it, vi } from 'vitest';
import { exportToPdf, formatGeneratedDate, pdfFileName } from './exportToPdf';

// Fake jsPDF document: records what the code asks it to draw. No real PDF is built.
const doc = {
  text: vi.fn(),
  setFontSize: vi.fn(),
  setTextColor: vi.fn(),
  save: vi.fn(),
};
const jsPdfConstructor = vi.fn();
const autoTable = vi.fn();

vi.mock('jspdf', () => ({
  jsPDF: function FakeJsPdf(options: unknown) {
    jsPdfConstructor(options);
    return doc;
  },
}));
vi.mock('jspdf-autotable', () => ({ default: autoTable }));

/** Fixed generation date: 15 Nov 2026, 09:05 local time. */
const NOW = new Date(2026, 10, 15, 9, 5);

const table = { head: ['Nombre', 'Carga'], body: [['Sentadilla', '80']] };

/** All texts written with `doc.text`, in order. */
function writtenTexts(): unknown[] {
  return doc.text.mock.calls.map((call) => call[0]);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('exportToPdf helpers', () => {
  it('formats the generation date with two-digit parts', () => {
    expect(formatGeneratedDate(NOW)).toBe('15/11/2026 09:05');
  });

  it('appends the date to the file name', () => {
    expect(pdfFileName('ejercicios', NOW)).toBe('ejercicios-2026-11-15.pdf');
  });
});

describe('exportToPdf', () => {
  it('writes title, subtitle and date, draws the table and saves the file', async () => {
    await exportToPdf(
      { title: 'Ejercicios', subtitle: 'Grupo muscular: Pecho', fileName: 'ejercicios', table },
      NOW,
    );

    expect(jsPdfConstructor).toHaveBeenCalledWith({ orientation: 'landscape' });
    expect(writtenTexts()).toEqual([
      'Ejercicios',
      'Grupo muscular: Pecho',
      'Generado el 15/11/2026 09:05',
    ]);
    expect(autoTable).toHaveBeenCalledWith(
      doc,
      expect.objectContaining({ head: [table.head], body: table.body }),
    );
    expect(doc.save).toHaveBeenCalledWith('ejercicios-2026-11-15.pdf');
  });

  it('omits the subtitle line when there is none', async () => {
    await exportToPdf({ title: 'Ejercicios', fileName: 'ejercicios', table }, NOW);

    expect(writtenTexts()).toEqual(['Ejercicios', 'Generado el 15/11/2026 09:05']);
  });
});
