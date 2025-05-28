Summary of Your Group Buy SEO/AI Tools Platform
Business Concept
You're building a group buy platform for SEO and AI tools where multiple users share access to premium services through pooled subscriptions, reducing individual costs.
Core User Roles
• Users/Members: Customers who purchase subscription plans to access AI/SEO tools
• Admins/Moderators: Platform managers who handle service credentials and access
• Django Superadmin: System-level administration
User Journey

1. Login & Browse: Users log into the platform and see a catalog of available AI/SEO services
2. Plan Selection: Users choose from three subscription tiers:
   o Individual Plan: Access to 1 service
   o 5-Service Plan: Access to 5 services
   o 15-Service Plan: Access to 15 services
3. Purchase & Request: After payment, the system creates a service access request for the admin panel
4. Service Access: Verified users with active paid subscriptions can request cookie data for their subscribed services
   Admin Workflow
5. Service Management: Admins receive user subscription requests and see which services need to be provisioned
6. Credential Setup: Admins add login credentials for each AI/SEO tool in the system
7. Automated Login: Background processes automatically log into the actual AI tool websites using stored credentials
8. Cookie Extraction: The system extracts and stores authentication cookies from successful logins
9. User Distribution: Valid cookies are made available to users who have purchased access to those specific services
   Technical Architecture
   • Multi-subscription Support: Users can purchase multiple plans simultaneously
   • Automated Cookie Management: Background processes handle login automation and cookie extraction
   • Access Control: Proper verification ensures only paying, active users get service access
   • Scalable Design: System can handle multiple concurrent users sharing the same service credentials
   Value Proposition
   Users get affordable access to expensive AI/SEO tools through shared accounts, while the platform handles all the technical complexity of credential management and access distribution.



# Group Buy SEO/AI Tools - Software Architecture

## Overview

This architecture supports a group buy platform where users can purchase subscription plans to access various AI/SEO tools through shared credentials and cookie-based authentication.

## Improved Django Models

### User Management

```python
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import *
import uuid

class User(AbstractBaseUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = EmailField(unique=True)
    full_name = CharField(max_length=100)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    is_verified = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    last_login = DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def has_active_subscription(self):
        return self.user_subscriptions.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).exists()

    def get_accessible_services(self):
        """Get all services user has access to through active subscriptions"""
        active_subscriptions = self.user_subscriptions.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        )
        service_ids = set()
        for sub in active_subscriptions:
            service_ids.update(sub.subscription.services.values_list('id', flat=True))
        return Service.objects.filter(id__in=service_ids)
```

### Service Management

```python
class Service(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=50, unique=True)  # e.g., "ChatGPT", "Claude", "SEMRush"
    display_name = CharField(max_length=100)  # User-friendly name
    login_url = URLField()
    description = TextField()
    logo_url = URLField(null=True, blank=True)
    category = CharField(max_length=30, choices=[
        ('ai_chat', 'AI Chat'),
        ('ai_image', 'AI Image'),
        ('seo', 'SEO Tools'),
        ('analytics', 'Analytics'),
        ('other', 'Other')
    ])
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name
```

### Subscription Plans

```python
class SubscriptionPlan(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=50)  # "Individual", "5-Service Pack", "15-Service Pack"
    description = TextField()
    price = DecimalField(max_digits=8, decimal_places=2)
    duration_days = IntegerField()
    max_services = IntegerField()  # 1, 5, 15
    services = ManyToManyField(Service, blank=True)  # Available services in this plan
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"
```

### User Subscriptions (Bridge Table)

```python
class UserSubscription(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=CASCADE, related_name='user_subscriptions')
    subscription = ForeignKey(SubscriptionPlan, on_delete=CASCADE)
    payment = ForeignKey('Payment', on_delete=CASCADE)

    # Subscription status
    is_active = BooleanField(default=True)
    purchased_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()

    # Selected services (for plans that allow choice)
    selected_services = ManyToManyField(Service, blank=True)

    class Meta:
        unique_together = ['user', 'subscription', 'payment']

    def is_expired(self):
        return timezone.now() > self.expires_at
```

