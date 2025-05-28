import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
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
    last_login_attempt = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service', 'is_active']),
            models.Index(fields=['is_active', 'current_users']),
        ]

    def __str__(self):
        return f"{self.service.name} - {self.username}"

    def can_assign_user(self):
        """Check if this login service can handle more users"""
        return self.is_active and self.current_users < self.max_concurrent_users

    def get_available_slots(self):
        """Get number of available user slots"""
        return max(0, self.max_concurrent_users - self.current_users)

    def increment_users(self):
        """Increment current users count"""
        if self.current_users < self.max_concurrent_users:
            self.current_users += 1
            self.save(update_fields=['current_users'])
        else:
            raise ValidationError("Maximum concurrent users reached")

    def decrement_users(self):
        """Decrement current users count"""
        if self.current_users > 0:
            self.current_users -= 1
            self.save(update_fields=['current_users'])

class UserService(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    login_service = models.ForeignKey(LoginService, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'service']
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['status', 'assigned_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.service.name}"

    @property
    def is_active(self):
        """Backward compatibility property"""
        return self.status == 'active'

    def activate(self):
        """Activate user service and assign login service"""
        if self.status != 'active':
            # Find available login service
            available_login_service = LoginService.objects.filter(
                service=self.service,
                is_active=True,
                current_users__lt=models.F('max_concurrent_users')
            ).first()

            if available_login_service:
                self.login_service = available_login_service
                self.status = 'active'
                available_login_service.increment_users()
                self.save()
                return True
            else:
                raise ValidationError("No available login service slots")
        return False

    def deactivate(self):
        """Deactivate user service"""
        if self.status == 'active' and self.login_service:
            self.login_service.decrement_users()
            self.status = 'inactive'
            self.save()

    def record_access(self):
        """Record user access to this service"""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])

class Cookie(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid'),
        ('pending_validation', 'Pending Validation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_service = models.ForeignKey(UserService, on_delete=models.CASCADE, related_name='cookies')
    cookie_data = models.JSONField()
    session_id = models.CharField(max_length=255, null=True, blank=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_validated = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_validation')
    validation_attempts = models.IntegerField(default=0)

    class Meta:
        ordering = ['-extracted_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['user_service', 'status']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Cookie for {self.user_service} - {self.status}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if cookie is valid and not expired"""
        return self.status == 'valid' and not self.is_expired()

    def mark_as_expired(self):
        """Mark cookie as expired"""
        self.status = 'expired'
        self.save(update_fields=['status'])

    def validate_cookie(self):
        """Validate cookie and update status"""
        self.validation_attempts += 1
        self.last_validated = timezone.now()

        if self.is_expired():
            self.status = 'expired'
        else:
            # Here you would implement actual cookie validation logic
            # For now, we'll assume validation passes
            self.status = 'valid'

        self.save(update_fields=['status', 'validation_attempts', 'last_validated'])
        return self.status == 'valid'

class CookieInjectionLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('expired', 'Cookie Expired'),
        ('invalid', 'Invalid Cookie'),
        ('access_denied', 'Access Denied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cookie = models.ForeignKey(Cookie, on_delete=models.CASCADE, related_name='injection_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    injection_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['injection_status', 'timestamp']),
            models.Index(fields=['cookie', 'injection_status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.injection_status} - {self.timestamp}"

class CookieExtractionJob(models.Model):
    """Model to track cookie extraction jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login_service = models.ForeignKey(LoginService, on_delete=models.CASCADE, related_name='extraction_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    extracted_cookies_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['login_service', 'status']),
        ]

    def __str__(self):
        return f"Extraction job for {self.login_service} - {self.status}"
