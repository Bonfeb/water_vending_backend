from django.db import models
from django.utils import timezone
from users.models import *
from products.models import *


class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('purchase', 'New Bottle Purchase'),
        ('refill', 'Water Refill'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid - Processing'),
        ('assigned', 'Assigned to Rider'),
        ('picked', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    bottle = models.ForeignKey(Bottle, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    size = models.IntegerField(choices=Bottle.SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    payment_phone = models.CharField(max_length=15)
    delivery_address = models.TextField()
    delivery_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.phone_number}"