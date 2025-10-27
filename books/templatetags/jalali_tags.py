from django import template
from django.utils import timezone
import jdatetime
from datetime import datetime, date

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value, format_string='%Y/%m/%d'):
    """تبدیل تاریخ میلادی به شمسی"""
    if not value:
        return ''
    
    if isinstance(value, str):
        return value
    
    try:
        # تبدیل به تاریخ ساده اگر datetime باشد
        if hasattr(value, 'date'):
            # datetime object
            jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
        elif isinstance(value, date):
            # date object
            jalali_date = jdatetime.date.fromgregorian(date=value)
        else:
            return str(value)
        
        return jalali_date.strftime(format_string)
    except Exception as e:
        return str(value)

@register.filter(name='to_jalali_datetime')
def to_jalali_datetime(value):
    """تبدیل تاریخ و زمان میلادی به شمسی"""
    return to_jalali(value, '%Y/%m/%d %H:%M')

@register.filter(name='to_persian_number')
def to_persian_number(value):
    """تبدیل اعداد انگلیسی به فارسی"""
    if value is None:
        return ''
    
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    
    value_str = str(value)
    for i, digit in enumerate(english_digits):
        value_str = value_str.replace(digit, persian_digits[i])
    
    return value_str

