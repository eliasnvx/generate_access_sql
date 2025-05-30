# Asterisk Access Table SQL Generator

**Description:**
A Python utility to generate SQL INSERT statements for the Asterisk `access` table from Zoho-like CSV contact exports and a JSON file with storage locations (gate/container phone numbers). The script performs validation and logs warnings for skipped or malformed records.

---

## Quick Start

1. Prepare your data files:
   - `locations.json` — array of locations with gate phone numbers
   - `contacts_region1.csv`, `contacts_region2.csv` — client contact lists
2. Run the script:

```bash
python3 generate_access_sql.py -j locations.json -c contacts_region1.csv contacts_region2.csv -o restore_access_final.sql
```

## Arguments
- `-j`, `--json` — path to locations JSON file
- `-c`, `--csv` — list of CSV files with contacts
- `-o`, `--output` — output SQL file
- `--log` — log level (DEBUG, INFO, WARNING, ERROR)

## Example Data Formats

### locations.json
```json
{
    "locations": [
        {"phone": "+37128550090", "name": "Gate 1"},
        {"phone": "+37064671293", "name": "Gate 2"},
        {"phone": "+37061591061", "name": "Gate 3"}
    ]
}
```

### contacts_region1.csv (fragment)
```csv
First Name,Last Name,Company Name,Display Name,Phone,MobilePhone,CF.Storage number
Ivan,Ivanov,,Ivan Ivanov,123456789,,1
,,Acme Ltd,Acme Ltd,,987654321,2
,,,,Eduard Podgrušyj,,37061591061,3
```

## Logging & Validation
- The script logs warnings for skipped records and missing/incorrect fields.
- Validates the presence of required columns in input files.

## Requirements
- Python 3.x
- Uses only the Python standard library

---

# Генератор SQL для Asterisk access table

Скрипт `generate_access_sql.py` генерирует SQL INSERT-запросы для таблицы доступа Asterisk на основе CSV-файлов Zoho и JSON с локациями.

## Быстрый старт

1. Скопируйте или создайте файлы:
   - `locations.json` — список локаций с номерами ворот/контейнеров
   - `contacts_region1.csv`, `contacts_region2.csv` — контакты клиентов
2. Запустите скрипт:

```bash
python3 generate_access_sql.py -j locations.json -c contacts_region1.csv contacts_region2.csv -o restore_access_final.sql
```

## Аргументы
- `-j`, `--json` — путь к JSON-файлу с локациями
- `-c`, `--csv` — список CSV-файлов с контактами
- `-o`, `--output` — выходной SQL-файл
- `--log` — уровень логирования (DEBUG, INFO, WARNING, ERROR)

## Пример структуры данных

### locations.json
```json
{
    "locations": [
        {"phone": "+37128550090", "name": "Gate 1"},
        {"phone": "+37064671293", "name": "Gate 2"},
        {"phone": "+37061591061", "name": "Gate 3"}
    ]
}
```

### contacts_region1.csv (фрагмент)
```csv
First Name,Last Name,Company Name,Display Name,Phone,MobilePhone,CF.Storage number
Ivan,Ivanov,,Ivan Ivanov,123456789,,1
,,Acme Ltd,Acme Ltd,,987654321,2
,,,,Eduard Podgrušyj,,37061591061,3
```

## Логирование и валидация
- Скрипт пишет предупреждения о пропущенных строках и ошибках в консоль.
- Проверяется наличие нужных колонок в файлах.

## Требования
- Python 3.x
- Используется только стандартная библиотека