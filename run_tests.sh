#!/bin/bash

echo "Запуск тестов в Docker контейнере..."
echo

# Останавливаем и удаляем существующие контейнеры
docker-compose -f docker-compose.test.yml down -v

# Собираем и запускаем тесты
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Очищаем после завершения
docker-compose -f docker-compose.test.yml down -v

echo
echo "Тесты завершены!" 