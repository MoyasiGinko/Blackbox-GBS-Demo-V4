from django.db import models
from django.db.models import JSONField
from django.conf import settings
import uuid

class UserService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    credentials = JSONField()  # encrypted
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.service.name}"

class Cookie(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_service = models.ForeignKey(UserService, on_delete=models.CASCADE)
    cookie_data = JSONField()  # encrypted cookie blob
    extracted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Cookie for {self.user_service.user.email} - {self.user_service.service.name}"

class CookieInjectionLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cookie = models.ForeignKey(Cookie, on_delete=models.CASCADE)
    injection_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Injection {self.injection_status} for cookie {self.cookie.id}"
