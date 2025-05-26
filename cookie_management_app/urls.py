from django.urls import path
from .views import AddLoginServiceView, GetCookieDataView

urlpatterns = [
    path('login_services/add/', AddLoginServiceView.as_view(), name='loginservice-add'),
    path('cookies/<uuid:pk>/', GetCookieDataView.as_view(), name='cookie-detail'),
]
