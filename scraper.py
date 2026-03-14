import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
import os
import logging

# إعدادات اللوج
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

TRUSTED_BRANDS = [
    "samsung", "apple", "iphone", "google", "pixel",
    "motorola", "moto", "oneplus", "xiaomi", "redmi",
    "realme", "nokia", "sony", "huawei", "nothing",
    "blu", "tcl", "blackview", "ulefone", "oukitel",
    "doogee", "unihertz", "fossibot", "cubot", "zte",
    "oppo", "vivo", "umidigi", "hmd", "lively",
    "8849", "cat phone", "nuu", "tracfone", "htc"
]

EXCLUDED_KEYWORDS = [
    "screen protector", "case", "cover", "charger",
    "cable", "adapter", "glass", "tempered",
    "tripod", "gimbal", "stabilizer", "holder",
    "mount", "flash drive", "usb drive", "watch",
    "smartwatch", "printer", "scale", "tablet",
    "telescope", "breathalyzer", "microphone",
    "lanyard", "wallet", "strap", "book", "guide",
    "lens protector", "camera lens", "car mount",
    "phone case", "bumper", "pouch", "speakerphone",
    "prompter", "ssd", "scuba", "housing"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def fetch_page(session, url):
    for attempt in range(3):
        try:
            response = session.get(url, headers=get_headers(), timeout=30)
            if response.status_code == 200:
                return response
            logging.warning(f"Attempt {attempt+1} failed: {response.status_code}")
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            logging.error(f"Attempt {attempt+1} error: {e}")
            time.sleep(random.uniform(5, 10))
    return None

def start_scraping(category_name, source_name, url, pages):
    session = requests.Session()
    dataset = []

    for page in range(1, pages + 1):
        logging.info(f"Scraping {source_name} - Page {page}")

        if source_name == "amazon":
            page_url = f"{url}&page={page}"
        else:
            page_url = f"{url}&p={page}" if "?" in url else f"{url}?p={page}"

        response = fetch_page(session, page_url)

        if not response:
            logging.warning(f"Skipping page {page} after 3 failed attempts.")
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        if source_name == "amazon":
            items = soup.find_all("div", {"data-component-type": "s-search-result"})
        elif source_name == "noon":
            items = soup.find_all("div", {"class": "productContainer"}) or soup.find_all("a", href=True)
        else:
            items = []

        for item in items:
            try:
                if source_name == "amazon":
                    name = item.h2.text.strip() if item.h2 else ""
                    price = item.find("span", "a-price-whole").text.replace(",", "") if item.find("span", "a-price-whole") else "0"
                    rating_tag = item.find("span", "a-icon-alt")
                    rating = rating_tag.text.split()[0] if rating_tag else "0"

                elif source_name == "noon":
                    name_tag = item.find("div", {"data-qa": "product-name"}) or item.find("div", {"class": "name"})
                    price_tag = item.find("strong", {"class": "amount"}) or item.find("span", {"class": "priceNow"})
                    rating_tag = item.find("div", {"class": "stars"}) or item.find("span", {"class": "rating"})
                    if not name_tag:
                        continue
                    name = name_tag.text.strip()
                    price = price_tag.text.strip().replace("EGP", "").replace(",", "") if price_tag else "0"
                    rating = rating_tag.text.strip() if rating_tag else "0"

                name_lower = name.lower()

                if not any(brand in name_lower for brand in TRUSTED_BRANDS):
                    continue

                if any(keyword in name_lower for keyword in EXCLUDED_KEYWORDS):
                    continue

                dataset.append({
                    "Category": category_name,
                    "Product_Name": name,
                    "Price": price,
                    "Rating": rating,
                    "Source": source_name,
                    "Scraped_At": time.strftime("%Y-%m-%d %H:%M:%S")
                })

            except:
                continue

        logging.info(f"Page {page} processed. Found {len(dataset)} items so far.")
        time.sleep(random.uniform(7, 12))

    if dataset:
        df = pd.DataFrame(dataset)
        filename = f"raw_{source_name}_{category_name}.csv"
        df.to_csv(filename, mode="a", index=False, header=not os.path.exists(filename), encoding="utf-8-sig")
        logging.info(f"Saved {len(df)} records to {filename}")
    else:
        logging.warning("No data collected. Site might be blocking Python requests.")

if __name__ == "__main__":
    print("\n=== PULSE DATA ENGINE ===\n")
    source = input("Source (amazon/noon): ").lower().strip()
    cat = input("Category: ").lower().strip()
    search_url = input("URL: ").strip()
    p_count = int(input("Pages: "))
    start_scraping(cat, source, search_url, p_count)