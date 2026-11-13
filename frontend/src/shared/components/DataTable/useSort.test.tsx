/**
 * Pruebas del hook `useSort`.
 *
 * @remarks
 * Cubre texto, número y fecha; comparación de acentos; orden estable;
 * valores vacíos/nulo siempre al final; y cambios de dirección.
 * El hook ordena al montar con el `initialAccessor`, por lo que cada prueba
 * parte de ese estado inicial y usa `setSort` para cambiarlo.
 */
import { describe, expect, it } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSort } from './useSort';

type Row = {
  name: string;
  age: number;
  createdAt: string;
};

const rows: Row[] = [
  { name: 'Zoe', age: 30, createdAt: '2026-01-10' },
  { name: 'Ángelo', age: 25, createdAt: '2026-03-05' },
  { name: 'ana', age: 25, createdAt: '2026-02-20' },
  { name: '', age: 0, createdAt: '' },
  { name: 'Ángulo', age: 40, createdAt: '2026-01-10' },
];

function setup(initialRows: Row[], initialAccessor: keyof Row = 'name') {
  return renderHook(({ r, a }) => useSort(r, a), {
    initialProps: { r: initialRows, a: initialAccessor },
  });
}

describe('useSort - estado inicial', () => {
  it('ordena texto en orden ascendente por defecto al montar', () => {
    const { result } = setup(rows);

    expect(result.current.sortDirection).toBe('asc');
    expect(result.current.sortAccessor).toBe('name');
    expect(result.current.sorted.map((r) => r.name)).toEqual([
      'ana',
      'Ángelo',
      'Ángulo',
      'Zoe',
      '',
    ]);
  });
});

describe('useSort - texto con acentos', () => {
  it('ordena ignorando mayúsculas y acentos (Ángelo y Ángulo junto a A)', () => {
    const { result } = setup(rows, 'name');

    const names = result.current.sorted.map((r) => r.name);
    expect(names[0]).toBe('ana');
    expect(names[1]).toBe('Ángelo');
    expect(names[2]).toBe('Ángulo');
    expect(names[3]).toBe('Zoe');
    expect(names[4]).toBe('');
  });
});

describe('useSort - números', () => {
  it('ordena números en orden ascendente', () => {
    const { result } = setup(rows, 'age');

    const ages = result.current.sorted.map((r) => r.age);
    expect(ages).toEqual([0, 25, 25, 30, 40]);
  });
});

describe('useSort - fechas', () => {
  it('ordena fechas ISO en orden ascendente', () => {
    const { result } = setup(rows, 'createdAt');

    const dates = result.current.sorted.map((r) => r.createdAt);
    expect(dates).toEqual(['2026-01-10', '2026-01-10', '2026-02-20', '2026-03-05', '']);
  });
});

describe('useSort - cambio de dirección', () => {
  it('al ordenar la misma columna alterna asc → desc → asc', () => {
    const { result } = setup(rows, 'name');

    expect(result.current.sortDirection).toBe('asc');

    act(() => {
      result.current.setSort('name');
    });
    expect(result.current.sortDirection).toBe('desc');

    act(() => {
      result.current.setSort('name');
    });
    expect(result.current.sortDirection).toBe('asc');
  });

  it('al cambiar a otra columna empieza en asc', () => {
    const { result } = setup(rows, 'name');

    act(() => {
      result.current.setSort('age');
    });

    expect(result.current.sortAccessor).toBe('age');
    expect(result.current.sortDirection).toBe('asc');
    expect(result.current.sorted.map((r) => r.age)).toEqual([0, 25, 25, 30, 40]);
  });
});

describe('useSort - orden estable y vacíos', () => {
  it('mantiene el orden estable cuando los valores son iguales', () => {
    const { result } = setup(rows, 'age');

    // 'Ángelo' está antes que 'ana' en el array original; ambos tienen age 25.
    const ages25 = result.current.sorted.filter((r) => r.age === 25);
    expect(ages25).toHaveLength(2);
    expect(ages25[0]?.name).toBe('Ángelo');
    expect(ages25[1]?.name).toBe('ana');
  });

  it('coloca valores vacíos siempre al final, en asc', () => {
    const { result } = setup(rows, 'name');

    const names = result.current.sorted.map((r) => r.name);
    expect(names.at(-1)).toBe('');
  });

  it('coloca valores vacíos siempre al final, en desc', () => {
    const { result } = setup(rows, 'name');

    act(() => {
      result.current.setSort('name'); // asc → desc
    });

    const names = result.current.sorted.map((r) => r.name);
    expect(names[0]).toBe('Zoe');
    expect(names.at(-1)).toBe('');
  });
});
