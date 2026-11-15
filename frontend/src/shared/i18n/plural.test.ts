import { describe, expect, it } from 'vitest';
import { plural } from './plural';

const forms = { one: 'configurado', other: 'configurados' };

describe('plural', () => {
  it('uses the singular for 1', () => {
    expect(plural(1, forms)).toBe('configurado');
  });

  it('uses the plural for 0', () => {
    expect(plural(0, forms)).toBe('configurados');
  });

  it('uses the plural for numbers greater than 1', () => {
    expect(plural(2, forms)).toBe('configurados');
    expect(plural(15, forms)).toBe('configurados');
  });
});
