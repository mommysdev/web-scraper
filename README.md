# 🕷️ Universal Web Scraper

Универсальный парсер сайтов на Python. Поддерживает статические и динамические
(JavaScript) страницы. Экспорт в CSV, JSON, Excel.

## Возможности
- 🌐 Парсинг статических сайтов (requests + BeautifulSoup)
- 🎭 Парсинг динамических сайтов (Playwright)
- 📋 Гибкая конфигурация через YAML
- 📊 Экспорт: CSV, JSON, XLSX
- 🔄 Пагинация (автоматический обход страниц)
- ⏱️ Rate limiting (защита от блокировки)
- 🔁 Retry с exponential backoff
- 📝 Подробное логирование

## Быстрый старт

```bash
pip install -r requirements.txt

# Парсинг по конфигу
python scraper.py --config configs/example.yml --output results.csv

# Быстрый парсинг одной страницы
python scraper.py --url "https://example.com/catalog" --selector ".product-card" --output products.json
```

## Конфигурация (YAML)
```yaml
name: "Парсинг каталога товаров"
base_url: "https://example.com/catalog"
engine: static  # static или playwright

selectors:
  container: ".product-list .product-card"
  fields:
    title: "h3.product-title"
    price: ".price-value"
    url:
      selector: "a.product-link"
      attribute: "href"
    image:
      selector: "img.product-image"
      attribute: "src"

pagination:
  type: next_button  # next_button, page_number, scroll
  selector: "a.next-page"
  max_pages: 10

settings:
  delay: 1.5          # секунд между запросами
  timeout: 30
  user_agent: "Mozilla/5.0 ..."
  retry_count: 3

output:
  format: csv         # csv, json, xlsx
  filename: "products.csv"
```

## Структура
```
├── scraper.py          # Точка входа (CLI)
├── core/
│   ├── __init__.py
│   ├── static.py       # Парсер статических страниц
│   ├── dynamic.py      # Парсер через Playwright
│   ├── config.py       # Загрузка конфигурации
│   └── exporters.py    # Экспорт данных
├── configs/
│   └── example.yml     # Пример конфигурации
├── requirements.txt
└── README.md
```

## Кастомизация для клиентов
- Настройка под конкретный сайт (селекторы, пагинация)
- Обход защиты (прокси, ротация User-Agent)
- Регулярный запуск (cron / планировщик)
- Интеграция с Google Sheets / базой данных
- Уведомления об изменениях (Telegram, email)
