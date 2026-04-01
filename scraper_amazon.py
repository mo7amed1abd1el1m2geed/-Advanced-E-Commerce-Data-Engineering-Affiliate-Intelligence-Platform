import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import logging
from datetime import datetime
from fake_useragent import UserAgent
import sys
import io

# إصلاح مشكلة اللغة العربية في الـ Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 1. CONFIGURATION ---
CONFIG = {
    "BASE_URL": "https://www.amazon.eg",
    "QUERIES": [
    "makeup", "skin care", "sunblock", "perfume", "hair care", 
    "moisturizer", "serum", "mascara", "shampoo", "foundation"
],
    "PAGES_PER_QUERY": 20,
    "DELAY_RANGE": (5, 8),
    "OUTPUT_FILE": f"beauty_market_data_{datetime.now().strftime('%Y%m%d')}.csv",
    "MIN_PRICE": 50.0 
}

BRANDS = [
    "L'Oreal", "Maybelline", "Vichy", "La Roche-Posay", "CeraVe", 
    "Garnier", "Nivea", "Neutrogena", "Eucerin", "Bioderma", 
    "The Ordinary", "Beesline", "Eva", "Amanda", "Sheglam", 
    "Luna", "Cybele", "Ciao", "Golden Rose", "Kiko", "NYX", 
    "Dior", "Chanel", "Essence", "Catrice", "Vichy"
]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class PulseBeautyScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.results = []

    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept-Language": "en-US,en;q=0.9,ar-EG;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive"
        }

    def detect_brand(self, title):
        for brand in BRANDS:
            if brand.lower() in title.lower():
                return brand
        return "Generic/Other"

    def clean_price(self, price_str):
        if not price_str: return 0.0
        try:
            clean_val = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
            return float(clean_val)
        except: return 0.0

    def parse_product(self, item, category):
        try:
            name_tag = item.select_one('h2 a span') or item.select_one('.a-size-base-plus')
            if not name_tag: return None
            title = name_tag.text.strip()

            price_tag = item.select_one('.a-price .a-offscreen') or item.select_one('.a-price-whole')
            price = self.clean_price(price_tag.text) if price_tag else 0.0

            if price < CONFIG["MIN_PRICE"]: return None

            rating_tag = item.select_one('i.a-icon-star-small span.a-icon-alt') or item.select_one('.a-icon-alt')
            rating = rating_tag.text.split()[0] if rating_tag else "0"

            return {
                "Category": category,
                "Brand": self.detect_brand(title),
                "Title": title,
                "Price_EGP": price,
                "Rating": float(rating) if rating != "0" else 0.0,
                "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except: return None

    def run(self):
        logging.info("🚀 Starting Pulse Beauty Engine...")
        
        for query in CONFIG["QUERIES"]:
            logging.info(f"🔎 Scraping Category: {query}")
            for page in range(1, CONFIG["PAGES_PER_QUERY"] + 1):
                url = f"{CONFIG['BASE_URL']}/s?k={query.replace(' ', '+')}&page={page}"
                try:
                    response = self.session.get(url, headers=self.get_headers(), timeout=20)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, "html.parser")
                        items = soup.select('div[data-component-type="s-search-result"], .s-result-item[data-asin]')
                        
                        count = 0
                        for item in items:
                            product = self.parse_product(item, query)
                            if product:
                                self.results.append(product)
                                count += 1
                        
                        logging.info(f"✅ Page {page}: Extracted {count} items.")
                        time.sleep(random.uniform(*CONFIG["DELAY_RANGE"]))
                    else:
                        logging.warning(f"⚠️ Page {page} failed with status {response.status_code}")
                except Exception as e:
                    logging.error(f"❌ Error: {e}")

        self.export_data()

    def export_data(self):
        if not self.results:
            logging.error("No data collected.")
            return
        df = pd.DataFrame(self.results).drop_duplicates(subset=['Title'])
        df.to_csv(CONFIG["OUTPUT_FILE"], index=False, encoding="utf-8-sig")
        logging.info(f"🎯 DONE! Saved {len(df)} Unique Beauty Products to {CONFIG['OUTPUT_FILE']}")

if __name__ == "__main__":
    scraper = PulseBeautyScraper()
    scraper.run()