import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth.models import User

# Check if admin exists
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@jahani.com',
        password='admin123'
    )
    print(f"Admin created: username='admin', password='admin123'")
else:
    print("Admin user already exists")
