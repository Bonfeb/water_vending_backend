from django.utils import timezone
from users.models import User


def create_notification(user, title, message):
    from riders.models import Notification
    return Notification.objects.create(
        user=user,
        title=title,
        message=message
    )


def notify_admin(title, message):
    admin = User.objects.filter(is_admin=True).first()
    if admin:
        return create_notification(admin, title, message)
    return None


def notify_rider(rider, title, message):
    return create_notification(rider, title, message)


def notify_customer(customer, title, message):
    return create_notification(customer, title, message)