# -*- coding: utf-8 -*-
"""
Project: Amazon Egypt Data Scraper
Author: Your Team
Description: سكربت متقدم لسحب بيانات منتجات أمازون مصر
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import logging
from datetime import datetime
from fake_useragent import UserAgent
from urllib.robotparser import RobotFileParser
import sys
import io

# --- إصلاح مشكلة الإيموجي في ويندوز ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- 1. CONFIGURATION ---
CONFIG = {
    "BASE_URL": "https://www.amazon.eg",
    "SEARCH_QUERY": "/s?k=laptop",  # عدل كلمة البحث هنا
    "PAGES_TO_SCRAPE": 3,
    "DELAY_RANGE": (10, 15),  # زدنا التأخير عشان أمازون ما يحظرش
    "OUTPUT_FILE": f"laptop_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    "RETRY_ATTEMPTS": 3,
    "PROXIES": {},
    "PROXY_LIST": []
}

# --- إعداد الـ Logging بدون إيموجي ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_log.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AmazonProScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.results = []

    def check_robots_txt(self, url):
        try:
            rp = RobotFileParser()
            rp.set_url(f"{CONFIG['BASE_URL']}/robots.txt")
            rp.read()
            return rp.can_fetch("*", url)
        except: 
            return True

    def detect_captcha(self, response_text):
        captcha_indicators = [
            'captcha', 'robot check', 'verify you are human',
            'challenge', 'cloudflare', 'turnstile', 'please verify'
        ]
        return any(ind in response_text.lower() for ind in captcha_indicators)

    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive"
        }

    def clean_price(self, price_str):
        if not price_str: 
            return 0.0
        try:
            clean_val = re.sub(r'[^\d.]', '', price_str)
            return float(clean_val)
        except (ValueError, TypeError):
            return 0.0

    def validate_product(self, product):
        # تخفيف شروط التحقق عشان نجمع بيانات أكثر
        if not product.get("Title"):
            return False
        if len(product.get("Title", "")) < 3:  # قللنا من 5 لـ 3
            return False
        if product.get("Price_EGP", 0) <= 0:
            return False
        if not (0 <= product.get("Rating", 0) <= 5):
            return False
        return True

    def parse_product(self, item):
        try:
            name_tag = item.h2
            if not name_tag: 
                return None

            price_whole = item.find("span", "a-price-whole")
            price_fraction = item.find("span", "a-price-fraction")
            
            raw_price = "0"
            if price_whole:
                raw_price = price_whole.text.strip()
                if price_fraction:
                    raw_price += f".{price_fraction.text.strip()}"

            rating_tag = item.find("span", "a-icon-alt")
            rating = rating_tag.text.split()[0] if rating_tag else "0"

            title = name_tag.text.strip()
            if len(title) < 3: 
                return None 

            return {
                "Title": title,
                "Price_EGP": self.clean_price(raw_price),
                "Rating": float(rating) if rating != "0" else 0.0,
                "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logging.warning(f"Failed to parse item: {e}")
            return None

    def get_proxy(self):
        if CONFIG["PROXY_LIST"]:
            return random.choice(CONFIG["PROXY_LIST"])
        return None

    def run(self):
        logging.info("Starting Pulse System: Data Ingestion Engine...")
        
        for page in range(1, CONFIG["PAGES_TO_SCRAPE"] + 1):
            url = f"{CONFIG['BASE_URL']}{CONFIG['SEARCH_QUERY']}&page={page}"
            
            if not self.check_robots_txt(url):
                logging.warning(f"Robots.txt disallows scraping page {page}")
                continue

            success = False
            for attempt in range(CONFIG["RETRY_ATTEMPTS"]):
                try:
                    proxy = self.get_proxy()
                    proxies = {
                        "http": proxy,
                        "https": proxy
                    } if proxy else {}

                    response = self.session.get(
                        url, 
                        headers=self.get_headers(), 
                        proxies=proxies,
                        timeout=20
                    )
                    
                    if self.detect_captcha(response.text):
                        logging.error(f"Captcha detected on page {page}! Proxy might be flagged.")
                        break 

                    if response.status_code == 200:
                        self.process_page(response.content)
                        success = True
                        break
                    else:
                        logging.warning(f"Attempt {attempt+1} failed: Status {response.status_code}")
                        
                except Exception as e:
                    logging.error(f"Network error on page {page}: {e}")
                
                time.sleep(10 * (attempt + 1)) 

            if not success: 
                logging.warning(f"Page {page} failed after {CONFIG['RETRY_ATTEMPTS']} attempts")
                continue

            wait_time = random.uniform(*CONFIG["DELAY_RANGE"])
            logging.info(f"Page {page} done. Sleeping for {wait_time:.2f}s...")
            time.sleep(wait_time)

        self.export_data()

    def process_page(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        items = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        # لو مش جاب حاجة، جرب selector تاني
        if not items:
            items = soup.find_all("div", class_="s-result-item")
        
        logging.info(f"Items Found: {len(items)}")
        
        page_data_count = 0
        for item in items:
            product = self.parse_product(item)
            if product and self.validate_product(product):
                self.results.append(product)
                page_data_count += 1
        
        logging.info(f"Extracted {page_data_count} valid products.")

    def export_data(self):
        if not self.results:
            logging.error("No data collected.")
            return
        df = pd.DataFrame(self.results)
        df.drop_duplicates(subset=['Title'], keep='first', inplace=True)
        df.to_csv(CONFIG["OUTPUT_FILE"], index=False, encoding="utf-8-sig")
        logging.info(f"DONE! Total Unique Records: {len(df)}")

if __name__ == "__main__":
    scraper = AmazonProScraper()
    scraper.run()