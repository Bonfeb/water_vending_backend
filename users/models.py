from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"

    @property
    def is_admin(self):
        return self.groups.filter(name='staff').exists()

    @property
    def is_customer(self):
        return self.groups.filter(name='customers').exists()