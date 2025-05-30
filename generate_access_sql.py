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
    
    locations = {}
    
    for i, loc in enumerate(data['locations']):
        phone = normalize_phone(loc.get('phone', ''))
        if not phone:
            logging.warning(f"Location #{i+1}: no gate phone (phone)")
        
        name = loc.get('name', '').strip()
        if not name:
            logging.warning(f"Location #{i+1}: no name")
            continue
            
        address = None
        if '(' in name and ')' in name:
            address = name[name.find('(')+1:name.find(')')].strip()
        
        if address:
            address_key = address.lower().replace('  ', ' ')
            locations[address_key] = phone
            
            short_address = address_key.split(',')[0].strip()
            if short_address != address_key:
                locations[short_address] = phone

        locations[name.lower()] = phone
        locations[str(i+1)] = phone
    
    logging.info(f"Loaded {len(locations)} location addresses from {json_path}")
    return locations


def process_csv(file_path, locations, seen, sql_lines):
    required_fields = [
        'First Name', 'Last Name', 'Company Name', 'Display Name',
        'Phone', 'MobilePhone'
    ]
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            missing = [field for field in required_fields if field not in reader.fieldnames]
            if missing:
                logging.warning(f"{file_path}: missing fields: {', '.join(missing)}")
            
            for row_num, row in enumerate(reader, 2):
                client_phone = normalize_phone(row.get('Phone') or row.get('MobilePhone') or '')
                if not client_phone:
                    logging.warning(f"{file_path}:{row_num}: no client phone")
                    continue
                
                storage_location = (row.get('CF.Storage location') or row.get('CF.Noliktavas lokācija') or '').strip()
                if not storage_location:
                    logging.warning(f"{file_path}:{row_num}: no storage location")
                    continue
                
                storage_location_key = storage_location.lower().replace('  ', ' ')
                
                gate_phone = None
                
                if storage_location_key in locations:
                    gate_phone = locations[storage_location_key]
                else:
                    short_location = storage_location_key.split(',')[0].strip()
                    if short_location in locations:
                        gate_phone = locations[short_location]
                    else:
                        storage_number = row.get('CF.Noliktavas numurs') or row.get('CF.Storage number') or ''
                        if storage_number and storage_number in locations:
                            gate_phone = locations[storage_number]

                if not gate_phone:
                    gate_phone = normalize_phone(row.get('GatePhone') or row.get('Gate Phone') or 
                                               row.get('CF.Gate number') or row.get('CF.Gate phone 1') or '')
                
                if not gate_phone:
                    logging.warning(f"{file_path}:{row_num}: no gate phone for location '{storage_location}'")
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
    parser.add_argument('--verbose', action='store_true', help='Show detailed matching information')
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log.upper(), 'INFO'),
        format='[%(levelname)s] %(message)s'
    )

    locations = load_locations(args.json)
    seen = set()
    sql_lines = []

    for csv_file in args.csv:
        process_csv(csv_file, locations, seen, sql_lines)

    try:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write('\n'.join(sql_lines))
        logging.info(f"✅ Generated {len(sql_lines)} INSERTs in {args.output}")
    except Exception as e:
        logging.error(f"Error writing to {args.output}: {e}")


if __name__ == '__main__':
    main()