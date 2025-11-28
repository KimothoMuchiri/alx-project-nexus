from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, CartItemListCreateView, CartItemDetailView, CheckoutView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),

    path('cart/', CartItemListCreateView.as_view(), name='cart-list-create'),
    path('cart/<int:pk>/', CartItemDetailView.as_view(), name='cart-detail'),

    path('checkout/', CheckoutView.as_view(), name='checkout'),
]