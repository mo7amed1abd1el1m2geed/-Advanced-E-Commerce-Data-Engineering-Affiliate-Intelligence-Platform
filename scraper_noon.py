# -*- coding: utf-8 -*-
import requests
import pandas as pd
from datetime import datetime
import time
import random

class NoonFinalBoss:
    def __init__(self):
        self.results = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "x-platform": "web",
            "x-mp": "noon",
            "x-cms": "v2",
            "Content-Type": "application/json"
        }

    def scrape_category(self, query, pages=5):
        print(f"🚀 [API MODE] Hunting: {query}")
        
        for page in range(1, pages + 1):
            # ده الرابط السري اللي نون بيجيب منه الداتا بصيغة JSON
            api_url = f"https://www.noon.com/_svc/catalog/api/v3/search/?q={query.replace(' ', '%20')}&page={page}&limit=50&lang=en"
            
            try:
                response = requests.get(api_url, headers=self.headers, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('hits', [])
                    
                    for prod in products:
                        self.results.append({
                            "Source": "Noon_API_Pro",
                            "Brand": prod.get('brand', 'Generic'),
                            "Title": prod.get('name', ''),
                            "Price_EGP": prod.get('price', 0),
                            "Sale_Price": prod.get('sale_price', 0),
                            "Rating": prod.get('rating', {}).get('value', 0),
                            "Category": query,
                            "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    
                    print(f"✅ Page {page}: Extracted {len(products)} products.")
                    time.sleep(random.uniform(2, 4))
                else:
                    print(f"⚠️ Failed to reach API. Status: {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")

    def save(self, filename):
        df = pd.DataFrame(self.results).drop_duplicates(subset=['Title'])
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"🎯 SUCCESS! Total unique items: {len(df)}")

if __name__ == "__main__":
    scraper = NoonFinalBoss()
    # جرب كلمة واحدة دلوقتي للتأكد
    scraper.scrape_category("laptop", pages=3)
    scraper.save("noon_laptops_api_final.csv")