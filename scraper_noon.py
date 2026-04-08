
from playwright.sync_api import sync_playwright   # بنستورد Playwright اللي بيشغّل المتصفح
import csv                                         # بنستورد CSV عشان نحفظ البيانات في ملف
import time                                        # بنستورد time عشان نستخدم sleep
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# دالة بتجيب قيمة حقل واحد من المنتج حسب اللي المستخدم طلبه
def extract_field(p, field):                       # p = كارت المنتج ، field = اسم العنصر اللي عايزينه
    try:                                            # بنجرب نشوف الحقل موجود ولا لأ
        if field == "Title":                        # لو المستخدم اختار اسم المنتج
            return p.query_selector('h2[data-qa="plp-product-box-name"]').inner_text().strip()
                                                    # بنجيب الاسم ونشيله من المسافات

        elif field == "Price":                      # لو اختار السعر
            return p.query_selector('div[data-qa="plp-product-box-price"]').inner_text().strip()

        elif field == "URL":                        # لو اختار رابط المنتج
            return p.query_selector('a').get_attribute('href')

        elif field == "Image":                      # لو اختار الصورة
            return p.query_selector('img').get_attribute('src')

        elif field == "Rating":                  # لو اختار التقييم
          return p.query_selector('div[class*="textCtr"]').inner_text().strip()

        elif field == "Reviews":                    # لو اختار عدد الريفيوهات
            return p.query_selector('span.count').inner_text().strip()

        elif field == "Brand":                      # لو اختار البراند
            return p.query_selector('div[data-qa="product-box-brand"]').inner_text().strip()

        else:                                       # لو الحقل مش معروف
            return ""
    except:                                         # لو حصل خطأ أو العنصر مش موجود
        return ""

# دالة بتسحب صفحة واحدة فيها منتجات
def scrape_page(page, url, fields):                 # page = صفحة المتصفح، url = رابط، fields = الحقول المطلوبة
    try:
        page.goto(url, timeout=120000, wait_until="networkidle")
                                                    # بنفتح اللينك ونستنى لحد ما النت يهدى
    except:
        print("Timeout waiting for page to load.")  # لو الصفحة اتأخرت
        return []

    try:
        page.wait_for_selector('div[data-qa="plp-product-box"]', timeout=15000)
                                                    # نستنى أول كارت منتج يظهر
    except:
        print("Timeout waiting for products.")      # لو المنتجات مظهرتش
        return []

    products = page.query_selector_all('div[data-qa="plp-product-box"]')
                                                    # بنجيب كل كروت المنتجات في الصفحة

    page_data = []                                  # هنحط فيها بيانات المنتجات

    for p in products:                              # بنلف على كل منتج
        item = {}                                   # dict فاضية هنحط فيها البيانات المطلوبة
        for field in fields:                        # بنلف على كل حقل المستخدم اختاره
            item[field] = extract_field(p, field)   # بنجيب قيمة الحقل ونحطها في ال item
        page_data.append(item)                      # بنضيف المنتج لقائمة الصفحة

    return page_data                                # بنرجّع كل المنتجات اللي لقيناها

# دالة بتسحب كذا صفحة
def scrape_all_pages(base_query, fields, max_pages=5):
                                                    # base_query = كلمة البحث
    all_products = []                               # هنا هنحفظ كل المنتجات من كل الصفحات

    with sync_playwright() as p:                    # بنشغل playwright
        browser = p.chromium.launch(headless=False) # بنفتح المتصفح ( ظاهر مش مخفي )

        context = browser.new_context(              # بنعمل session جديدة
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                                    # بنحط User-Agent قوي عشان مانبانش بوت
        )

        page = context.new_page()                   # بنفتح صفحة جوّه المتصفح

        for page_num in range(1, max_pages + 1):    # بنلف على كل الصفحات
            print(f"Scraping page {page_num}...")   # بنطبع الصفحة اللي شغالين عليها

            url = f"https://www.noon.com/egypt-en/search/?q={base_query}&page={page_num}"
                                                    # بنبني لينك الصفحة

            products = scrape_page(page, url, fields)
                                                    # بنسحب المنتجات من الصفحة

            if not products:                        # لو مفيش داتا
                print("No products found on this page. Stopping.")
                break                               # بنوقف السحب

            all_products.extend(products)           # بنضيف منتجات الصفحة للقائمة الكبيرة

            time.sleep(2)                           # بريك صغير عشان نقلل الضغط

        browser.close()                             # نقفل المتصفح بعد ما نخلص

    return all_products                             # نرجّع كل المنتجات

# دالة لحفظ ملف CSV
def save_to_csv(data, filename):
    keys = data[0].keys() if data else []           # العناوين = أسماء الحقول
    with open(filename, 'w', newline='', encoding='utf-8') as f:
                                                    # نفتح ملف CSV نكتب فيه
        writer = csv.DictWriter(f, fieldnames=keys) # بنجهز الكاتب
        writer.writeheader()                        # نكتب الصف الأول (العناوين)
        writer.writerows(data)                      # نكتب كل المنتجات
    print(f"Data saved to {filename}")              # نطبع رسالة إن الملف اتحفظ

# الدالة الأساسية
def main():
    query = input("Enter the words  : ").strip().replace(" ", "+")
                                                    # ناخد كلمة البحث ونبدل المسافات بـ +

    print("\n اختار اللي انتى عايزو : ")     # نعرض الاختيارات
    print("1) Title")
    print("2) Price")
    print("3) URL")
    print("4) Image")
    print("5) Rating")
    print("6) Reviews")
    print("7) Brand\n")

    choice = input("اكتب الأرقام : ") # ناخد الأرقام اللي اختارها المستخدم

    numbers = [n.strip() for n in choice.split(",")]
                                                    # نفصلهم ونشيل المسافات

    mapping = {                                     # تحويل رقــم → اسم الحقل
        "1": "Title",
        "2": "Price",
        "3": "URL",
        "4": "Image",
        "5": "Rating",
        "6": "Reviews",
        "7": "Brand"
    }

    fields = [mapping[n] for n in numbers if n in mapping]
                                                    # نحدد فعلاً المستخدم اختار إيه

    max_pages = 30                                # عدد الصفحات اللي هنسحبها

    all_products = scrape_all_pages(query, fields, max_pages)
                                                    # نسحب الداتا

    save_to_csv(all_products, f"noon_{query}.csv")  # نحفظ الملف

if __name__ == "__main__":                          # لو الملف اتشغّل كبرنامج
    main()                                        # نشغل الدالة الرئيسية

