# کتابخانه گروهی (BookClub)

سیستم جامع مدیریت کتابخوانی گروهی با جنگو

## 🚀 ویژگی‌ها

### ✨ مدیریت دوره‌های کتابخوانی
- ایجاد و مدیریت دوره‌های مختلف
- تعریف مراحل سه‌گانه برای هر دوره
- مدیریت کتاب‌ها در هر مرحله

### 📚 مدیریت کتاب‌ها
- ثبت کتاب‌ها با تصویر جلد
- تعریف امتیاز خواندن و آزمون
- تعیین مدت زمان خواندن هر کتاب
- طبقه‌بندی کتاب‌ها در مراحل مختلف

### 👥 مدیریت اعضا
- ثبت‌نام و مدیریت اعضا
- پیگیری پیشرفت شخصی
- مدیریت مرحله فعلی هر عضو

### 🏆 سیستم رتبه‌بندی
- رتبه‌بندی کلی اعضا
- رتبه‌بندی مرحله‌ای
- نمایش نمودارهای آماری
- مقایسه عملکرد اعضا

### 📖 سیستم تخصیص و بازگشت
- تخصیص کتاب به اعضا
- ثبت تاریخ تحویل و موعد
- محاسبه جریمه تاخیر (۱۰ امتیاز در روز)
- ثبت امتیاز آزمون

### 🧪 سیستم آزمون
- ایجاد آزمون برای هر کتاب
- سوالات چندگزینه‌ای، درست/غلط و تشریحی
- محاسبه خودکار امتیاز

## 🛠️ تکنولوژی‌های استفاده شده

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5 (RTL)
- **Database**: SQLite (قابل تغییر به PostgreSQL/MySQL)
- **JavaScript**: ES6+ با Chart.js
- **CSS**: Custom CSS با پشتیبانی از فونت فارسی
- **Forms**: Django Crispy Forms

## 📋 پیش‌نیازها

- Python 3.8+
- pip
- Git

## 🚀 نصب و راه‌اندازی

### ۱. کلون کردن پروژه
```bash
git clone <repository-url>
cd bookclub
```

### ۲. ایجاد محیط مجازی
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### ۳. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### ۴. اجرای مایگریشن‌ها
```bash
python manage.py makemigrations
python manage.py migrate
```

### ۵. ایجاد کاربر ادمین
```bash
python manage.py createsuperuser
```

### ۶. اجرای سرور
```bash
python manage.py runserver
```

## 📁 ساختار پروژه

```
bookclub/
├── bookclub/          # تنظیمات اصلی جنگو
├── books/             # اپلیکیشن مدیریت کتاب‌ها
├── members/           # اپلیکیشن مدیریت اعضا
├── reading_sessions/  # اپلیکیشن جلسات کتابخوانی
├── templates/         # تمپلیت‌های HTML
├── static/            # فایل‌های استاتیک (CSS, JS)
├── media/             # فایل‌های آپلود شده
└── manage.py          # فایل مدیریت جنگو
```

## 🎯 نحوه استفاده

### برای مدیران

#### ۱. ایجاد دوره جدید
1. ورود به پنل ادمین
2. ایجاد دوره جدید در بخش "دوره‌های کتابخوانی"
3. تعریف مراحل سه‌گانه
4. اضافه کردن کتاب‌ها به هر مرحله

#### ۲. مدیریت اعضا
1. ایجاد کاربران جدید
2. تعیین مرحله فعلی هر عضو
3. تخصیص کتاب‌ها

#### ۳. ثبت بازگشت کتاب‌ها
1. انتخاب کتاب تحویل داده شده
2. ثبت امتیاز آزمون
3. محاسبه خودکار جریمه تاخیر

### برای اعضا

#### ۱. مشاهده پیشرفت
- صفحه "پیشرفت من" برای مشاهده وضعیت فعلی
- نمایش کتاب‌های در حال خواندن
- تاریخچه کتاب‌های تکمیل شده

#### ۲. شرکت در آزمون‌ها
- دسترسی به آزمون‌های کتاب‌های خوانده شده
- پاسخ به سوالات و کسب امتیاز

#### ۳. مشاهده رتبه‌بندی
- رتبه‌بندی کلی و مرحله‌ای
- نمودارهای آماری عملکرد

## 🔧 تنظیمات

### تغییر پایگاه داده
در فایل `bookclub/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### تنظیمات ایمیل
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
```

## 📱 ویژگی‌های ریسپانسیو

- طراحی کاملاً ریسپانسیو برای تمام دستگاه‌ها
- پشتیبانی از RTL برای زبان فارسی
- انیمیشن‌های جذاب و تعاملی
- رابط کاربری مدرن و کاربرپسند

## 🎨 سفارشی‌سازی

### تغییر رنگ‌ها
در فایل `static/css/style.css`:

```css
:root {
    --primary-color: #your-color;
    --secondary-color: #your-color;
    /* ... */
}
```

### اضافه کردن فونت جدید
```css
@font-face {
    font-family: 'YourFont';
    src: url('path/to/your/font.woff2') format('woff2');
}
```

## 🧪 تست

```bash
python manage.py test
```

## 📊 API

پروژه شامل API‌های زیر است:

- `GET /api/rankings/` - دریافت رتبه‌بندی‌ها
- `GET /api/user/{id}/progress/` - پیشرفت کاربر
- `GET /api/user/{id}/notifications/` - اعلان‌های کاربر

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کردن پروژه
2. ایجاد شاخه جدید (`git checkout -b feature/AmazingFeature`)
3. Commit تغییرات (`git commit -m 'Add some AmazingFeature'`)
4. Push به شاخه (`git push origin feature/AmazingFeature`)
5. ایجاد Pull Request

## 📝 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## 📞 پشتیبانی

برای سوالات و مشکلات:

- ایجاد Issue در GitHub
- تماس با تیم توسعه

## 🔮 ویژگی‌های آینده

- [ ] سیستم اعلان‌های push
- [ ] اپلیکیشن موبایل
- [ ] سیستم چت گروهی
- [ ] گزارش‌های پیشرفته
- [ ] سیستم گواهینامه
- [ ] یکپارچه‌سازی با شبکه‌های اجتماعی

---

**نکته**: این پروژه برای استفاده در محیط‌های آموزشی و کتابخانه‌های گروهی طراحی شده است.
