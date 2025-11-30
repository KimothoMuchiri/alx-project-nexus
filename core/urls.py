from django.urls import path
from .views import SecurityDashboardView

app_name = "core"

urlpatterns = [
    path('dashboard/', SecurityDashboardView.as_view(), name='security-dashboard'),
]
