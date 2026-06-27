from django.db import models
from django.conf import settings
import uuid


class Bottle(models.Model):
    SIZE_CHOICES = [
        (5, '5 Litres'),
        (10, '10 Litres'),
        (20, '20 Litres'),
    ]

    size = models.IntegerField(choices=SIZE_CHOICES)
    purchase_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.size} - {self.id}"

class Pricing(models.Model):
    size = models.IntegerField(choices=Bottle.SIZE_CHOICES, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    refill_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return (
            f"{self.get_size_display()} - "
            f"Purchase: KES {self.purchase_price}, Refill: KES {self.refill_price}"
        )