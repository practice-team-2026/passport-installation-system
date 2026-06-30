# 📋 Паспорт установки

Веб-приложение для учёта смонтированных объектов, паспортов установок и планирования технического обслуживания.

## Команда
- **Аналитик:** Бохиржон
- **Backend Developer:** Ким
- **Frontend Developer:** Анна

## Стек
- Python 3.11 + Flask
- SQLite (dev) / PostgreSQL (prod)
- SQLAlchemy + Alembic
- HTML + CSS + JavaScript (Chart.js)

## Структура
├── app/
│ ├── models/ # Модели БД
│ ├── routes/ # API-эндпоинты
│ ├── services/ # Бизнес-логика
│ ├── templates/ # HTML-шаблоны
│ └── static/ # CSS / JS
├── data/ # Тестовые данные
├── tests/ # Тесты
├── config.py # Настройки
├── run.py # Точка входа
└── requirements.txt # Зависимости

## Запуск
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```
