     # Edu Platform Full (Django)
     ### كيفية التشغيل محليًا
     1. فك الضغط وادخل المجلد edu_platform_full

     2. إنشاء بيئة افتراضية:
python -m venv venv
venv\Scripts\activate

     3. تثبيت المتطلبات:
pip install -r requirements.txt
python -m pip install Pillow
pip install django-jazzmin
pip install python-dotenv django-jazzmin whitenoise pillow

     4. تنفيذ التهيئة:
python manage.py makemigrations
python manage.py migrate

     5. إنشاء الأدمن الافتراضي:
python manage.py create_default_admin

     6. تشغيل السيرفر:
python manage.py runserver 0.0.0.0:8000


     - تسجيل الدخول للحساب الافتراضي: username: Abdo  password: 1234
     - غيّر كلمة المرور فورًا بعد تسجيل الدخول

https://canyouseeme.org/#google_vignette
