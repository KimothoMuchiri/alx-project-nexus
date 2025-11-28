from rest_framework import generics, status,  viewsets, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter, SearchFilter
from .models import Category, Product, CartItem, Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer,  CartItemSerializer, OrderSerializer
from .permissions import IsAdminOrManagerOrReadOnly, IsCustomer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['name']
    search_fields = ['name', 'description']


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['price', 'created_at']
    search_fields = ['name', 'description', 'sku']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

class CartItemListCreateView(generics.ListCreateAPIView):
    """
    GET: list current user's cart items
    POST: add/update item in current user's cart
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related('product')

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        # Check stock before adding
        if product.stock < quantity:
            raise serializers.ValidationError("Not enough stock available.")

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                raise serializers.ValidationError("Not enough stock for this quantity.")
            cart_item.quantity = new_quantity
            cart_item.save()
        return cart_item

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related('product')

class CheckoutView(generics.GenericAPIView):
    """
    Convert the current user's cart into an order.
    """
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = OrderSerializer

    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user).select_related('product')

        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Check all stock first
        for item in cart_items:
            if item.quantity > item.product.stock:
                return Response(
                    {"detail": f"Not enough stock for {item.product.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 2. Create order
        order = Order.objects.create(
            user=user,
            status=Order.Status.PENDING,
            total_amount=0
        )
        total = 0

        for item in cart_items:
            product = item.product
            price = product.discount_price or product.price
            total += price * item.quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price_at_purchase=price,
            )

            product.stock -= item.quantity
            product.save()

        order.total_amount = total
        order.status = Order.Status.PAID
        order.save()

        # Clear cart
        cart_items.delete()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)