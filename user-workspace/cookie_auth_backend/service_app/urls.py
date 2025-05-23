from django.urls import path
from .views import ServiceListCreateView, UserServiceListView

urlpatterns = [
    path('services/', ServiceListCreateView.as_view(), name='service-list-create'),
    path('user-services/', UserServiceListView.as_view(), name='user-service-list'),
]
