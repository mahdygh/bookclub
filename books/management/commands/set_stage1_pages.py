from django.core.management.base import BaseCommand

from books.models import Book


class Command(BaseCommand):
    help = "به‌روزرسانی تعداد صفحات کتاب‌های مرحله اول"

    mapping = {
        "آرمان عزیز": 25,
        "آشنایی با قرآن کریم (جزء اول)": 84,
        "آقا محسن": 47,
        "آقا مهدی": 48,
        "آقای ایرانی": 120,
        "آقای رئیس جمهور": 48,
        "آپارتمان در آتش": 100,
        "احکام دین": 73,
        "ادواردو، مسافری از رُم": 64,
        "از چیزی نمیترسیدم": 136,
        "اسم من پلاک است": 18,
        "برادران مزدور": 56,
        "برانکارد دربستی": 144,
        "برگه های سفید، دیوهای سیاه": 48,
        "بچه ای که نمیخواست آدم باشد": 80,
        "بچه ها بهنام": 24,
        "حاج همت": 49,
        "خاطرات خدا": 128,
        "خاطرات شیطان": 84,
        "خانم امدادگر": 48,
        "خمپاره های نقلی": 164,
        "داستان راستان": 368,
        "دردسرهای الاغ شاخ دار": 92,
        "دنیای یک پسر مو فرفری": 96,
        "رفیق مثل رسول": 192,
        "سلام بر ابراهیم 1": 240,
        "سه دقیقه در قیامت": 96,
        "سیاست نامه": 180,
        "صدا زدم باران": 156,
        "سیدمجتبی": 48,
        "عمو قاسم": 46,
        "قصه های ادواردو": 152,
        "قصه های شنیدنی حیوانات": 136,
        "مالک زمان": 120,
        "نقاشی روی آسمان": 82,
        "نقشه جاسوس": 326,
        "نورا": 136,
        "پرسش و پاسخ مهدوی": 72,
        "پسرک فلافل فروش": 120,
        "کشتی سیراف": 88,
        "10 قصه از امام زمان": 132,
    }

    def handle(self, *args, **options):
        missing = []
        updated = 0

        for title, pages in self.mapping.items():
            book = Book.objects.filter(title=title).first()
            if not book:
                missing.append(title)
                continue

            if book.page_count != pages:
                book.page_count = pages
                book.save(update_fields=["page_count"])
                updated += 1

        if updated:
            self.stdout.write(self.style.SUCCESS(f"Updated page_count for {updated} books."))
        else:
            self.stdout.write("No page_count changes applied.")

        if missing:
            missing_titles = ", ".join(missing)
            self.stdout.write(self.style.WARNING(f"Missing titles: {missing_titles}"))