### Payment Management

```python
class Payment(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=CASCADE, related_name='payments')
    subscription_plan = ForeignKey(SubscriptionPlan, on_delete=CASCADE)

    amount = DecimalField(max_digits=10, decimal_places=2)
    payment_status = CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ])
    payment_method = CharField(max_length=30, choices=[
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency')
    ])

    transaction_id = CharField(max_length=255, unique=True)
    payment_date = DateTimeField(auto_now_add=True)

    # Additional payment metadata
    payment_metadata = JSONField(default=dict, blank=True)
```

### Service Credentials Management

```python
class LoginService(models.Model):
    """Admin-managed credentials for each service"""
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = ForeignKey(Service, on_delete=CASCADE, related_name='login_credentials')

    # Credential information
    username = CharField(max_length=100)
    encrypted_password = TextField()  # Encrypted password
    additional_credentials = JSONField(default=dict, blank=True)  # API keys, etc.

    # Status and management
    is_active = BooleanField(default=True)
    max_concurrent_users = IntegerField(default=5)
    current_users = IntegerField(default=0)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_login_attempt = DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.service.name} - {self.username}"
```

### Cookie Management

```python
class UserService(models.Model):
    """Bridge table for user access to specific services"""
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=CASCADE, related_name='user_services')
    service = ForeignKey(Service, on_delete=CASCADE)
    login_service = ForeignKey(LoginService, on_delete=CASCADE, null=True, blank=True)

    # Access management
    is_active = BooleanField(default=True)
    assigned_at = DateTimeField(auto_now_add=True)
    last_accessed = DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'service']

class Cookie(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_service = ForeignKey(UserService, on_delete=CASCADE, related_name='cookies')

    # Cookie data
    cookie_data = JSONField()  # Encrypted cookie blob
    session_id = CharField(max_length=255, null=True, blank=True)

    # Timing
    extracted_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    last_validated = DateTimeField(null=True, blank=True)

    # Status
    status = CharField(max_length=20, choices=[
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid')
    ])

    def is_expired(self):
        return timezone.now() > self.expires_at

class CookieInjectionLog(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cookie = ForeignKey(Cookie, on_delete=CASCADE, related_name='injection_logs')
    user = ForeignKey(User, on_delete=CASCADE)

    injection_status = CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('expired', 'Cookie Expired'),
        ('invalid', 'Invalid Cookie')
    ])
    message = TextField()
    timestamp = DateTimeField(auto_now_add=True)
    ip_address = GenericIPAddressField(null=True, blank=True)
```

## User Flow Architecture

### 1. User Registration & Purchase Flow

```python
# User views available subscription plans
subscription_plans = SubscriptionPlan.objects.filter(is_active=True)

# User selects a plan and completes payment
payment = Payment.objects.create(
    user=user,
    subscription_plan=selected_plan,
    amount=selected_plan.price,
    payment_status='pending'
)

# After successful payment, create UserSubscription
user_subscription = UserSubscription.objects.create(
    user=user,
    subscription=selected_plan,
    payment=payment,
    expires_at=timezone.now() + timedelta(days=selected_plan.duration_days)
)

# For plans with service selection, allow user to choose services
if selected_plan.max_services > 1:
    # User selects up to max_services from available services
    user_subscription.selected_services.set(selected_services)
```

### 2. Admin Service Management Flow

```python
# Admin adds credentials for a service
login_service = LoginService.objects.create(
    service=service,
    username="admin_username",
    encrypted_password=encrypt_password("password"),
    max_concurrent_users=10
)

# Background task extracts cookies
def extract_cookies_task(login_service_id):
    login_service = LoginService.objects.get(id=login_service_id)
    # Automated login process
    cookies = perform_automated_login(login_service)

    # Save cookies for users who have access to this service
    users_with_access = get_users_with_service_access(login_service.service)
    for user in users_with_access:
        user_service, created = UserService.objects.get_or_create(
            user=user,
            service=login_service.service,
            defaults={'login_service': login_service}
        )

        Cookie.objects.create(
            user_service=user_service,
            cookie_data=encrypt_cookies(cookies),
            expires_at=timezone.now() + timedelta(hours=24)
        )
```

