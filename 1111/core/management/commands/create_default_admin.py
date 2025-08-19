from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile

class Command(BaseCommand):
    help = 'Create default admin Abdo/1234'

    def handle(self, *args, **options):
        if not User.objects.filter(username='Abdo').exists():
            user = User.objects.create_user(username='Abdo', password='1234')
            Profile.objects.create(user=user, role='admin')
            self.stdout.write(self.style.SUCCESS('Created default admin Abdo'))
        else:
            self.stdout.write('Abdo already exists')
