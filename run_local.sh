#!/usr/bin/env bash
set -e

echo "==> 1/6 إنشاء virtual environment"
python3 -m venv venv
source venv/bin/activate

echo "==> 2/6 تثبيت المكتبات"
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f .env ]; then
  echo "==> .env مش موجود! لازم يكون موجود قبل ما تشغل السكريبت ده."
  exit 1
fi

echo "==> 3/6 تنفيذ migrate"
python manage.py migrate

echo "==> 4/6 تحميل بيانات الخدمات الأولية"
python manage.py loaddata services/fixtures/initial_services.json

echo "==> 5/6 إنشاء حساب superuser (لو مش موجود بالفعل)"
echo "هتُسأل عن username / email / password دلوقتي:"
python manage.py createsuperuser || true

echo "==> 6/6 تشغيل السيرفر المحلي"
echo "الصفحة الرئيسية: http://127.0.0.1:8000/"
echo "طلب خدمة:        http://127.0.0.1:8000/request-service/"
ADMIN_PATH=$(grep DJANGO_ADMIN_URL .env | cut -d '=' -f2)
echo "لوحة التحكم:      http://127.0.0.1:8000/${ADMIN_PATH}"
python manage.py runserver
