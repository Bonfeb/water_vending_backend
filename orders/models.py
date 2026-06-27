from django.db import models
from django.conf import settings


class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('purchase', 'New Bottle Purchase'),
        ('refill', 'Water Refill'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('preparing', 'Preparing'),
        ('dispatched', 'Dispatched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Authenticated user or null for guest
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        blank=True, null=True
    )
    # Guest info (used when user is null)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)

    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    # Optional — even for refills, user may use their own non-business bottle
    bottle = models.ForeignKey(
        'products.Bottle',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True, blank=True
    )
    size = models.IntegerField(choices=[(5, '5L'), (10, '10L'), (20, '20L')])
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt = models.CharField(max_length=50, blank=True, null=True)
    payment_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField()
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"Order #{self.id} - {self.user.phone_number}"
        return f"Order #{self.id} - {self.guest_name} (Guest)"

    @property
    def customer_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.guest_name or ''

    @property
    def customer_phone(self):
        if self.user:
            return self.user.phone_number
        return self.guest_phone or ''