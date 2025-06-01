@echo off
echo Запуск тестов в Docker контейнере...
echo.

REM Останавливаем и удаляем существующие контейнеры
docker-compose -f docker-compose.test.yml down -v

REM Собираем и запускаем тесты
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

REM Очищаем после завершения
docker-compose -f docker-compose.test.yml down -v

echo.
echo Тесты завершены!
pause 