import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

/** Estilos visuales disponibles para el botón. */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

/**
 * Props del botón.
 *
 * @remarks
 * Extiende las props nativas de `<button>` (`onClick`, `disabled`, `type`,
 * `aria-*`...), así que el componente acepta todo lo que acepta un botón HTML.
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Estilo visual. Por defecto, `primary` (píldora violeta). */
  variant?: ButtonVariant;
  /** Muestra un indicador de carga y desactiva el botón mientras dura. */
  isLoading?: boolean;
  /** Ocupa todo el ancho de su contenedor (como "Entrar" en el login). */
  fullWidth?: boolean;
  /** Icono opcional que aparece a la derecha del texto. */
  icon?: ReactNode;
  /** Texto del botón. */
  children: ReactNode;
}

/**
 * Botón base del sistema FORJA: forma de píldora, tres variantes y estado de carga.
 *
 * @example
 * ```tsx
 * <Button type="submit" fullWidth isLoading={enviando}>Entrar</Button>
 * <Button variant="ghost" onClick={volver}>Volver a inicio</Button>
 * ```
 */
export function Button({
  variant = 'primary',
  isLoading = false,
  fullWidth = false,
  icon,
  type = 'button',
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  // Unimos las clases CSS que tocan según las props. `filter(Boolean)` quita las vacías.
  const classes = [
    styles.button,
    styles[variant],
    fullWidth ? styles.fullWidth : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      {...rest}
      type={type}
      className={classes}
      // Mientras carga no se puede pulsar otra vez (evita envíos duplicados).
      disabled={disabled === true || isLoading}
      // Avisa a los lectores de pantalla de que el botón está ocupado.
      aria-busy={isLoading || undefined}
    >
      {isLoading && <span className={styles.spinner} aria-hidden="true" />}
      <span>{children}</span>
      {icon !== undefined && !isLoading && (
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
      )}
    </button>
  );
}
