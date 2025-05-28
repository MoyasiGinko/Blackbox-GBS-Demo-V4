import uuid
from django.db import models

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('ai_chat', 'AI Chat'),
        ('ai_image', 'AI Image'),
        ('seo', 'SEO Tools'),
        ('analytics', 'Analytics'),
        ('writing', 'Writing Tools'),
        ('social_media', 'Social Media'),
        ('design', 'Design Tools'),
        ('other', 'Other')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    login_url = models.URLField()
    description = models.TextField()
    logo_url = models.URLField(null=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
