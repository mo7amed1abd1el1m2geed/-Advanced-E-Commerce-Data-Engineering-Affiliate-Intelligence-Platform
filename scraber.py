from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import requests
import os
import random
import re
import pandas as pd

# -----------------------------
# إنشاء فولدرات
# -----------------------------
os.makedirs('product_images', exist_ok=True)
os.makedirs('clean_data', exist_ok=True)

# -----------------------------
# إدخال المستخدم
# -----------------------------
category = input("Enter category: ").strip().lower()
pages = int(input("Enter number of pages: "))

# -----------------------------
# تحويل الكاتيجوري لرابط
# -----------------------------
category_map = {
    "laptops": "laptops",
    "smartphones": "smartphones",
    "smartwatches": "smartwatch",
    "home appliances": "home appliances",
    "beauty": "beauty",
    "furniture": "furniture",
    "medical": "medical",
    "fashion": "fashion",
    "men": "men fashion",
    "women": "women fashion",
    "shoes": "shoes",
    "baby": "baby",
    "gaming": "gaming"
}

search_query = category_map.get(category, category)

# -----------------------------
# فلترة
# -----------------------------
def get_exclude_keywords(cat):
    if "laptop" in cat:
        return ['bag', 'case', 'mouse', 'keyboard']
    elif "watch" in cat:
        return ['strap', 'band', 'charger', 'case']
    elif "phone" in cat:
        return ['case', 'cover', 'holder']
    else:
        return []

exclude_keywords = get_exclude_keywords(category)

# -----------------------------
# تشغيل المتصفح
# -----------------------------
service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service)

# -----------------------------
# بيانات
# -----------------------------
seen_products = set()
products_data = []

# -----------------------------
# تحميل الصور
# -----------------------------
def download_image(img_url, filename):
    try:
        if img_url == "No Image":
            return None

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(img_url, headers=headers, timeout=10)

        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            path = f"product_images/{filename}.jpg"

            with open(path, "wb") as f:
                f.write(response.content)

            if os.path.getsize(path) < 2000:
                os.remove(path)
                return None

            return path
    except:
        return None

# -----------------------------
# Scroll
# -----------------------------
def scroll_page():
    for _ in range(15):
        browser.execute_script("window.scrollBy(0, 2000);")
        time.sleep(1)

# -----------------------------
# Scraping
# -----------------------------
def get_products_info():
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')

    # بنمسك الـ a tag اللي شايل الكارت كله
    products = soup.select('a[class*="productBoxLink"]')

    for product in products:
        # 1. رابط المنتج (بناخده مباشرة من العنصر اللي واقفين عليه)
        product_url = product.get('href', 'No Link')
        if product_url.startswith("/"):
            product_url = "https://www.noon.com" + product_url

        # 2. الاسم (بندور جواه)
        name_tag = product.select_one('h2') 
        name = name_tag.text.strip() if name_tag else "N/A"

        if name in seen_products:
            continue
        seen_products.add(name)

        # فلترة الكلمات المستبعدة
        if any(word in name.lower() for word in exclude_keywords):
            continue

        # 3. السعر
        price_tag = product.select_one('strong')
        price = price_tag.text.strip() if price_tag else "N/A"

        # 4. التقييم
        rate_tag = product.select_one('div[class*="RatingPreview"]')
        rate = rate_tag.text.strip() if rate_tag else "0.0"
        rate_val = re.findall(r"[-+]?\d*\.\d+|\d+", rate)
        final_rate = rate_val[0] if rate_val else "0.0"

        # 5. الصورة
        img_tag = product.select_one('img')
        img_url = "No Image"
        if img_tag:
            img_url = (img_tag.get('data-src') or img_tag.get('src') or img_tag.get('srcset'))
            if img_url and " " in img_url: img_url = img_url.split(" ")[0]
            if img_url and img_url.startswith('//'): img_url = 'https:' + img_url
            
            # تنظيف إضافي لو الصورة طلعت placeholder
            if not img_url or "placeholder" in img_url or "svg" in img_url:
                img_url = "No Image"
        # طباعة للتأكد
        print(f"{name} | {price} | {product_url[:50]}...")

        # حفظ البيانات
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_"))[:50]
        image_path = download_image(img_url, safe_name)

        products_data.append({
            "name": name,
            "price": price,
            "rating": final_rate,
            "image_url": img_url,
            "image_path": image_path if image_path else "No Image",
            "source": "Noon",
            "category_name": category,
            "product_url": product_url
        })

        time.sleep(random.uniform(0.5, 1.5))

# -----------------------------
# Pagination
# -----------------------------
base_url = f"https://www.noon.com/egypt-en/search/?q={search_query}&page="

for page in range(1, pages + 1):
    print(f"Page {page} 🔥")

    browser.get(base_url + str(page))

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "img"))
    )

    scroll_page()
    get_products_info()

# -----------------------------
# إنهاء
# -----------------------------
browser.quit()

# -----------------------------
# حفظ CSV
# -----------------------------
df = pd.DataFrame(products_data)

# ترتيب الأعمدة النهائي
df = df[
    [
        "name",
        "price",
        "rating",
        "image_url",
        "image_path",
        "source",
        "category_name",
        "product_url"
    ]
]

df.to_csv(f"clean_data/{category}.csv", index=False, encoding='utf-8-sig')

print("DONE ✅")