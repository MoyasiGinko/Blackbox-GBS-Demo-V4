from django.urls import path
from .views import CookieListView

urlpatterns = [
    path('cookies/', CookieListView.as_view(), name='cookie-list'),
]
