# Credenciales y datos de prueba

## Usuarios

| Usuario | Contraseña | Rol | Cliente (client_id) |
|---------|-----------|-----|---------------------|
| `cliente1` | `cliente123` | user | Distribuidora Andina S.A. (2) |
| `cliente2` | `cliente123` | user | Comercial del Plata SRL (3) |
| `cliente3` | `cliente123` | user | Importadora Sur SA (4) |
| `admin` | `admin123` | admin | OrderFlow Operaciones (1) |

> El **atacante** de la demo es **`cliente1`** (permisos básicos).

## Mapa de pedidos (para la demo)

| Pedido | Cliente | Dueño legítimo | Rol en la demo |
|--------|---------|----------------|----------------|
| 1, 2, 7 | 2 | `cliente1` | Pedidos propios del atacante |
| **3, 4, 8** | 3 | `cliente2` | **Objetivos** de IDOR (Paso 2) y modificación (Paso 4) |
| 5, 6 | 4 | `cliente3` | Pedidos de otro cliente |

- Como `cliente1`, tus pedidos propios son **#1, #2 y #7**.
- El pedido **#3** (de `cliente2`) es el objetivo recomendado para la demo:
  se lee por IDOR (Paso 2) y se modifica por BFLA (Paso 4).
