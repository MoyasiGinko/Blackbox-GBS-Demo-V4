from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Create a superuser programmatically'

    def handle(self, *args, **kwargs):
        email = 'moyasi@gmail.com'
        full_name = 'Moyasi'
        password = 'moyasi17'

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Superuser with email "{email}" already exists.'))
        else:
            User.objects.create_superuser(email=email, full_name=full_name, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser with email "{email}" created successfully.'))
