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

category_map = {
    "laptops": "laptops",
    "smartphones": "smartphones",
    "smartwatches": "smartwatch",
    "gaming": "gaming laptop"
}

search_query = category_map.get(category, category)

# -----------------------------
# فلترة الكلمات
# -----------------------------
def get_exclude_keywords(cat):
    cat = cat.lower() # تحويل اسم الكاتيجوري لسمول للمقارنة
    if "laptop" in cat:
        return ['bag', 'case', 'mouse', 'keyboard', 'adapter', 'cable', 'شنطة', 'ماوس']
    elif "watch" in cat:
        return ['strap', 'band', 'charger', 'case', 'screen protector', 'استيك', 'سوار']
    elif "phone" in cat:
        return ['case', 'cover', 'holder', 'charger', 'cable', 'جراب', 'لاصقة', 'حماية']
    elif "appliance" in cat: # للأجهزة المنزلية
        return ['filter', 'spare part', 'cleaner', 'فلتر', 'قطع غيار']
    elif "beauty" in cat or "makeup" in cat:
        return ['bag', 'empty', 'organizer', 'شنطة', 'منظم']
    else:
        return []

exclude_keywords = get_exclude_keywords(category)

# -----------------------------
# تشغيل المتصفح (مع إضافة User-Agent لأمازون)
# -----------------------------
options = webdriver.ChromeOptions()
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# options.add_argument('--headless') # فك الكومنت لو مش عايز المتصفح يفتح قدامك

service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)

seen_products = set()
products_data = []

# -----------------------------
# تحميل الصور
# -----------------------------
def download_image(img_url, filename):
    try:
        if not img_url or img_url == "No Image":
            return None

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(img_url, headers=headers, timeout=10)

        if response.status_code == 200:
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
    for _ in range(10):
        browser.execute_script("window.scrollBy(0, 800);")
        time.sleep(0.5)

# -----------------------------
# Scraping logic for Amazon
# -----------------------------
def get_products_info():
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')

    # بنمسك كارت المنتج بالكامل (ده سليم في أمازون)
    products = soup.select('div[data-component-type="s-search-result"]')

    for product in products:
        # 1. الاسم - بندور عليه في الـ h2
        name_tag = product.select_one('h2 span')
        name = name_tag.text.strip() if name_tag else "N/A"

        if name == "N/A" or name in seen_products:
            continue
        if any(word in name.lower() for word in exclude_keywords):
            continue
        seen_products.add(name)

        # 2. رابط المنتج - بندور على أي لينك جواه كود المنتج /dp/
        product_url = "No Link"
        # بندور على أول لينك 'a' جواه "/dp/"
        url_tag = product.find('a', href=True, class_='a-link-normal')
        if not url_tag or "/dp/" not in url_tag.get('href', ''):
             url_tag = product.select_one('a[href*="/dp/"]')
        
        if url_tag:
            href = url_tag.get('href')
            # لو اللينك ناقص بنكمله
            product_url = "https://www.amazon.eg" + href if href.startswith("/") else href
            # بننظف اللينك من الزيادات
            product_url = product_url.split("?")[0].split("/ref=")[0]

        # 3. السعر
        price_tag = product.select_one('.a-price-whole')
        price = price_tag.text.replace(',', '').strip() if price_tag else "N/A"

        # 4. التقييم
        rate_tag = product.select_one('i[class*="a-icon-star"]')
        rate_text = rate_tag.text if rate_tag else "0.0"
        rate_match = re.search(r"(\d+\.\d+|\d+)", rate_text)
        final_rate = rate_match.group(1) if rate_match else "0.0"

        # 5. الصورة - الحل بناءً على الصورة اللي بعتها
        img_tag = product.select_one('img.s-image')
        img_url = "No Image"
        if img_tag:
            # بنجرب الـ src العادي الأول
            img_url = img_tag.get('src')
            
            # لو طلع صورة وهمية (pixel) أو placeholder بنروح للـ srcset
            if not img_url or "data:image" in img_url or "1x1.gif" in img_url:
                srcset = img_tag.get('srcset')
                if srcset:
                    # الـ srcset بيبقى فيه كذا جودة، بناخد أول واحدة
                    img_url = srcset.split(",")[0].split(" ")[0]
                else:
                    # آخر محاولة مع data-src
                    img_url = img_tag.get('data-src', "No Image")

        # حفظ البيانات
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_"))[:50].strip()
        image_path = download_image(img_url, safe_name)

        products_data.append({
            "name": name,
            "price": price,
            "rating": final_rate,
            "image_url": img_url,
            "image_path": image_path if image_path else "No Image",
            "source": "Amazon",
            "category_name": category,
            "product_url": product_url
        })
        
        print(f"Captured: {name[:30]}... | Link: {'OK' if 'amazon' in product_url else 'Fixed'}")

# -----------------------------
# Pagination
# -----------------------------
# رابط أمازون مصر للبحث
base_url = f"https://www.amazon.eg/s?k={search_query}&page="

for page in range(1, pages + 1):
    print(f"\n--- Scraping Amazon Page {page} ---")
    
    browser.get(base_url + str(page))
    
    try:
        # استنتاج إن المنتجات ظهرت
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]'))
        )
        scroll_page()
        get_products_info()
    except Exception as e:
        print(f"Error or No results on page {page}")
        break

    time.sleep(random.uniform(2, 4)) # بريك بسيط عشان الحظر

browser.quit()

# -----------------------------
# حفظ CSV
# -----------------------------
import csv # تأكد إنك ضفت السطر ده في أول الكود خالص مع الـ imports

# ... (بقية الكود بتاع السحب)

if products_data:
    df = pd.DataFrame(products_data)
    cols = ["name", "price", "rating", "image_url", "image_path", "source", "category_name", "product_url"]
    df = df[cols]
    
    # التعديل السحري هنا:
    df.to_csv(
        f"clean_data/amazon_{category}.csv", 
        index=False, 
        encoding='utf-8-sig', 
        quoting=csv.QUOTE_ALL  # ده بيخلي كل خلية محاطة بـ " " عشان اللينكات ما تسيحش على بعض
    )
    
    print(f"\nDONE ✅ | Total Products: {len(products_data)}")
else:
    print("\nNo data found! ❌")