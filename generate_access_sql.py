"""
English:
Generate SQL INSERTs for Asterisk access table from Zoho CSVs and locations JSON.

Russian:
Генератор SQL INSERT для таблицы access (Asterisk) на основе CSV из Zoho и locations.json.

Assign/Назначение:
  cid = client phone (Client phone/клиентский номер)
  did = gate phone (Gate phone/номер ворот)

Usage/Использование:
  ./generate_access_sql.py \
    -j locations.json \
    -c contacts_region1.csv contacts_region2.csv \
    -o restore_access_final.sql
"""

import json
import csv
import argparse
import sys
import logging


def normalize_phone(raw):
    return ''.join(filter(str.isdigit, raw or ''))


def load_locations(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON {json_path}: {e}")
        sys.exit(1)
    if 'locations' not in data or not isinstance(data['locations'], list):
        logging.error(f"JSON {json_path} has no 'locations' key or it's not a list!")
        sys.exit(1)
    phones = []
    for i, loc in enumerate(data['locations']):
        p = normalize_phone(loc.get('phone', ''))
        if not p:
            logging.warning(f"Location #{i+1}: no gate phone (phone)")
        phones.append(p if p else None)
    return phones


def process_csv(file_path, loc_phones, seen, sql_lines):
    required_fields = [
        'First Name', 'Last Name', 'Company Name', 'Display Name',
        'Phone', 'MobilePhone', 'CF.Noliktavas numurs', 'CF.Storage number'
    ]
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            missing = [field for field in required_fields if field not in reader.fieldnames]
            if missing:
                logging.warning(f"{file_path}: missing fields: {', '.join(missing)}")
            for row_num, row in enumerate(reader, 2):
                raw_idx = row.get('CF.Noliktavas numurs') or row.get('CF.Storage number') or ''
                try:
                    idx = int(float(raw_idx)) - 1
                except Exception:
                    logging.warning(f"{file_path}:{row_num}: invalid storage index '{raw_idx}'")
                    continue
                if idx < 0 or idx >= len(loc_phones):
                    logging.warning(f"{file_path}:{row_num}: index {idx+1} out of range")
                    continue
                gate_phone = loc_phones[idx]
                if not gate_phone:
                    gate_phone = normalize_phone(row.get('GatePhone') or row.get('Gate Phone') or '')
                if not gate_phone:
                    logging.warning(f"{file_path}:{row_num}: no gate phone")
                    continue
                client_phone = normalize_phone(row.get('Phone') or row.get('MobilePhone') or '')
                if not client_phone:
                    logging.warning(f"{file_path}:{row_num}: no client phone")
                    continue
                first = row.get('First Name', '').strip()
                last = row.get('Last Name', '').strip()
                comp = row.get('Company Name', '').strip()
                display = row.get('Display Name', '').strip()
                if first or last:
                    name = (first + ' ' + last).strip()
                elif comp:
                    name = comp
                elif display:
                    name = display
                else:
                    name = None
                client_sql = f"'{name}'" if name else 'NULL'
                key = (client_phone, gate_phone)
                if key in seen:
                    continue
                seen.add(key)
                sql_lines.append(
                    f"INSERT INTO access (cid, did, client) VALUES ('{client_phone}', '{gate_phone}', {client_sql});"
                )
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SQL INSERTs for Asterisk access table from CSVs and JSON."
    )
    parser.add_argument('-j', '--json', default='locations.json', help='Path to locations JSON')
    parser.add_argument('-c', '--csv', nargs='+', required=True, help='Paths to CSV files')
    parser.add_argument('-o', '--output', default='restore_access_final.sql', help='Output SQL file')
    parser.add_argument('--log', default='INFO', help='Log level: DEBUG, INFO, WARNING, ERROR')
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log.upper(), 'INFO'),
        format='[%(levelname)s] %(message)s'
    )

    loc_phones = load_locations(args.json)
    seen = set()
    sql_lines = []

    for csv_file in args.csv:
        process_csv(csv_file, loc_phones, seen, sql_lines)

    try:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write('\n'.join(sql_lines))
        logging.info(f"✅ Generated {len(sql_lines)} INSERTs in {args.output}")
    except Exception as e:
        logging.error(f"Error writing to {args.output}: {e}")


if __name__ == '__main__':
    main()
