# Dockerfile

# 1. Base Image (Slim for optimization)
FROM python:3.12-slim

# 2. Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=aim_fin.settings.prod

# 3. Work Directory
WORKDIR /app

# 4. Install System Dependencies (for mysqlclient)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 5. Create Non-root User
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 6. Install Python Dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy Project Code (ownership to appuser)
COPY --chown=appuser:appgroup . /app/

# 8. Copy Entrypoint Script
COPY --chown=appuser:appgroup entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 9. Prepare Static/Media Directories (Permissions)
RUN mkdir -p /app/static /app/media && \
    chown -R appuser:appgroup /app/static /app/media

# 9. Switch to Non-root User
USER appuser

# 10. Expose Port (Gunicorn default)
EXPOSE 8000

# 11. Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
