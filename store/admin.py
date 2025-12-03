from django.contrib import admin

from .models import Category, Product, CartItem, Order, OrderItem, OrderReminder

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "created_at")
    search_fields = ("user__username", "product__name")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price_at_purchase")

@admin.register(OrderReminder)
class OrderReminderAdmin(admin.ModelAdmin):
    list_display = ("order", "sent_at")
