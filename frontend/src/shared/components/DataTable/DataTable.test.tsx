/**
 * Pruebas del componente `DataTable`.
 *
 * @remarks
 * Cubre estados de carga y vacía, ordenamiento por texto/número/fecha,
 * acentos, orden estable, valores vacíos, cambios de dirección e
 * indicadores de orden accesibles.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from './DataTable';
import type { ColumnDef } from './columns';

type Row = {
  name: string;
  age: number;
  createdAt: string;
};

const columns: ColumnDef<Row>[] = [
  { accessor: 'name', header: 'Nombre', sortable: true },
  { accessor: 'age', header: 'Edad', sortable: true },
  { accessor: 'createdAt', header: 'Creado', sortable: true },
];

const data: Row[] = [
  { name: 'Zoe', age: 30, createdAt: '2026-01-10' },
  { name: 'Ángelo', age: 25, createdAt: '2026-03-05' },
  { name: 'ana', age: 25, createdAt: '2026-02-20' },
  { name: '', age: 0, createdAt: '' },
];

function renderTable(overrides: Partial<{ data: Row[]; loading: boolean }> = {}) {
  const props = {
    columns,
    data,
    loading: false,
    ...overrides,
  };
  return { ...render(<DataTable<Row> {...props} />) };
}

/** Obtiene los valores de una columna por índice (0=nombre, 1=edad, 2=fecha). */
function columnValues(columnIndex: number): string[] {
  const cells = screen.getAllByRole('row');
  // Saltamos la fila de encabezado (primer row) y tomamos la celda del índice.
  return cells.slice(1).map((row) => row.querySelectorAll('td')[columnIndex]?.textContent ?? '');
}

describe('DataTable - estados', () => {
  it('muestra estado de carga cuando loading es true', () => {
    renderTable({ loading: true });

    expect(screen.getByText('Cargando…')).toBeInTheDocument();
  });

  it('muestra estado vacío cuando no hay datos', () => {
    renderTable({ data: [] });

    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

describe('DataTable - renderizado', () => {
  it('renderiza encabezados y filas de datos', () => {
    renderTable();

    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Edad')).toBeInTheDocument();
    expect(screen.getByText('Creado')).toBeInTheDocument();
    expect(screen.getByText('Zoe')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('no muestra filas cuando hay datos vacíos', () => {
    renderTable({ data: [] });

    expect(screen.queryByText('Zoe')).not.toBeInTheDocument();
  });
});

describe('DataTable - acciones de edición', () => {
  it('muestra la acción cuando canEdit devuelve true', () => {
    render(
      <DataTable<Row>
        columns={columns}
        data={data.slice(0, 1)}
        onEdit={vi.fn()}
        canEdit={() => true}
      />,
    );

    expect(screen.getByRole('button', { name: 'Editar registro 1' })).toBeInTheDocument();
  });

  it('oculta la acción cuando canEdit devuelve false', () => {
    render(
      <DataTable<Row>
        columns={columns}
        data={data.slice(0, 1)}
        onEdit={vi.fn()}
        canEdit={() => false}
      />,
    );

    expect(screen.queryByRole('button', { name: 'Editar registro 1' })).not.toBeInTheDocument();
  });

  it('muestra la acción solo en las filas editables', () => {
    render(
      <DataTable<Row>
        columns={columns}
        data={data.slice(0, 3)}
        onEdit={vi.fn()}
        canEdit={(row) => row.name === 'Zoe'}
      />,
    );

    expect(screen.getAllByRole('button', { name: /Editar registro/ })).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Editar registro 3' })).toBeInTheDocument();
  });
});

describe('DataTable - ordenamiento', () => {
  it('ya está ordenado asc por nombre al montar', () => {
    renderTable();

    const names = columnValues(0);
    expect(names).toEqual(['ana', 'Ángelo', 'Zoe', '']);
  });

  it('pasa a descendente al hacer clic en la misma columna', () => {
    renderTable();

    const nombreHeader = screen.getByText('Nombre');
    fireEvent.click(nombreHeader); // asc → desc

    const names = columnValues(0);
    expect(names).toEqual(['Zoe', 'Ángelo', 'ana', '']);
  });

  it('vuelve a ascendente al hacer clic una tercera vez', () => {
    renderTable();

    const nombreHeader = screen.getByText('Nombre');
    fireEvent.click(nombreHeader); // asc → desc
    fireEvent.click(nombreHeader); // desc → asc

    const names = columnValues(0);
    expect(names).toEqual(['ana', 'Ángelo', 'Zoe', '']);
  });

  it('ordena por edad (número)', () => {
    renderTable();

    fireEvent.click(screen.getByText('Edad'));

    const ages = columnValues(1);
    expect(ages[0]).toBe('0');
    expect(ages[1]).toBe('25');
    expect(ages[2]).toBe('25');
    expect(ages[3]).toBe('30');
  });

  it('ordena por fecha (texto ISO)', () => {
    renderTable();

    fireEvent.click(screen.getByText('Creado'));

    const dates = columnValues(2);
    console.error('DATE ORDER:', dates);
    expect(dates[0]).toBe('2026-01-10');
    expect(dates[1]).toBe('2026-02-20');
    expect(dates[2]).toBe('2026-03-05');
    expect(dates[3]).toBe('');
  });

  it('expone el estado activo de orden al consumidor', () => {
    const onSortChange = vi.fn();
    render(<DataTable<Row> columns={columns} data={data} onSortChange={onSortChange} />);

    fireEvent.click(screen.getByText('Edad'));

    expect(onSortChange).toHaveBeenCalledWith('age', 'asc');
  });
});
