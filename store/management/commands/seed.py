from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal
import random

from accounts.models import User, CustomerProfile
from store.models import Category, Product


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, users, and customer profiles."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding database..."))

        self._reset_users()
        CustomerProfile.objects.all().delete() 
        self.create_users_and_profiles()
        self.create_categories_and_products()

        self.stdout.write(self.style.SUCCESS("Seeding completed."))

    # ---------- USERS + PROFILES ----------

    def _reset_users(self):
        """
        Delete all non-superuser accounts (their profiles will cascade).
        Keep any superusers you created manually.
        """
        # This will delete store_manager, customer1..customerN, etc.
        deleted_count, _ = User.objects.filter(is_superuser=False).delete()
        self.stdout.write(
            self.style.WARNING(f"Deleted {deleted_count} non-superuser users.")
        )

    def create_users_and_profiles(self):
        """
        Create a store manager and 5 sample customers, plus a CustomerProfile
        for each user (manager + customers).
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
            self.stdout.write(
                self.style.SUCCESS(f"Created store manager user: {manager_username}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Store manager '{manager_username}' already exists.")
            )

        # Ensure profile for store manager
        self._ensure_profile_for_user(manager, is_manager=True)

        # 5 Customers: customer1 .. customer10
        for i in range(1, 11):
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
                self.stdout.write(
                    self.style.WARNING(f"Customer '{username}' already exists.")
                )

            # Ensure profile for each customer
            self._ensure_profile_for_user(customer, index=i)

    def _ensure_profile_for_user(self, user, is_manager=False, index=None):
        """
        Create a CustomerProfile for a user if it doesn't exist.
        """
        # fake data pools
        streets = [
            "Moi Avenue",
            "Kenyatta Avenue",
            "Kampala Road",
            "Thika Road",
            "Mombasa Road",
            "Lilongwe street",
            "Aswan avenue"
        ]
        cities = ["Nairobi", "Kampala", "Kisumu", "Nakuru", "Eldoret", "Lilongwe", "Cairo"]
        countries = ["Kenya", "Uganda", "Kenya", "Kenya", "Egypt", "Zimbambwe"]  

        profile, created = CustomerProfile.objects.update_or_create(
            user=user,
            defaults={
                "phone_number": self._generate_phone_number(is_manager=is_manager, index=index),
                "address_line1": f"{random.randint(1, 999)} {random.choice(streets)}",
                "address_line2": "Apartment " + str(random.randint(1, 50)),
                "city": random.choice(cities),
                "country": random.choice(countries),
                "postal_code": f"{random.randint(10000, 99999)}",
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created CustomerProfile for user: {user.username}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"CustomerProfile already exists for user: {user.username}"
                )
            )

    def _generate_phone_number(self, is_manager=False, index=None):
        """
        Generate a simple Kenya-style phone number string.
        """
        if is_manager:
            # Manager gets a fixed number
            return "+254700000001"
        if index is not None:
            # Use index to make numbers more predictable per customer
            return f"+2547{index}{random.randint(1000000, 9999999)}"
        # Fallback random
        return f"+2547{random.randint(10000000, 99999999)}"

    # ---------- CATEGORIES + PRODUCTS ----------

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
                self.stdout.write(
                    self.style.WARNING(f"Category '{name}' already exists.")
                )

        if not category_objects:
            self.stdout.write(
                self.style.WARNING("No categories available to create products.")
            )
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
                        self.style.WARNING(
                            f"Product '{name}' already exists in {category.name}."
                        )
                    )
