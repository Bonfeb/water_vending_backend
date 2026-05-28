from django.db import models
import uuid
from users.models import *


class Bottle(models.Model):
    SIZE_CHOICES = [
        (5, '5 Litres'),
        (10, '10 Litres'),
        (20, '20 Litres'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bottles')
    size = models.IntegerField(choices=SIZE_CHOICES)
    purchase_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.size}L"


class Pricing(models.Model):
    size = models.IntegerField(choices=Bottle.SIZE_CHOICES, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    refill_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.size}L - Purchase: KES {self.purchase_price}, Refill: KES {self.refill_price}"