from rest_framework import serializers
from .models import Category, Product, CartItem, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'sku',
            'description',
            'price',
            'discount_price',
            'stock',
            'is_active',
            'created_at',
            'updated_at',
            'category',
            'category_id',
        ]
    def validate_stock(self, value):
        if value <0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def validate(self, attrs):
        """
        Cross-field validation:
        - price >= 0
        - discount_price >= 0
        - discount_price <= price (if provided)
        """
        price = attrs.get('price', getattr(self.instance, 'price', None))
        discount_price = attrs.get('discount_price', getattr(self.instance, 'discount_price', None))

        if price is not None and price < 0:
            raise serializers.ValidationError({"price": "Price cannot be negative."})

        if discount_price is not None:
            if discount_price < 0:
                raise serializers.ValidationError({"discount_price": "Discount price cannot be negative."})
            if price is not None and discount_price > price:
                raise serializers.ValidationError(
                    {"discount_price": "Discount price cannot be greater than price."}
                )

        return attrs

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source='product',
        write_only=True,
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'quantity',
            'created_at',
            'updated_at',
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price_at_purchase']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'created_at', 'updated_at', 'items']
