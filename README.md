# Code & Forge — Digital Atelier

موقع Django كامل بتصميم Cyberpunk Neon (Cyan × Hot Pink) لعرض وطلب الخدمات التقنية.

## التشغيل محلياً

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# افتح .env وعدّل DJANGO_SECRET_KEY وباقي القيم

python manage.py migrate
python manage.py loaddata services/fixtures/initial_services.json
python manage.py createsuperuser
python manage.py runserver
```

- الموقع: http://127.0.0.1:8000/
- لوحة التحكم: على المسار المحدد في `DJANGO_ADMIN_URL` داخل `.env`
  (وليس `/admin/` الافتراضي).

## ملخص الحماية الأمنية المطبّقة

| الخطر | الحماية |
|---|---|
| **XSS** | Django يقوم تلقائياً بترميز (escape) كل مخرجات القوالب؛ إضافةً لذلك تُنظَّف كل الحقول النصية عبر `bleach.clean()` قبل الحفظ في `services/forms.py`. |
| **SQL Injection** | كل الاستعلامات تمر عبر Django ORM (استعلامات معدّة/parameterized) — لا يوجد أي SQL خام في المشروع. |
| **CSRF** | `{% csrf_token %}` مُفعّل في نموذج طلب الخدمة، ومُطبّق عبر `CsrfViewMiddleware` و`@csrf_protect` على كل POST. |
| **Spam / Flooding** | `django-ratelimit` يحد الإرسال إلى 5 طلبات/ساعة لكل IP على مسار `request_service`، بالإضافة إلى حقل Honeypot مخفي لصد البوتات البسيطة. |
| **حماية لوحة الأدمن** | مسار غير افتراضي (`DJANGO_ADMIN_URL`)، جلسات مؤقتة (30 دقيقة)، تحقق كلمة مرور قوي (12 حرفاً كحد أدنى)، وصلاحية الحذف مقصورة على superuser. |
| **الكوكيز والـ Headers** | `Secure` + `HttpOnly` + `SameSite=Strict` على كوكيز الجلسة والـ CSRF، `HSTS`، `X-Frame-Options: DENY`، `X-Content-Type-Options: nosniff`. |
| **الأسرار (Secrets)** | تُقرأ كل القيم الحساسة (`SECRET_KEY`, بيانات قاعدة البيانات, بيانات البريد) من متغيرات البيئة عبر `python-decouple`، ولا تُكتب مباشرة في الكود. |

## هيكل المشروع

```
codeforge/
├── config/                # الإعدادات والـ URLs الرئيسية
├── services/               # التطبيق: Models / Forms / Views / Admin
│   ├── templates/services/ # قوالب صفحة الرئيسية وطلب الخدمة
│   └── fixtures/           # بيانات أولية لأنواع الخدمات
├── templates/base.html     # القالب الأساسي (Navbar / Footer / Neon theme)
├── static/css/neon.css     # نظام التصميم النيوني (Glow, Cards, Inputs)
└── requirements.txt
```
