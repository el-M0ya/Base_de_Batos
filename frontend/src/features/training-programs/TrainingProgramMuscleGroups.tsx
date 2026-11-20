import type { MuscleGroup } from '../../shared/types/muscleGroup';
import { messages } from '../../shared/i18n/messages';
import styles from './TrainingProgramMuscleGroups.module.css';

const t = messages.trainingPrograms.muscleGroupPicker;

/** Props for the muscle-group association editor. */
export interface TrainingProgramMuscleGroupsProps {
  /** Available options loaded from the muscle-group API. */
  groups: readonly MuscleGroup[];
  /** Currently selected group identifiers. */
  selectedIds: readonly string[];
  /** Reports the next selected identifier set. */
  onChange: (selectedIds: string[]) => void;
  /** Optional validation message. */
  error?: string | undefined;
  /** Disables selection while the program is being saved. */
  disabled?: boolean;
}

/**
 * Selector and summary for a program's covered muscle groups.
 *
 * @remarks
 * It uses checkboxes instead of a native multi-select so the selected
 * associations are visible and easy to edit. The component is deliberately
 * unaware of API details; the form owns loading and error state.
 */
export function TrainingProgramMuscleGroups({
  groups,
  selectedIds,
  onChange,
  error,
  disabled = false,
}: TrainingProgramMuscleGroupsProps) {
  /** Toggles one group while preserving the other associations. */
  function toggleGroup(id: string) {
    const nextIds = selectedIds.includes(id)
      ? selectedIds.filter((selectedId) => selectedId !== id)
      : [...selectedIds, id];
    onChange(nextIds);
  }

  const selectedGroups = groups.filter((group) => selectedIds.includes(group.id));

  return (
    <fieldset className={styles.fieldset} disabled={disabled}>
      <legend className={styles.legend}>{t.legend}</legend>
      <p className={styles.hint}>{t.hint}</p>
      {groups.length === 0 ? (
        <p className={styles.empty}>{t.empty}</p>
      ) : (
        <div className={styles.options}>
          {groups.map((group) => (
            <label key={group.id} className={styles.option}>
              <input
                type="checkbox"
                checked={selectedIds.includes(group.id)}
                onChange={() => toggleGroup(group.id)}
              />
              <span>{group.name}</span>
            </label>
          ))}
        </div>
      )}
      {error !== undefined && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      <div className={styles.selected} aria-live="polite">
        <span className={styles.selectedLabel}>{t.selectedLabel}</span>{' '}
        {selectedGroups.length === 0
          ? t.noneSelected
          : selectedGroups.map((group) => group.name).join(', ')}
      </div>
    </fieldset>
  );
}