### 3. User Service Access Flow

```python
# User requests access to a service
def get_service_access(user, service):
    # Check if user has active subscription for this service
    accessible_services = user.get_accessible_services()
    if service not in accessible_services:
        raise PermissionDenied("No active subscription for this service")

    # Get or create UserService
    user_service, created = UserService.objects.get_or_create(
        user=user,
        service=service
    )

    # Get valid cookie
    valid_cookie = user_service.cookies.filter(
        status='valid',
        expires_at__gt=timezone.now()
    ).first()

    if not valid_cookie:
        # Request new cookie extraction
        schedule_cookie_extraction.delay(user_service.id)
        return None

    return valid_cookie.cookie_data
```

## API Endpoints Structure

### User Endpoints

- `GET /api/services/` - List all available services
- `GET /api/subscription-plans/` - List available subscription plans
- `POST /api/purchase/` - Purchase a subscription plan
- `GET /api/my-subscriptions/` - User's active subscriptions
- `GET /api/my-services/` - User's accessible services
- `GET /api/service/{service_id}/access/` - Request service access/cookies

### Admin Endpoints

- `GET /api/admin/services/` - Manage services
- `POST /api/admin/services/{service_id}/credentials/` - Add service credentials
- `GET /api/admin/login-services/` - Manage login credentials
- `POST /api/admin/extract-cookies/{login_service_id}/` - Trigger cookie extraction
- `GET /api/admin/users/` - User management
- `GET /api/admin/subscriptions/` - Subscription management

## Background Tasks (Celery)

```python
@shared_task
def extract_cookies_for_service(login_service_id):
    """Extract cookies for a service and distribute to users"""
    pass

@shared_task
def validate_existing_cookies():
    """Check if existing cookies are still valid"""
    pass

@shared_task
def cleanup_expired_data():
    """Clean up expired cookies and subscriptions"""
    pass

@shared_task
def send_subscription_expiry_notifications():
    """Notify users of upcoming subscription expiry"""
    pass
```

## Security Considerations

1. **Encryption**: All passwords and cookie data should be encrypted
2. **Rate Limiting**: Implement rate limiting on cookie requests
3. **Session Management**: Proper session handling for concurrent users
4. **Audit Logging**: Log all admin actions and user access
5. **IP Restrictions**: Optional IP-based access controls
6. **Two-Factor Authentication**: For admin accounts

## Database Indexes

```python
# Add these to your models for better performance
class Meta:
    indexes = [
        models.Index(fields=['user', 'is_active']),  # UserSubscription
        models.Index(fields=['expires_at', 'status']),  # Cookie
        models.Index(fields=['service', 'is_active']),  # LoginService
        models.Index(fields=['payment_status', 'payment_date']),  # Payment
    ]
```

This architecture provides a scalable foundation for your group buy platform with proper separation of concerns, user access management, and admin control over service credentials and cookie distribution.

Frontend Authentication Setup: Workflow
To achieve robust, secure, and modular user session management in your Next.js app, here’s what needs to be done:

1. Session Management & Token Handling

• Use cookies (not localStorage) for storing tokens, with httpOnly and secure flags.
• Use a session manager to read/write tokens and user info from cookies.
• On login, set tokens in cookies and session manager.
• On logout, clear cookies and session manager.
• All API requests should include the access token in the Authorization header.

2. API Interceptors

• Use Axios interceptors to automatically attach tokens to requests and handle token refresh on 401 errors.

3. React Query & Providers

• Use TanStack Query for all data fetching, with a global provider.
• Use AuthProvider and NotificationProvider for authentication state and user feedback.
• Use a modular context/provider structure.

4. Security Enhancements

• Use httpOnly, secure, and sameSite=strict cookies for tokens.
• Never expose tokens to JavaScript if possible.
• Refresh tokens automatically before expiry.
