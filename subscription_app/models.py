import uuid
from django.db import models
from django.utils import timezone
from auth_app.models import User
from service_app.models import Service

class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.IntegerField()
    max_services = models.IntegerField()
    services = models.ManyToManyField(Service, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class UserSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_subscriptions')
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment = models.ForeignKey('payment_app.Payment', on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    selected_services = models.ManyToManyField(Service, blank=True)

    class Meta:
        unique_together = ['user', 'subscription', 'payment']

    def is_expired(self):
        return timezone.now() > self.expires_at
