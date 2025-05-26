import uuid
from django.db import models
from auth_app.models import User
from subscription_app.models import SubscriptionPlan

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Payment {self.id} - {self.payment_status}"
