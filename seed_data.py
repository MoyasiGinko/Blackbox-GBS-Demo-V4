#!/usr/bin/env python3
"""
Seed database with initial subscription plans and services for testing.
"""

import os
import sys
import django

# Setup Django
sys.path.append('e:\\Github\\GBST\\Blackbox-GBS-Demo-V4')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cookie_auth_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscription_app.models import SubscriptionPlan
from service_app.models import Service
from decimal import Decimal

User = get_user_model()

def create_test_users():
    """Create test users if they don't exist."""
    print("Creating test users...")

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
        print("✅ Admin user created")
    else:
        print("ℹ️  Admin user already exists")

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
        print("✅ Test user created")
    else:
        print("ℹ️  Test user already exists")

def create_services():
    """Create sample services."""
    print("Creating sample services...")

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
        {
            'name': 'jasper',
            'display_name': 'Jasper AI',
            'login_url': 'https://app.jasper.ai/login',
            'description': 'AI writing assistant for content creation',
            'category': 'ai_chat'
        },
        {
            'name': 'copy_ai',
            'display_name': 'Copy.ai',
            'login_url': 'https://app.copy.ai/login',
            'description': 'AI-powered copywriting tool',
            'category': 'ai_chat'
        },
        {
            'name': 'canva_pro',
            'display_name': 'Canva Pro',
            'login_url': 'https://www.canva.com/login',
            'description': 'Professional design platform',
            'category': 'other'
        }
    ]

    created_services = []
    for service_data in services_data:
        service, created = Service.objects.get_or_create(
            name=service_data['name'],
            defaults=service_data
        )
        created_services.append(service)
        if created:
            print(f"✅ Created service: {service.display_name}")
        else:
            print(f"ℹ️  Service already exists: {service.display_name}")

    return created_services

def create_subscription_plans(services):
    """Create subscription plans."""
    print("Creating subscription plans...")

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
        print("✅ Created Individual Plan")
    else:
        print("ℹ️  Individual Plan already exists")

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
        print("✅ Created 5-Service Pack")
    else:
        print("ℹ️  5-Service Pack already exists")

    # 15-Service Plan
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
        print("✅ Created Premium Pack")
    else:
        print("ℹ️  Premium Pack already exists")

    # Quarterly Plans
    quarterly_plan, created = SubscriptionPlan.objects.get_or_create(
        name='Quarterly Premium',
        defaults={
            'description': 'Access to ALL tools for 3 months - Best Value!',
            'price': Decimal('199.99'),
            'duration_days': 90,
            'max_services': 20,
            'is_active': True
        }
    )
    if created:
        quarterly_plan.services.set(services)
        print("✅ Created Quarterly Premium")
    else:
        print("ℹ️  Quarterly Premium already exists")

def main():
    """Main seeding function."""
    print("🌱 Seeding database with initial data...")
    print("=" * 50)

    try:
        create_test_users()
        print()

        services = create_services()
        print()

        create_subscription_plans(services)
        print()

        print("=" * 50)
        print("🎉 Database seeding completed successfully!")

        # Print summary
        print("\nSummary:")
        print(f"📧 Users: {User.objects.count()}")
        print(f"🛍️  Services: {Service.objects.count()}")
        print(f"📋 Subscription Plans: {SubscriptionPlan.objects.count()}")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
