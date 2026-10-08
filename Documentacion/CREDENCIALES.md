# Credenciales y datos de prueba

## Usuarios

| Usuario | Contraseña | Rol | Cliente (client_id) |
|---------|-----------|-----|---------------------|
| `nico` | `nico123` | user | Competidora Rápida SRL (89) |
| `clopez` | `cliente123` | user | Comercial Lopez e Hijos S.A. (458) |
| `admin` | `admin123` | admin | OrderFlow Operaciones (1) |

> El **atacante** de la demo es **`nico`** (permisos básicos). La **víctima** es
> el cliente **458** (titular "Carlos Lopez").

## Mapa de pedidos (para la demo — endpoint del comprobante, Paso 2)

| Pedido | Cliente | `factura_referencia` | Rol en la demo |
|--------|---------|----------------------|----------------|
| 102, 103, **105** | 89 | FAC-2026-3BQZ6R0T / TM5W8K1C / **N1P4X7LC** | Pedidos propios del atacante (`nico`) |
| 100, 101, **104** | 458 | FAC-2026-9F2KQ7JD / D4XP1M8A / **A7K9QD2F** | **Objetivos** del IDOR (víctima) |

- Como `nico`, tu pedido propio de referencia es **#105**.
- Probando hacia atrás llegás al **#104** (de la víctima), que devuelve
  `cliente_id=458` y `factura_referencia="FAC-2026-A7K9QD2F"` (token opaco: no es
  adivinable ni deducible de la doc; **sólo** se obtiene con este IDOR).

## Mapa del ledger `ldg_fin_legacy` (Pasos 3 y 4 — endpoint `facturas/ver`)

> Nombres de columnas opacos a propósito: `acct_no` (cliente), `doc_ref` (referencia),
> `pay_raw` (tarjeta). El atacante sólo los descubre leyendo la fuga de error del Paso 3.

| id | acct_no | doc_ref | Rol en la demo |
|----|---------|---------|----------------|
| 88 | 458 | FAC-2026-9F2KQ7JD | Historial de la víctima |
| 95 | 458 | FAC-2026-D4XP1M8A | Historial de la víctima |
| **104** | 458 | **FAC-2026-A7K9QD2F** | Factura del comprobante del Paso 2 |
| 112 | 89 | FAC-2026-N1P4X7LC | Transacción propia del atacante |
| 120 | 1 | FAC-2026-0QW3E8ZK | Otro cliente (ruido) |

- La referencia **`FAC-2026-A7K9QD2F`** (obtenida en el Paso 2) es la entrada del Paso 3.
- El payload final `FAC-2026-A7K9QD2F' OR acct_no=458--` devuelve las 3
  transacciones de la víctima (88, 95, 104) con `pay_raw` en texto plano.
- **Encadenamiento:** la `doc_ref` y el `acct_no=458` salen del Paso 2; el nombre de
  columna `acct_no` sale de la fuga del Paso 3. Sin esos datos no se llega al payload acotado.
