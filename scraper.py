import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

def start_scraping(category_name, target_url):
    """
    وظيفة السحب: تأخذ اسم القسم والرابط وتقوم باستخراج البيانات وحفظها في ملف CSV.
    """
    
    # قائمة بمتصفحات وهمية (User-Agents) لتقليل فرص كشف السكربت من قبل الموقع
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US, en;q=0.5"
    }
    
    print(f"\n[!] جاري الاتصال بالموقع لسحب بيانات قسم: {category_name}...")
    
    try:
  #كود طلب للموقع علشان ناخد محتوي الصفحة 
        response = requests.get(target_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ خطأ: لم ينجح الاتصال بالموقع. كود الخطأ: {response.status_code}")
            return

        # تحليل محتوى الصفحة باستخدام BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        products_list = []

        # البحث عن حاويات المنتجات (Selectors خاصة بأمازون مصر)
        items = soup.find_all("div", {"data-component-type": "s-search-result"})

        for item in items:
            # 1. سحب اسم المنتج
            name_tag = item.h2
            name = name_tag.text.strip() if name_tag else "غير متوفر"
            
            # 2. سحب السعر (الجزء الصحيح قبل الفاصلة)
            price_tag = item.find("span", "a-price-whole")
            price = price_tag.text.strip().replace(",", "") if price_tag else "0"
            
            # 3. سحب التقييم (مثلاً: 4.5 من 5)
            rating_tag = item.find("span", "a-icon-alt")
            rating = rating_tag.text.split()[0] if rating_tag else "0"

            # إضافة البيانات للقائمة
            products_list.append({
                "Category": category_name,
                "Product_Name": name,
                "Price_EGP": price,
                "Rating": rating,
                "Source": "Amazon Egypt"
            })

        # التأكد من وجود بيانات قبل عملية الحفظ
        if products_list:
            df = pd.DataFrame(products_list)
            # إنشاء اسم ملف فريد بناءً على القسم
            file_name = f"raw_data_{category_name.replace(' ', '_')}.csv"
            
            # حفظ الملف بصيغة utf-8-sig لضمان ظهور اللغة العربية بشكل صحيح في Excel
            df.to_csv(file_name, index=False, encoding="utf-8-sig")
            
            print(f"✅ نجاح! تم سحب {len(df)} منتج وحفظهم في ملف: {file_name}")
        else:
            print("⚠️ تنبيه: لم يتم العثور على منتجات. تأكد من الرابط أو قم بتحديث الكلاسات (Classes).")

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")

# نقطة انطلاق البرنامج (Main)
if __name__ == "__main__":
    print("========================================")
    print("   Pulse System - Data Ingestion Tool   ")
    print("========================================\n")
    
    print("تعليمات للمستخدم:")
    print("1. ابحث في أمازون عن القسم المطلوب.")
    print("2. انسخ الرابط (URL) من أعلى المتصفح.")
    print("3. الصق الرابط هنا عندما يطلبه البرنامج.\n")
    
    # طلب المدخلات من المستخدم في الـ Terminal
    input_category = input("أدخل اسم القسم (مثلاً Laptops): ").strip()
    input_url = input("أدخل رابط البحث (URL): ").strip()
    
    if input_category and input_url:
        start_scraping(input_category, input_url)
    else:
        print("❌ خطأ: يجب إدخل اسم القسم والرابط للبدء.")