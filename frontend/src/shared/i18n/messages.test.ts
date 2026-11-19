import { describe, expect, it } from 'vitest';
import { messages } from './messages';

describe('messages', () => {
  it('writes the configured muscle-group count with the right plural', () => {
    const configuredCount = messages.trainingPrograms.table.configuredCount;

    expect(configuredCount(0)).toBe('0 configurados');
    expect(configuredCount(1)).toBe('1 configurado');
    expect(configuredCount(3)).toBe('3 configurados');
  });
});
