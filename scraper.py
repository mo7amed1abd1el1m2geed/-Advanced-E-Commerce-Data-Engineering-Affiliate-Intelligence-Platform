import requests
from bs4 import BeautifulSoup
import random
import time
import pandas as pd

# 1. User-Agent rotation to prevent getting blocked by Amazon
# قائمة متغيرة لتعريف المتصفح عشان أمازون ما يكتشفش إنه بوت
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# 2. Quality Control Configuration
# الكلمات اللي لازم تكون موجودة لضمان إن المنتج موبايل فعلاً
REQUIRED_KEYWORDS = ["phone", "smartphone", "mobile", "galaxy", "iphone", "pixel", "nokia", "motorola", "realme", "xiaomi"]
# الكلمات المستبعدة (الإكسسوارات والموديلات الوهمية أو التقليد)
BLOCKED_KEYWORDS = ["case", "cover", "charger", "cable", "adapter", "glass", "screen protector", "s26", "s27", "c24", "fake", "dummy"]

def run_advanced_scraper(category_name, search_url, num_pages=3):
    """
    Scrapes Amazon products with strict data validation.
    وظيفة السحب مع التحقق الصارم من جودة البيانات
    """
    final_dataset = []
    
    for current_page in range(1, num_pages + 1):
        print(f"--- Scraping Page {current_page} of {num_pages} ---")
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        # Adjusting the URL for pagination
        # تعديل الرابط للانتقال بين الصفحات
        paginated_url = f"{search_url}&page={current_page}"
        
        try:
            response = requests.get(paginated_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[Warning] Failed to access page {current_page}. Status Code: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            # Searching for the specific Amazon product containers
            # البحث عن الحاويات الخاصة بمنتجات أمازون
            items = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            valid_counts = 0
            for item in items:
                # Extract Product Name
                name_element = item.h2
                if not name_element: continue
                
                full_name = name_element.text.strip()
                name_lower = full_name.lower()
                
                # --- DATA VALIDATION LOGIC ---
                # 1. Block accessories and fake models
                # استبعاد الإكسسوارات والموديلات غير المنطقية
                if any(blocked in name_lower for blocked in BLOCKED_KEYWORDS):
                    continue
                
                # 2. Ensure it is actually a smartphone
                # التأكد إن المنتج موبايل مش حاجة تانية
                if not any(req in name_lower for req in REQUIRED_KEYWORDS):
                    continue
                
                # Extract Price (Numerical value only)
                price_element = item.find("span", "a-price-whole")
                raw_price = price_element.text.replace(",", "").strip() if price_element else "0"
                
                # Extract Rating
                rating_element = item.find("span", "a-icon-alt")
                # Format: "4.5 out of 5 stars" -> we take "4.5"
                raw_rating = rating_element.text.split()[0] if rating_element else "0"

                # Save only if price exists (Discard out-of-stock or invalid data)
                # حفظ البيانات فقط لو السعر موجود عشان نتجنب الداتا الناقصة
                if raw_price != "0":
                    final_dataset.append({
                        "Category": category_name,
                        "Product_Name": full_name,
                        "Price_EGP": int(raw_price),
                        "Rating": float(raw_rating),
                        "Source": "Amazon Egypt",
                        "Timestamp": time.strftime("%Y-%m-%d %H:%M")
                    })
                    valid_counts += 1
            
            print(f"[Success] Found {valid_counts} valid smartphones on page {current_page}.")
            
            # Anti-Ban delay: simulates human browsing behavior
            # تأخير زمني عشوائي لمنع الحظر
            wait_time = random.uniform(2, 5)
            time.sleep(wait_time)
            
        except Exception as error:
            print(f"[Error] An anomaly occurred on page {current_page}: {error}")

    # Exporting results to CSV using Pandas
    # تصدير البيانات النهائية لملف اكسل
    if final_dataset:
        df = pd.DataFrame(final_dataset)
        filename = f"raw_data_{category_name.lower()}_{int(time.time())}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print("\n" + "="*40)
        print(f"PROCESS COMPLETED!")
        print(f"Total Clean Records: {len(df)}")
        print(f"File Saved as: {filename}")
        print("="*40)
    else:
        print("[Notice] No data matched your filters. Check the URL or Keywords.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- PULSE SYSTEM: DATA INGESTION ENGINE ---")
    
    # Example Amazon Egypt search link for smartphones
    # رابط تجريبي للبحث عن الموبايلات في أمازون مصر
    AMAZON_URL = "https://www.amazon.eg/s?k=smartphones" 
    
    # Start the process
    run_advanced_scraper(category_name="Smartphones", search_url=AMAZON_URL, num_pages=2)