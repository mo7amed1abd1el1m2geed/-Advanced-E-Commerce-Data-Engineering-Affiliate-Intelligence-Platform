import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

# Keywords that must exist in a smartphone product name
SMARTPHONE_KEYWORDS = [
    "phone", "smartphone", "mobile", "galaxy", "iphone",
    "pixel", "motorola", "oneplus", "xiaomi", "realme",
    "nokia", "sony", "lg", "htc", "huawei", "redmi",
    "moto", "blu", "tcl", "unlocked", "android", "5g"
]

# Keywords that must NOT exist in a smartphone product name
EXCLUDED_KEYWORDS = [
    "screen protector", "case", "cover", "charger",
    "cable", "adapter", "glass", "film", "tempered",
    "holder", "mount", "stand", "strap", "band",
    "gimbal", "stabilizer", "printer", "telescope",
    "sprinkler", "irrigation", "speakerphone", "scanner",
    "headphone", "earbud", "sonar", "breathalyzer"
]

def start_scraping(target_url, max_pages=3):
    """
    Scraping function: takes URL and number of pages to scrape.
    """
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US, en;q=0.5"
    }

    all_products = []

    for page in range(1, max_pages + 1):
        print(f"\n[!] Scraping page {page} of {max_pages}...")
        
        page_url = f"{target_url}&page={page}"
        
        try:
            response = requests.get(page_url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Error: Connection failed. Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            products_list = []

            items = soup.find_all("div", {"data-component-type": "s-search-result"})

            for item in items:
                # 1. Get product name
                name_tag = item.h2
                name = name_tag.text.strip() if name_tag else "N/A"
                name_lower = name.lower()

                # Filter: must be a smartphone
                is_smartphone = any(keyword in name_lower for keyword in SMARTPHONE_KEYWORDS)
                if not is_smartphone:
                    continue

                # Filter: must NOT be an accessory
                is_accessory = any(keyword in name_lower for keyword in EXCLUDED_KEYWORDS)
                if is_accessory:
                    continue

                # 2. Get price
                price_tag = item.find("span", "a-price-whole")
                price = price_tag.text.strip().replace(",", "").replace(".", "") if price_tag else "0"
                
                # 3. Get rating
                rating_tag = item.find("span", "a-icon-alt")
                rating = rating_tag.text.split()[0] if rating_tag else "0"

                products_list.append({
                    "Category": "smartphones",
                    "Product_Name": name,
                    "Price_EGP": price,
                    "Rating": rating,
                    "Source": "Amazon Egypt"
                })

            all_products.extend(products_list)
            print(f"✅ Page {page}: Found {len(products_list)} products.")

        except Exception as e:
            print(f"❌ Unexpected error on page {page}: {e}")
            break

        time.sleep(1)

    if all_products:
        df = pd.DataFrame(all_products)
        df = df[df["Price_EGP"].astype(int) > 0]       # شيل Price = 0
        df = df.drop_duplicates()               # شيل المكرر
        df.to_csv("raw_data_smartphones.csv", index=False, encoding="utf-8-sig")
        print(f"\n✅ Success! Scraped {len(df)} products total and saved to: raw_data_smartphones.csv")
    else:
        print("⚠️ Warning: No products found. Check the URL or update the CSS classes.")

# Main entry point
if __name__ == "__main__":
    print("========================================")
    print("   Pulse System - Data Ingestion Tool   ")
    print("========================================\n")
    
    print("Instructions:")
    print("1. Search for the category you want on Amazon.")
    print("2. Copy the URL from the browser.")
    print("3. Paste it here when prompted.\n")
    
    input_category = input("Enter category name (e.g. Laptops): ").strip()
    input_url = input("Enter search URL: ").strip()
    max_pages = int(input("Enter number of pages to scrape (e.g. 3): ").strip())
    
    if input_category and input_url:
        start_scraping(input_url, max_pages)
    else:
        print("❌ Error: Category name and URL are required.")