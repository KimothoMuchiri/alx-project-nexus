from django.urls import path
from .views import RegisterView, CustomerProfileView  

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', CustomerProfileView.as_view(), name='profile'),
]
