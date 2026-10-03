# Análisis de vulnerabilidades y mitigaciones

Detalle técnico de cada vulnerabilidad sembrada, su ubicación en el código, el
impacto y cómo se corregiría. Material para el informe.

---

## Paso 1 — A02:2021 Security Misconfiguration

- **Dónde:** `app/__init__.py` (registro de Swagger UI en `/api/docs` sin
  autenticación) y `app/config.py` (`DEBUG = True`).
- **Causa:** la documentación de la API y los errores detallados quedan
  disponibles para cualquiera, exponiendo endpoints, parámetros y estructura.
- **Impacto:** reconocimiento. El atacante obtiene el mapa completo de la API,
  incluidos los endpoints de administración.
- **Mitigación:**
  - No publicar Swagger/OpenAPI en entornos accesibles por usuarios finales, o
    protegerlo tras autenticación/rol de administrador.
  - `DEBUG = False` en cualquier entorno no local; manejar errores con páginas
    genéricas.
  - Separar documentación interna de la expuesta.

---

## Paso 2 — A01:2021 Broken Access Control (IDOR)

- **Dónde:** `app/routes/api.py` → `get_order()` (`GET /api/orders/<id>`).
- **Causa:** se verifica *autenticación* pero no *autorización*: no se comprueba
  que `order.client_id` coincida con el `client_id` del usuario de la sesión.
- **Impacto:** acceso a pedidos, renglones, envíos y facturas de otros clientes
  (pérdida de confidencialidad) y obtención de identificadores reutilizables.
- **Mitigación:** validar propiedad del recurso en el servidor. Ejemplo:
  ```python
  if order["client_id"] != g.user["client_id"] and g.user["role"] != "admin":
      return jsonify({"error": "No autorizado"}), 403
  ```
  Aplicar el mismo control a los sub-recursos (`/items`, envío, factura).

---

## Paso 3 — A05 Injection + A10 Mishandling of Exceptional Conditions

- **Dónde:** `app/routes/api.py` → `search_products()`
  (`GET /api/products/search`).
- **Causa (A05):** la consulta se arma por **concatenación de strings** con el
  parámetro `q`, permitiendo inyección SQL (bypass booleano, `UNION`, lectura de
  otras tablas como `users` y `sqlite_master`).
- **Causa (A10):** ante una excepción se devuelve el **mensaje de error y la
  query completa**, filtrando la estructura interna.
- **Impacto:** lectura de datos sensibles (usuarios, hashes, roles), mapeo del
  esquema y descubrimiento de funcionalidades a atacar.
- **Mitigación:**
  - Usar **consultas parametrizadas** (placeholders `?`), nunca concatenación:
    ```python
    like = f"%{q}%"
    db.execute(
        "SELECT id, name, sku, price, stock FROM products "
        "WHERE name LIKE ? OR sku LIKE ?", (like, like))
    ```
  - Manejar las excepciones y responder con un error **genérico** (loggear el
    detalle solo del lado del servidor).

---

## Paso 4 — A01:2021 Broken Function Level Authorization

- **Dónde:** `app/routes/api.py` → `admin_update_order()`
  (`POST /api/admin/orders/<id>`), decorado con `login_required` en vez de
  `admin_required`.
- **Causa:** una función de administración no valida el **rol** del usuario; con
  solo estar autenticado se puede invocar.
- **Impacto:** **modificación no autorizada** de pedidos de cualquier cliente
  (pérdida de integridad y de control de acceso). Es el objetivo final.
- **Mitigación:**
  - Exigir rol en todos los endpoints de administración (usar el decorador
    `admin_required`, que ya existe en `app/auth.py`).
  - Control de acceso centralizado y "deny by default"; además, validar
    propiedad cuando corresponda.

---

## Encadenamiento e impacto global

| Dimensión | Impacto |
|-----------|---------|
| Confidencialidad | Acceso a pedidos, clientes, usuarios y hashes. |
| Integridad | Modificación no autorizada de pedidos ajenos. |
| Control de acceso | Ejecución de funciones destinadas a administradores. |
| Operacional | Alteración de información de gestión comercial y logística. |

La lección central: vulnerabilidades de impacto *individual* limitado, al
**encadenarse**, habilitan un ataque de alcance crítico.
