# OrderFlow — Laboratorio de Seguridad Web (TP SAW · Grupo 3)

Maqueta de una plataforma ficticia de gestión de pedidos, construida como
laboratorio para *Seguridad en Aplicaciones Web*. Contiene vulnerabilidades
sembradas a propósito que permiten demostrar una cadena de explotación completa.

> ⚠️ **Uso educativo.** Aplicación intencionalmente vulnerable: correla solo en
> local (`127.0.0.1`) y no la expongas a Internet.

## Cadena de ataque (OWASP Top 10)

| Paso | Vulnerabilidad | Resultado |
|------|----------------|-----------|
| 1 | A02 – Security Misconfiguration | `/api/docs` expuesto revela un endpoint *legacy*. |
| 2 | A01 – Broken Access Control (IDOR) | Se leen comprobantes de otros clientes. |
| 3 | A10 – Mishandling of Exceptional Conditions | Un error 500 filtra la query y la estructura de la base. |
| 4 | A05 – Injection + A04 – Cryptographic Failures | SQLi expone el historial de la víctima con tarjetas en texto plano. |

## Cómo ejecutar

**Docker (recomendado):**

```bash
docker compose up --build                            # http://127.0.0.1:5000
docker compose exec web python scripts/reset_db.py   # reiniciar la base
```

**Local** (requiere Python 3.10+ y PostgreSQL 13+):

- Windows: `.\setup.ps1` y luego `.\run.ps1`
- Linux / macOS: `./setup.sh` y luego `./run.sh`

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `nico` | `nico123` | atacante |
| `clopez` | `cliente123` | víctima |
| `admin` | `admin123` | admin |

Detalle en [`Documentacion/CREDENCIALES.md`](Documentacion/CREDENCIALES.md).

## Estructura

```
app/            Aplicación Flask (rutas web y API, templates, estáticos)
db/             Schema, seed y provisión de la base
scripts/        reset_db.py
Documentacion/  Propuesta del TP y credenciales
```

**Stack:** Python 3 + Flask, PostgreSQL, flask-swagger-ui, HTML/CSS/JS vanilla.
