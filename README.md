# OrderFlow — Laboratorio de Seguridad Web (TP SAW · Grupo 3)

Maqueta local de una plataforma ficticia de **gestión de pedidos y logística**
(*OrderFlow*), construida como **laboratorio de seguridad** para la materia
*Seguridad en Aplicaciones Web*.

La aplicación contiene **vulnerabilidades sembradas a propósito** que permiten
demostrar, en vivo, una **cadena de explotación** completa: un usuario con
permisos básicos (un competidor malicioso) llega a **exfiltrar el historial
comercial y los datos de tarjeta de otro cliente**.

> ⚠️ **Uso educativo.** Esta aplicación es intencionalmente vulnerable. Está
> pensada para correr **solo en local** (`127.0.0.1`). No la expongas a Internet
> ni la uses como base para código real.

---

## Cadena de ataque (OWASP Top 10)

| Paso | Vulnerabilidad | Resultado |
|------|----------------|-----------|
| 1 | **A02 – Security Misconfiguration** | La documentación de la API (`/api/docs`) es accesible sin control → se descubren los endpoints *legacy* (`GET /api/v1/pedidos/{id}/comprobante`, `GET /api/v1/facturas/ver`). La doc revela *dónde* están, pero **no** entrega referencias usables. |
| 2 | **A01 – Broken Access Control / IDOR** | `GET /api/v1/pedidos/{id}/comprobante` no valida propiedad → se leen comprobantes ajenos. **Única** fuente del `cliente_id` de la víctima (`458`) y de una referencia válida (token opaco `FAC-2026-A7K9QD2F`). Habilita los Pasos 3 y 4. |
| 3 | **A10 – Mishandling of Exceptional Conditions** | `GET /api/v1/facturas/ver?ref=` (con la referencia del Paso 2) tiene un filtro de formato *bypassable*; al romper el SQL, el error 500 filtra la query y los nombres internos (tabla `ldg_fin_legacy`, columnas `acct_no`/`pay_raw`) necesarios para el Paso 4. |
| 4 | **A05 – Injection** + **A04 – Cryptographic Failures** | La misma ruta arma SQL por concatenación → `ref=FAC-2026-A7K9QD2F' OR acct_no=458--` (usa el `cliente_id` del Paso 2 y la columna del Paso 3) devuelve todo el historial de la víctima, con **tarjetas en texto plano** (objetivo final). |

El paso a paso para la demo está en [`Documentacion/WALKTHROUGH.md`](Documentacion/WALKTHROUGH.md)
(Windows) y [`Documentacion/WALKTHROUGH_LINUX_MINT.md`](Documentacion/WALKTHROUGH_LINUX_MINT.md)
(Linux Mint / macOS). El detalle técnico y las mitigaciones, en
[`Documentacion/VULNERABILIDADES.md`](Documentacion/VULNERABILIDADES.md).

---

## Stack

- **Python 3 + Flask** (API REST + vistas server-rendered con Jinja2)
- **PostgreSQL** (vía `psycopg2`)
- **flask-swagger-ui** (documentación interactiva de la API)
- Front liviano: HTML + CSS + JS *vanilla* (sin build, funciona offline)

---

## Requisitos

> Si usás **Docker** (Opción A, más abajo) no necesitás instalar Python ni
> PostgreSQL: alcanza con Docker + Docker Compose. Lo de abajo es para la
> instalación local (Opción B).

- **Python 3.10+** — si no lo tenés, instalalo desde
  [python.org/downloads](https://www.python.org/downloads/) (en Windows, marcá
  *"Add Python to PATH"* durante la instalación).
- **PostgreSQL 13+** corriendo en local:
  - Linux (Debian/Ubuntu/Mint): `sudo apt install postgresql`
  - Windows: instalador de [postgresql.org](https://www.postgresql.org/download/windows/)
    (asegurate de que `psql` quede en el PATH).

El setup crea automáticamente el rol `orderflow` y la base `orderflow_lab`
(credenciales de laboratorio, ver `app/config.py` / `db/create_db.sql`).

---

## Cómo ejecutar

### Opción A — Docker (recomendado para la demo)

Requiere **Docker** y **Docker Compose**. Levanta Flask + PostgreSQL ya
provisionados, sin instalar ni tocar el Postgres del sistema:

```bash
docker compose up --build        # http://127.0.0.1:5000
```

La base se crea y se siembra sola al arrancar. Para reiniciarla entre demos:

```bash
docker compose down && docker compose up        # base limpia (es efímera)
# o, sin bajar los contenedores:
docker compose exec web python scripts/reset_db.py
```

Los usuarios de prueba son los mismos de la tabla de abajo (`nico` / `clopez` / `admin`).

> La base del contenedor es **efímera** (sin volumen): cada `up` tras un `down`
> arranca desde cero, ideal para repetir la demo.

### Opción B — Instalación local (Postgres nativo)

#### Windows (PowerShell)

```powershell
.\setup.ps1     # provisiona la base, crea el venv, instala deps e inicializa datos
.\run.ps1       # inicia la app en http://127.0.0.1:5000
```

#### Linux / macOS

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

> El `setup` usa el superusuario `postgres` para crear el rol y la base
> (en Linux, vía `sudo -u postgres`). Si tu Postgres usa otra autenticación,
> podés correr la provisión a mano: `psql -U postgres -f db/create_db.sql`.

Luego abrí **http://127.0.0.1:5000** e ingresá con alguno de los usuarios de
prueba (ver abajo).

### Reiniciar la base entre demos

```bash
python scripts/reset_db.py
```

---

## Usuarios de prueba

| Usuario | Contraseña | Rol | Cliente (client_id) |
|---------|-----------|-----|---------------------|
| `nico` | `nico123` | user | Competidora Rápida SRL (89) — **atacante** |
| `clopez` | `cliente123` | user | Comercial Lopez e Hijos S.A. (458) — **víctima** |
| `admin` | `admin123` | admin | OrderFlow Operaciones (1) |

El **atacante** de la demo es `nico`. Detalle en
[`Documentacion/CREDENCIALES.md`](Documentacion/CREDENCIALES.md).

---

## Estructura del proyecto

```
app/            Aplicación Flask (factory, auth, db, rutas web y API)
  routes/api.py   <- concentra las vulnerabilidades (endpoints /api/v1/...)
  routes/web.py   <- la fachada de "app normal"
  templates/      <- vistas Jinja
  static/         <- CSS, JS y openapi.json
db/             schema.sql, seed.sql y create_db.sql (provisión del rol/base)
scripts/        reset_db.py (recrea y re-seedea la base)
Documentacion/  Propuesta, walkthroughs de la demo y análisis de vulnerabilidades
```
