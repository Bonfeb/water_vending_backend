import re

def standardize_phone_number(phone):
    phone = re.sub(r'[\s\-()]', '', phone.strip())

    if phone.startswith('+254'):
        if re.match(r'^\+2547\d{8}$', phone):
            return phone
    elif phone.startswith('254'):
        if re.match(r'^2547\d{8}$', phone):
            return '+' + phone
    elif phone.startswith('07'):
        if re.match(r'^07\d{8}$', phone):
            return '+254' + phone[1:]
    elif phone.startswith('7'):
        if re.match(r'^7\d{8}$', phone):
            return '+254' + phone

    raise ValueError(
        f"Invalid phone number format: {phone}. "
        "Use format 0712345678 or +254712345678"
    )


def is_valid_phone_number(phone):
    """Check if phone number is a valid Kenyan format."""
    try:
        standardize_phone_number(phone)
        return True
    except ValueError:
        return False