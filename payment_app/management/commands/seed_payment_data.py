from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from decimal import Decimal
import random
from payment_app.models import Payment
from auth_app.models import User
from subscription_app.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Seed payment data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of payments to create'
        )

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write('🌱 Seeding payment data...')

        # Get users and plans
        users = list(User.objects.all())
        plans = list(SubscriptionPlan.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return

        if not plans:
            self.stdout.write(self.style.ERROR('No subscription plans found. Please create plans first.'))
            return

        payment_methods = ['stripe', 'paypal', 'crypto']
        payment_statuses = ['success', 'failed', 'refunded', 'pending']
        status_weights = [0.7, 0.1, 0.05, 0.15]  # 70% success, 10% failed, 5% refunded, 15% pending

        created_count = 0

        for i in range(count):
            try:
                user = random.choice(users)
                plan = random.choice(plans)
                payment_method = random.choice(payment_methods)
                payment_status = random.choices(payment_statuses, weights=status_weights)[0]

                # Create payment date within last 6 months
                days_ago = random.randint(0, 180)
                payment_date = timezone.now() - timedelta(days=days_ago)

                # Simulate different transaction scenarios
                if payment_status == 'success':
                    transaction_id = f"txn_success_{timezone.now().timestamp()}_{i}"
                    metadata = {
                        'gateway_response': {
                            'status': 'completed',
                            'gateway_fee': round(float(plan.price) * 0.029 + 0.30, 2)
                        },
                        'processed_at': payment_date.isoformat()
                    }
                elif payment_status == 'failed':
                    transaction_id = f"txn_failed_{timezone.now().timestamp()}_{i}"
                    metadata = {
                        'failure_reason': random.choice([
                            'Insufficient funds',
                            'Card declined',
                            'Network error',
                            'Invalid card'
                        ]),
                        'gateway_response': {'status': 'failed'},
                        'failed_at': payment_date.isoformat()
                    }
                elif payment_status == 'refunded':
                    transaction_id = f"txn_refunded_{timezone.now().timestamp()}_{i}"
                    metadata = {
                        'refund_reason': random.choice([
                            'Customer request',
                            'Service not delivered',
                            'Duplicate payment',
                            'Policy violation'
                        ]),
                        'refund_amount': str(plan.price),
                        'refunded_at': (payment_date + timedelta(days=random.randint(1, 30))).isoformat(),
                        'gateway_response': {'status': 'refunded'}
                    }
                else:  # pending
                    transaction_id = f"txn_pending_{timezone.now().timestamp()}_{i}"
                    metadata = {
                        'gateway_response': {'status': 'pending'},
                        'created_at': payment_date.isoformat()
                    }

                payment = Payment.objects.create(
                    user=user,
                    subscription_plan=plan,
                    amount=plan.price,
                    payment_status=payment_status,
                    payment_method=payment_method,
                    transaction_id=transaction_id,
                    payment_metadata=metadata
                )

                # Override the auto_now_add for payment_date
                payment.payment_date = payment_date
                payment.save()

                created_count += 1

                if created_count % 5 == 0:
                    self.stdout.write(f'Created {created_count} payments...')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating payment {i}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully created {created_count} payments')
        )

        # Show summary statistics
        self.show_statistics()

    def show_statistics(self):
        """Show payment statistics after seeding."""
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(payment_status='success').count()
        failed_payments = Payment.objects.filter(payment_status='failed').count()
        pending_payments = Payment.objects.filter(payment_status='pending').count()
        refunded_payments = Payment.objects.filter(payment_status='refunded').count()

        total_revenue = Payment.objects.filter(payment_status='success').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        self.stdout.write('\n📊 Payment Statistics:')
        self.stdout.write(f'   Total payments: {total_payments}')
        self.stdout.write(f'   Successful: {successful_payments}')
        self.stdout.write(f'   Failed: {failed_payments}')
        self.stdout.write(f'   Pending: {pending_payments}')
        self.stdout.write(f'   Refunded: {refunded_payments}')
        self.stdout.write(f'   Total revenue: ${total_revenue}')

        if successful_payments > 0:
            success_rate = (successful_payments / (total_payments - pending_payments)) * 100
            self.stdout.write(f'   Success rate: {success_rate:.1f}%')
