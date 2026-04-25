import csv
import os
import random
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import quote
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 1. إعداد المجلدات لحفظ الصور والملفات
IMAGE_DIR = "global_all_categories_images"
DATA_DIR = "global_all_categories_data"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 2. قاموس الكلمات المفتاحية للـ 13 قسم (كل قسم له كلمات بحث مختلفة لضمان الوصول لـ 1000 منتج)
SEARCH_VARIANTS = {
    "1": {"name": "Laptops & Computers", "queries": ["laptops", "desktop computers", "gaming pc", "macbook", "workstation pc"]},
    "2": {"name": "Smartphones", "queries": ["smartphones", "iphone", "samsung galaxy", "android phones", "unlocked phones"]},
    "3": {"name": "Smartwatches", "queries": ["smartwatches", "apple watch", "fitness trackers", "garmin watch", "samsung gear"]},
    "4": {"name": "Home Appliances", "queries": ["refrigerators", "washing machines", "microwaves", "air conditioners", "vacuum cleaners"]},
    "5": {"name": "Beauty & Makeup", "queries": ["makeup sets", "skincare products", "hair dryer", "perfumes", "beauty appliances"]},
    "6": {"name": "Home Furniture", "queries": ["living room furniture", "office chairs", "bedroom sets", "dining tables", "sofas"]},
    "7": {"name": "Medical Products", "queries": ["blood pressure monitor", "first aid kit", "thermometers", "wheelchairs", "medical supplies"]},
    "8": {"name": "Fashion", "queries": ["accessories", "watches", "sunglasses", "jewelry", "bags"]},
    "9": {"name": "Men's Fashion", "queries": ["mens shirts", "mens jeans", "mens jackets", "mens suits", "mens activewear"]},
    "10": {"name": "Women's Fashion", "queries": ["womens dresses", "womens tops", "womens skirts", "womens coats", "womens jewelry"]},
    "11": {"name": "Footwear (Shoes)", "queries": ["running shoes", "formal shoes", "sneakers", "boots", "sandals"]},
    "12": {"name": "Baby Products", "queries": ["baby strollers", "baby car seats", "baby monitors", "diapers", "baby toys"]},
    "13": {"name": "Gaming & Consoles", "queries": ["playstation 5", "xbox series x", "nintendo switch", "gaming consoles", "vr headsets"]}
}

# قائمة الكلمات المستبعدة للتأكد من سحب أجهزة/منتجات حقيقية وليس مجرد إكسسوارات
HARD_EXCLUDE = ["case", "cover", "protector", "cable", "charger", "adapter", "strap", "band", "sticker", "pouch"]

# دالة للتأكد من أن اسم المنتج لا يحتوي على كلمات الإكسسوارات المستبعدة
def is_clean_product(name):
    return not any(word in name.lower() for word in HARD_EXCLUDE)

# إعدادات المتصفح (Chrome) لإخفاء ملامح الأتمتة وتجنب الحظر
def setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(), options=options)

# 3. واجهة التفاعل مع المستخدم في الـ Terminal
print("\n" + "="*60)
print("--- Amazon Global Scraper: 13 Categories Edition ---")
print("="*60)

try:
    # الحصول على سعر صرف الدولار يدوياً من المستخدم
    usd_rate = float(input("💵 Enter USD to EGP exchange rate (e.g., 52.7): "))
except ValueError:
    print("❌ Error: Please enter a valid number for the exchange rate.")
    exit()

# عرض القائمة الكاملة للأقسام
print("\nSelect the category to scrape:")
for key, value in SEARCH_VARIANTS.items():
    print(f"{key}- {value['name']}")

choice = input("\n👉 Enter category number: ")
if choice not in SEARCH_VARIANTS:
    print("❌ Invalid choice! Please restart and select a number from the list.")
    exit()

selected_cat = SEARCH_VARIANTS[choice]
TARGET = 1000 # العدد المطلوب تجميعه
browser = setup_browser()
seen_asins = set() # مجموعة لمنع تكرار نفس المنتج
products_data = [] # القائمة التي ستخزن فيها البيانات النهائية

