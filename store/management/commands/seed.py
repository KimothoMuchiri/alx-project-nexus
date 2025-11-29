from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal
import random

from accounts.models import User
from store.models import Category, Product


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, and users."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding database..."))

        self.create_users()
        self.create_categories_and_products()

        self.stdout.write(self.style.SUCCESS("Seeding completed."))

    def create_users(self):
        """
        Create a store manager and 5 sample customers, if they don't exist.
        """

        # Store Manager
        manager_username = "store_manager"
        manager_email = "manager@example.com"

        manager, created = User.objects.get_or_create(
            username=manager_username,
            defaults={
                "email": manager_email,
            },
        )
        if created:
            manager.set_password("password123")
            manager.role = User.Roles.STORE_MANAGER
            manager.is_staff = True
            manager.save()
            self.stdout.write(self.style.SUCCESS(f"Created store manager user: {manager_username}"))
        else:
            self.stdout.write(f"Store manager '{manager_username}' already exists.")

        # 5 Customers: customer1 .. customer5
        for i in range(1, 6):
            username = f"customer{i}"
            email = f"{username}@example.com"

            customer, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                },
            )
            if created:
                customer.set_password("password123")
                customer.role = User.Roles.CUSTOMER
                customer.save()
                self.stdout.write(self.style.SUCCESS(f"Created customer user: {username}"))
            else:
                self.stdout.write(f"Customer '{username}' already exists.")

    def create_categories_and_products(self):
        """
        Create 5 categories and about 50 products (10 per category).
        """
        Product.objects.all().delete()
        self.stdout.write(self.style.WARNING("Deleted all existing products."))

        categories_data = [
            "Electronics",
            "Home & Kitchen",
            "Books",
            "Fashion",
            "Sports & Outdoors",
        ]

        category_objects = []

        # Create or get categories
        for name in categories_data:
            slug = slugify(name)
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"Sample category for {name}",
                },
            )
            category_objects.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))
            else:
                self.stdout.write(f"Category '{name}' already exists.")

        if not category_objects:
            self.stdout.write(self.style.WARNING("No categories available to create products."))
            return

        # For each category, create 10 products
        for category in category_objects:
            for i in range(1, 11):  # 10 products per category
                name = f"{category.name} Product {i}"
                slug = slugify(f"{category.name}-{i}")  # ensures uniqueness per category

                # Deterministic SKU: prefix from category slug + index
                cat_prefix = category.slug[:5].upper()  # e.g. ELECT, HOME-, BOOKS
                sku = f"SKU-{cat_prefix}-{i:03d}"       # e.g. SKU-ELECT-001

                price = Decimal(random.randint(10, 500))
                # Discount: either None or a valid lower price
                if random.random() < 0.5:
                    discount_percent = random.randint(5, 40)  # 5% to 40% off
                    multiplier = Decimal(100 - discount_percent) / Decimal(100)
                    discount_price = (price * multiplier).quantize(Decimal("0.01"))
                else:
                    discount_price = None
                stock = random.randint(5, 50)

                product, created = Product.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "category": category,
                        "name": name,
                        "sku": sku,
                        "description": f"Sample product: {name}",
                        "price": price,
                        "discount_price": discount_price,
                        "stock": stock,
                        "is_active": True,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created product: {name} in {category.name}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Product '{name}' already exists in {category.name}."
                    )
