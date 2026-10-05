# Imagen de la app del laboratorio OrderFlow (Flask).
# La base PostgreSQL corre en un servicio aparte (ver docker-compose.yml).
FROM python:3.12-slim

WORKDIR /app

# Dependencias primero (mejor cacheo de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación.
COPY . .

# FLASK_APP para `flask run`; LAB_DEBUG=1 mantiene errores verbosos (A02/A10).
# No se setea FLASK_DEBUG a propósito: así no se activa el reloader y create_app()
# (que hace el auto-init del esquema) corre una sola vez.
ENV FLASK_APP=app \
    LAB_DEBUG=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# 0.0.0.0 para que el port-mapping del contenedor llegue desde el host.
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
