# OrderFlow — Laboratorio de Seguridad Web (TP SAW · Grupo 3)

Maqueta local de una plataforma ficticia de **gestión de pedidos y logística**
(*OrderFlow*), construida como **laboratorio de seguridad** para la materia
*Seguridad en Aplicaciones Web*.

La aplicación contiene **vulnerabilidades sembradas a propósito** que permiten
demostrar, en vivo, una **cadena de explotación** completa: un usuario con
permisos básicos escala su acceso hasta **modificar pedidos de otros clientes**.

> ⚠️ **Uso educativo.** Esta aplicación es intencionalmente vulnerable. Está
> pensada para correr **solo en local** (`127.0.0.1`). No la expongas a Internet
> ni la uses como base para código real.

---

## Cadena de ataque (OWASP Top 10)

| Paso | Vulnerabilidad | Resultado |
|------|----------------|-----------|
| 1 | **A02 – Security Misconfiguration** | La documentación de la API (`/api/docs`) es accesible sin control → mapa de endpoints. |
| 2 | **A01 – Broken Access Control / IDOR** | `GET /api/orders/{id}` no valida propiedad → datos de otros clientes. |
| 3 | **A05 – Injection** + **A10 – Mishandling of Exceptional Conditions** | `GET /api/products/search` arma SQL por concatenación y filtra errores → estructura interna. |
| 4 | **A01 – Broken Function Level Authorization** | `POST /api/admin/orders/{id}` no valida rol → modificación de pedidos ajenos (objetivo final). |

El paso a paso para la demo está en [`Documentacion/WALKTHROUGH.md`](Documentacion/WALKTHROUGH.md).
El detalle técnico y las mitigaciones, en [`Documentacion/VULNERABILIDADES.md`](Documentacion/VULNERABILIDADES.md).

---

## Stack

- **Python 3 + Flask** (API REST + vistas server-rendered con Jinja2)
- **SQLite** (base por archivo, sin servidor)
- **flask-swagger-ui** (documentación interactiva de la API)
- Front liviano: HTML + CSS + JS *vanilla* (sin build, funciona offline)

---

## Requisitos

- **Python 3.10+** — si no lo tenés, instalalo desde
  [python.org/downloads](https://www.python.org/downloads/) (en Windows, marcá
  *"Add Python to PATH"* durante la instalación).

No hace falta nada más: SQLite viene con Python y las dependencias se instalan
en un entorno virtual local.

---

## Cómo ejecutar

### Windows (PowerShell)

```powershell
.\setup.ps1     # crea el entorno virtual, instala deps e inicializa la base
.\run.ps1       # inicia la app en http://127.0.0.1:5000
```

### Linux / macOS

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Luego abrí **http://127.0.0.1:5000** e ingresá con alguno de los usuarios de
prueba (ver abajo).

### Reiniciar la base entre demos

```bash
python scripts/reset_db.py
```

---

## Usuarios de prueba

| Usuario | Contraseña | Rol | Cliente |
|---------|-----------|-----|---------|
| `cliente1` | `cliente123` | user | Distribuidora Andina S.A. |
| `cliente2` | `cliente123` | user | Comercial del Plata SRL |
| `cliente3` | `cliente123` | user | Importadora Sur SA |
| `admin` | `admin123` | admin | OrderFlow Operaciones |

El **atacante** de la demo es `cliente1`. Detalle en
[`Documentacion/CREDENCIALES.md`](Documentacion/CREDENCIALES.md).

---

## Estructura del proyecto

```
app/            Aplicación Flask (factory, auth, db, rutas web y API)
  routes/api.py   <- concentra las 4 vulnerabilidades
  routes/web.py   <- la fachada de "app normal"
  templates/      <- vistas Jinja
  static/         <- CSS, JS y openapi.json
db/             Esquema (schema.sql) y datos de ejemplo (seed.sql)
scripts/        reset_db.py (recrea y re-seedea la base)
data/           Base SQLite generada (lab.sqlite, ignorada por git)
Documentacion/  Propuesta, walkthrough de la demo y análisis de vulnerabilidades
```
