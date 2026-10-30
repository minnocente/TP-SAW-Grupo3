# Credenciales y datos de prueba

## Usuarios

| Usuario | Contraseña | Rol | Cliente (client_id) |
|---------|-----------|-----|---------------------|
| `nico` | `nico123` | user | Distribuidora Rápida SRL (89) |
| `clopez` | `cliente123` | user | Comercial Lopez e Hijos S.A. (458) |
| `admin` | `admin123` | admin | OrderFlow Operaciones (1) |

> El **atacante** de la demo es **`nico`** (permisos básicos). La **víctima** es
> el cliente **458** (titular "Carlos Lopez").

## Mapa de pedidos (para la demo — endpoint del comprobante, Paso 2)

| Pedido | Cliente | `factura_referencia` | Rol en la demo |
|--------|---------|----------------------|----------------|
| 102, 103, **105** | 89 | FAC-2026-00087/00088/00089 | Pedidos propios del atacante (`nico`) |
| 100, 101, **104** | 458 | FAC-2026-00456/00457/**00458** | **Objetivos** del IDOR (víctima) |

- Como `nico`, tu pedido propio de referencia es **#105**.
- Probando hacia atrás llegás al **#104** (de la víctima), que devuelve
  `cliente_id=458` y `factura_referencia="FAC-2026-00458"`.

## Mapa de transacciones (Pasos 3 y 4 — endpoint `facturas/ver`)

| id | cliente_id | ref | Rol en la demo |
|----|-----------|-----|----------------|
| 88 | 458 | FAC-2026-00456 | Historial de la víctima |
| 95 | 458 | FAC-2026-00457 | Historial de la víctima |
| **104** | 458 | **FAC-2026-00458** | Factura del comprobante del Paso 2 |
| 112 | 89 | FAC-2026-00089 | Transacción propia del atacante |
| 120 | 1 | FAC-2026-00001 | Otro cliente (ruido) |

- La referencia **`FAC-2026-00458`** (obtenida en el Paso 2) es la entrada del Paso 3.
- El payload final `FAC-2026-00458' OR cliente_id=458--` devuelve las 3
  transacciones de la víctima (88, 95, 104) con `datos_pago` en texto plano.