# 4. بدء عملية سحب البيانات (Scraping)
try:
    # المرور على كل كلمة بحث موجودة في القسم المختار
    for query in selected_cat["queries"]:
        if len(products_data) >= TARGET: break
        
        print(f"\n🚀 Searching Amazon Global for: {query}")
        page = 1
        # التنقل بين صفحات نتائج البحث (بحد أقصى 25 صفحة لكل كلمة بحث)
        while page <= 25 and len(products_data) < TARGET:
            browser.get(f"https://www.amazon.com/s?k={quote(query)}&page={page}")
            try:
                # الانتظار حتى تظهر نتائج البحث في الصفحة
                WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')))
            except: 
                print(f"⚠️ No more results found on page {page}")
                break

            # تحليل كود الصفحة باستخدام BeautifulSoup
            soup = BeautifulSoup(browser.page_source, "lxml")
            cards = soup.select('div[data-component-type="s-search-result"]')
            
            for card in cards:
                asin = card.get("data-asin", "")
                if not asin or asin in seen_asins: continue
                
                name_el = card.select_one("h2 span")
                if not name_el: continue
                name = name_el.text.strip()
                
                # تطبيق فلتر تنقية المنتجات من الإكسسوارات
                if not is_clean_product(name): continue
                
                # استخراج السعر وتحويله من دولار لجنيه مصري
                price_whole = card.select_one(".a-price-whole")
                price_egp = round(float(price_whole.text.replace(",", "")) * usd_rate, 2) if price_whole else "N/A"
                
                # استخراج التقييم (مثلاً: 4.5 من 5)
                rating_el = card.select_one("i[class*='a-icon-star'] span")
                rating = rating_el.text.split()[0] if rating_el else "0"
                
                # استخراج رابط الصورة الأصلية
                img_tag = card.select_one("img.s-image")
                img_url = img_tag.get("src") if img_tag else ""
                
                # تحميل الصورة وحفظها في المجلد المخصص
                img_path = "No Image"
                if img_url:
                    try:
                        img_path = f"{IMAGE_DIR}/{asin}.jpg"
                        if not os.path.exists(img_path):
                            with open(img_path, "wb") as f: 
                                f.write(requests.get(img_url, timeout=10).content)
                    except: 
                        img_path = "No Image"

                # إضافة البيانات النهائية في شكل قاموس (Dictionary) يطابق الأعمدة الـ 8 المطلوبة
                products_data.append({
                    "name": name,                       # 1. اسم المنتج
                    "price": price_egp,                 # 2. السعر بالجنيه
                    "rating": rating,                   # 3. التقييم
                    "image-url": img_url,               # 4. رابط الصورة
                    "image-path": img_path,             # 5. مسار الصورة محلياً
                    "source": "Amazon Global",          # 6. المصدر
                    "category-name": selected_cat["name"], # 7. اسم القسم
                    "product-url": f"https://www.amazon.com/dp/{asin}" # 8. رابط المنتج
                })
                seen_asins.add(asin)
                if len(products_data) >= TARGET: break

            print(f"✅ Collected {len(products_data)} products so far...")
            page += 1
            # انتظار عشوائي بين الصفحات لتجنب اكتشاف "البوت" وحظر الـ IP
            time.sleep(random.uniform(2, 4))

finally:
    # إغلاق المتصفح بعد الانتهاء
    browser.quit()
    
    # 5. حفظ البيانات النهائية في ملف CSV
    if products_data:
        df = pd.DataFrame(products_data)
        # ترتيب الأعمدة حسب الترتيب المطلوب من 1 لـ 8
        cols = ["name", "price", "rating", "image-url", "image-path", "source", "category-name", "product-url"]
        safe_name = selected_cat["name"].replace(" ", "_").lower()
        output_file = f"{DATA_DIR}/final_{safe_name}_1000.csv"
        df[cols].to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Task Completed Successfully!")
        print(f"📂 Final file saved at: {output_file}")
    else:
        print("\n❌ No data collected. Please check your internet or keywords.")