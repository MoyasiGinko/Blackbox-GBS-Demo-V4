from django.contrib import admin
from .models import User, Service, Subscription, Payment
from .models_part2 import UserService, Cookie, CookieInjectionLog

admin.site.register(User)
admin.site.register(Service)
admin.site.register(Subscription)
admin.site.register(Payment)
admin.site.register(UserService)
admin.site.register(Cookie)
admin.site.register(CookieInjectionLog)
