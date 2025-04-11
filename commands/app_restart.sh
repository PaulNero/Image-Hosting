#!/bin/bash

# Остановка и перезапуск Docker-контейнеров
docker compose -f config/docker/docker-compose.yml down && docker compose -f config/docker/docker-compose.yml up --build 