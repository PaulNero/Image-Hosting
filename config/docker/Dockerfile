FROM python:3.11-alpine as builder

WORKDIR /app

# Установка зависимостей для сборки
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libmagic \
    postgresql-dev

COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app

# Установка runtime зависимостей
RUN apk add --no-cache \
    libmagic \
    wget \
    postgresql-libs

# Копирование установленных пакетов из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Копирование файлов приложения
COPY app/ /app/app/
COPY config/ /app/config/
COPY requirements.txt /app/

# Создание непривилегированного пользователя
RUN adduser -D appuser

# Создание необходимых директорий и настройка прав
RUN mkdir -p /app/images /app/logs /app/static && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/ || exit 1

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.app"]