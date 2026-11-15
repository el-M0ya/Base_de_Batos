/**
 * The words for each plural form. `one` is the singular; `other` is used for
 * every other number (0, 2, 3...) in Spanish and English.
 */
export interface PluralForms {
  /** Singular form, e.g. `'configurado'`. */
  one: string;
  /** Plural form, e.g. `'configurados'`. */
  other: string;
}

// Created once and reused: building a PluralRules object is relatively costly.
const spanishRules = new Intl.PluralRules('es');

/**
 * Picks the right singular/plural word for a number.
 *
 * @remarks
 * Uses the browser's built-in `Intl.PluralRules`, which knows the plural
 * rules of each language, so the same helper will work when the UI gets
 * an English version.
 *
 * @param count - The number being described.
 * @param forms - The singular and plural words.
 * @returns The word that matches `count` (without the number).
 *
 * @example
 * ```ts
 * plural(1, { one: 'configurado', other: 'configurados' }); // 'configurado'
 * plural(3, { one: 'configurado', other: 'configurados' }); // 'configurados'
 * ```
 */
export function plural(count: number, forms: PluralForms): string {
  return spanishRules.select(count) === 'one' ? forms.one : forms.other;
}
