from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from subscription_app.models import SubscriptionPlan
from service_app.models import Service
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed database with initial subscription plans and services'

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding database with initial data...")

        # Create test users
        self.create_test_users()

        # Create services
        services = self.create_services()

        # Create subscription plans
        self.create_subscription_plans(services)

        self.stdout.write(
            self.style.SUCCESS('🎉 Database seeding completed successfully!')
        )

    def create_test_users(self):
        """Create test users if they don't exist."""
        self.stdout.write("Creating test users...")

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'full_name': 'Admin User',
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write("✅ Admin user created")
        else:
            self.stdout.write("ℹ️  Admin user already exists")

        # Create test user
        test_user, created = User.objects.get_or_create(
            email='testuser@example.com',
            defaults={
                'full_name': 'Test User',
                'is_verified': True
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write("✅ Test user created")
        else:
            self.stdout.write("ℹ️  Test user already exists")

    def create_services(self):
        """Create sample services."""
        self.stdout.write("Creating sample services...")

        services_data = [
            {
                'name': 'chatgpt',
                'display_name': 'ChatGPT Plus',
                'login_url': 'https://chat.openai.com/auth/login',
                'description': 'Advanced AI chatbot with GPT-4 access',
                'category': 'ai_chat'
            },
            {
                'name': 'claude',
                'display_name': 'Claude Pro',
                'login_url': 'https://claude.ai/login',
                'description': 'Anthropic\'s advanced AI assistant',
                'category': 'ai_chat'
            },
            {
                'name': 'midjourney',
                'display_name': 'Midjourney',
                'login_url': 'https://www.midjourney.com/auth',
                'description': 'AI-powered image generation tool',
                'category': 'ai_image'
            },
            {
                'name': 'semrush',
                'display_name': 'SEMrush',
                'login_url': 'https://www.semrush.com/auth/',
                'description': 'Comprehensive SEO and marketing toolkit',
                'category': 'seo'
            },
            {
                'name': 'ahrefs',
                'display_name': 'Ahrefs',
                'login_url': 'https://ahrefs.com/auth/login',
                'description': 'Advanced SEO toolset for professionals',
                'category': 'seo'
            },
        ]

        created_services = []
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            created_services.append(service)
            if created:
                self.stdout.write(f"✅ Created service: {service.display_name}")
            else:
                self.stdout.write(f"ℹ️  Service already exists: {service.display_name}")

        return created_services

    def create_subscription_plans(self, services):
        """Create subscription plans."""
        self.stdout.write("Creating subscription plans...")

        # Individual Plan - 1 service
        individual_plan, created = SubscriptionPlan.objects.get_or_create(
            name='Individual Plan',
            defaults={
                'description': 'Access to 1 premium AI/SEO tool of your choice',
                'price': Decimal('9.99'),
                'duration_days': 30,
                'max_services': 1,
                'is_active': True
            }
        )
        if created:
            individual_plan.services.set(services)
            self.stdout.write("✅ Created Individual Plan")
        else:
            self.stdout.write("ℹ️  Individual Plan already exists")

        # 5-Service Plan
        service_plan, created = SubscriptionPlan.objects.get_or_create(
            name='5-Service Pack',
            defaults={
                'description': 'Access to 5 premium AI/SEO tools of your choice',
                'price': Decimal('29.99'),
                'duration_days': 30,
                'max_services': 5,
                'is_active': True
            }
        )
        if created:
            service_plan.services.set(services)
            self.stdout.write("✅ Created 5-Service Pack")
        else:
            self.stdout.write("ℹ️  5-Service Pack already exists")

        # Premium Plan
        premium_plan, created = SubscriptionPlan.objects.get_or_create(
            name='Premium Pack',
            defaults={
                'description': 'Access to ALL premium AI/SEO tools available',
                'price': Decimal('79.99'),
                'duration_days': 30,
                'max_services': 15,
                'is_active': True
            }
        )
        if created:
            premium_plan.services.set(services)
            self.stdout.write("✅ Created Premium Pack")
        else:
            self.stdout.write("ℹ️  Premium Pack already exists")
