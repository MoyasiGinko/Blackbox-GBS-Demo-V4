import uuid
from django.db import models
from service_app.models import Service
from auth_app.models import User

class LoginService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='login_credentials')
    username = models.CharField(max_length=100)
    encrypted_password = models.TextField()
    additional_credentials = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    max_concurrent_users = models.IntegerField(default=5)
    current_users = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.username}"

class UserService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    login_service = models.ForeignKey(LoginService, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'service']

class Cookie(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_service = models.ForeignKey(UserService, on_delete=models.CASCADE, related_name='cookies')
    cookie_data = models.JSONField()
    session_id = models.CharField(max_length=255, null=True, blank=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_validated = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

class CookieInjectionLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('expired', 'Cookie Expired'),
        ('invalid', 'Invalid Cookie')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cookie = models.ForeignKey(Cookie, on_delete=models.CASCADE, related_name='injection_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    injection_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
