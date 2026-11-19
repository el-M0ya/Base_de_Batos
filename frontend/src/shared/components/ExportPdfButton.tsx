import { useState } from 'react';
import { Download } from 'lucide-react';
import { Button } from './Button';
import { Alert } from './Alert';
import { exportToPdf, type PdfExportOptions } from '../export/exportToPdf';
import { messages } from '../i18n/messages';
import styles from './ExportPdfButton.module.css';

const t = messages.pdfExport;

/** Props of the export button. */
export interface ExportPdfButtonProps {
  /**
   * Returns what to export. It is called at click time, so the PDF always
   * contains what the user sees at that moment (current filters and order).
   */
  getExport: () => PdfExportOptions;
  /** Disables the button, e.g. while there is nothing to export. */
  disabled?: boolean;
}

/**
 * "Exportar PDF" button shared by the exercise list and the reports.
 *
 * @remarks
 * Shows a busy state while the PDF is generated (which also prevents double
 * clicks) and an error alert if the generation fails.
 */
export function ExportPdfButton({ getExport, disabled = false }: ExportPdfButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleClick() {
    setFailed(false);
    setIsExporting(true);
    try {
      await exportToPdf(getExport());
    } catch {
      setFailed(true);
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className={styles.wrapper}>
      <Button
        variant="secondary"
        icon={<Download size={18} />}
        isLoading={isExporting}
        disabled={disabled}
        title={t.hint}
        onClick={() => void handleClick()}
      >
        {isExporting ? t.exporting : t.button}
      </Button>
      {failed && <Alert onDismiss={() => setFailed(false)}>{t.failed}</Alert>}
    </div>
  );
}
