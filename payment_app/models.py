import uuid
from django.db import models
from django.utils import timezone
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

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['payment_status', 'payment_date']),
            models.Index(fields=['payment_method', 'payment_status']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.payment_status}"

    def is_successful(self):
        """Check if payment was successful."""
        return self.payment_status == 'success'

    def is_refundable(self):
        """Check if payment can be refunded."""
        return self.payment_status == 'success'

    def is_pending(self):
        """Check if payment is still pending."""
        return self.payment_status == 'pending'

    def days_since_payment(self):
        """Get number of days since payment was made."""
        delta = timezone.now() - self.payment_date
        return delta.days

    def get_refund_amount(self):
        """Get refunded amount from metadata."""
        return float(self.payment_metadata.get('refund_amount', 0))

    def get_gateway_fee(self):
        """Get payment gateway fee from metadata."""
        return float(self.payment_metadata.get('gateway_fee', 0))

    def mark_as_expired(self):
        """Mark pending payment as failed if too old."""
        if self.is_pending() and self.days_since_payment() > 1:
            self.payment_status = 'failed'
            self.payment_metadata.update({
                'failure_reason': 'Payment expired',
                'expired_at': timezone.now().isoformat()
            })
            self.save()
            return True
        return False
