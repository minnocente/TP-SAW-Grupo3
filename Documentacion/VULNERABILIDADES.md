# Análisis de vulnerabilidades y mitigaciones

Detalle técnico de cada vulnerabilidad sembrada, su ubicación en el código, el
impacto y cómo se corregiría. Material para el informe.

---

## Paso 1 — A02:2021 Security Misconfiguration

- **Dónde:** `app/__init__.py` (registro de Swagger UI en `/api/docs` sin
  autenticación) y `app/config.py` (`DEBUG = True`).
- **Causa:** la documentación de la API y los errores detallados quedan
  disponibles para cualquiera, exponiendo endpoints, parámetros y estructura.
  En particular, el grupo **"Reportes (v1)"** revela un endpoint *legacy*
  (`GET /api/v1/pedidos/{id}/comprobante`) que no aparece en la web pública.
- **Impacto:** reconocimiento. El atacante obtiene la ruta y el formato exacto de
  endpoints no listados en la UI.
- **Mitigación:**
  - No publicar Swagger/OpenAPI en entornos accesibles por usuarios finales, o
    protegerlo tras autenticación/rol de administrador.
  - `DEBUG = False` en cualquier entorno no local; manejar errores con páginas
    genéricas.
  - Dar de baja los endpoints *legacy* y separar la documentación interna de la expuesta.

---

## Paso 2 — A01:2021 Broken Access Control (IDOR)

- **Dónde:** `app/routes/api.py` → `comprobante()`
  (`GET /api/v1/pedidos/<pedido_id>/comprobante`).
- **Causa:** se verifica *autenticación* pero no *autorización*: no se comprueba
  que el pedido pertenezca al `client_id` del usuario de la sesión. Probando ids
  correlativos se accede a comprobantes ajenos.
- **Impacto:** acceso a datos de otros clientes y obtención de identificadores
  reutilizables (`cliente_id` de la víctima y su `factura_referencia`, un token
  **opaco** no adivinable). Es la **única** fuente de estos valores: sin este paso
  no se pueden armar los Pasos 3 y 4 (dependencia explícita del encadenamiento).
- **Mitigación:** validar propiedad del recurso en el servidor. Ejemplo:
  ```python
  if o["client_id"] != g.user["client_id"] and g.user["role"] != "admin":
      return jsonify({"error": "No autorizado"}), 403
  ```
  (Los endpoints `/api/orders/...` del laboratorio ya aplican este control.)

---

## Paso 3 — A10:2021 Mishandling of Exceptional Conditions

- **Dónde:** `app/routes/api.py` → `ver_factura()`
  (`GET /api/v1/facturas/ver`).
- **Causa:** hay un filtro de formato con regex, pero se usa `re.match(r"^FAC-\d{4}-[A-Z0-9]{8}", ref)`,
  que ancla **solo el inicio** (sin `$`): un valor que empieza con una referencia
  válida y concatena caracteres extra igual lo supera. Además, ante una excepción
  se devuelve el **mensaje de error y la query completa**.
- **Impacto:** al romper la consulta con una comilla, el 500 filtra el error del
  motor, la query y la estructura interna (tabla `ldg_fin_legacy` y sus 6 columnas,
  entre ellas `acct_no` y `pay_raw`). Esos nombres —deliberadamente opacos— son los
  que necesita el Paso 4 para acotar la inyección a la víctima: el Paso 4 depende de esta fuga.
- **Mitigación:**
  - Anclar la validación de principio a fin (`^FAC-\d{4}-[A-Z0-9]{8}$`) y, sobre todo,
    no confiar en la validación de formato como defensa contra inyección.
  - Capturar las excepciones y responder con un error **genérico**; loggear el
    detalle solo del lado del servidor (`DEBUG = False`).

---

## Paso 4 — A05:2021 Injection (SQLi) + A04:2021 Cryptographic Failures

- **Dónde:** `app/routes/api.py` → `ver_factura()` (misma ruta) y la tabla
  `ldg_fin_legacy` (`db/schema.sql` / `db/seed.sql`).
- **Causa (A05):** la consulta se arma por **concatenación de strings** con el
  parámetro `ref`, permitiendo inyección SQL. Con `' OR acct_no=458--` se
  manipula el `WHERE` para devolver todas las filas de la víctima. Este payload
  **acotado** necesita el `cliente_id=458` (Paso 2) y el nombre de columna `acct_no`
  (Paso 3): por eso el Paso 4 depende de los dos anteriores.
  > Nota: `' OR 1=1--` es un volcado **no acotado** (devuelve TODOS los clientes).
  > Es una propiedad inherente de la SQLi que no se elimina sin corregir la vuln; la
  > exfiltración dirigida *a la víctima* sí exige los datos de los Pasos 2 y 3.
- **Causa (A04):** la columna `pay_raw` almacena **PAN, vencimiento, CVV y
  titular en texto plano**, y el endpoint los devuelve tal cual.
- **Impacto:** exfiltración del historial comercial completo de la víctima y de
  sus datos de tarjeta, sin privilegios de administrador (pérdida crítica de
  confidencialidad; inteligencia comercial para captación desleal o extorsión).
- **Mitigación:**
  - Usar **consultas parametrizadas** (placeholders `%s`), nunca concatenación:
    ```python
    query("SELECT id, acct_no, fecha, total, detalle_items FROM ldg_fin_legacy"
          " WHERE doc_ref = %s AND acct_no = %s", (ref, g.user["client_id"]))
    ```
    (acotando además por el cliente de la sesión).
  - **No almacenar** CVV (prohibido por PCI-DSS); tokenizar o cifrar el PAN y
    mostrar solo los últimos 4 dígitos.

---

## Encadenamiento e impacto global

| Dimensión | Impacto |
|-----------|---------|
| Confidencialidad | Acceso a comprobantes, historial y **datos de tarjeta** de otros clientes. |
| Reconocimiento | Descubrimiento de endpoints legacy y de la estructura de la base. |
| Cumplimiento | Almacenamiento de datos de tarjeta en texto plano (incumple PCI-DSS). |
| Operacional / negocio | Inteligencia comercial (qué compra la víctima, a qué precio y con qué frecuencia). |

La lección central: vulnerabilidades de impacto *individual* limitado, al
**encadenarse**, habilitan un ataque de alcance crítico.
