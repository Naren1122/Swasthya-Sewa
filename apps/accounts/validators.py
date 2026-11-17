import re
from django.core.exceptions import ValidationError

# Blocklist of reserved testing and disposable temporary email domains
BLOCKED_EMAIL_DOMAINS = {
    # Reserved dummy/test domains
    'example.com',
    'example.org',
    'example.net',
    'test.com',
    'sample.com',
    'sample.net',
    'invalid.com',
    'invalid.org',
    'localhost',
    # Disposable / temporary email providers
    'mailinator.com',
    'tempmail.com',
    'temp-mail.org',
    '10minutemail.com',
    'guerrillamail.com',
    'throwawaymail.com',
    'yopmail.com',
    'sharklasers.com',
    'trashmail.com',
    'dispostable.com',
    'getairmail.com',
}

def validate_email_domain(email: str) -> None:
    """
    Validates that the email does not belong to a reserved test domain
    or a disposable/temporary email provider.
    """
    if not email or '@' not in email:
        raise ValidationError("Please provide a valid email address.")

    domain = email.split('@')[-1].lower().strip()
    if domain in BLOCKED_EMAIL_DOMAINS:
        raise ValidationError(
            f"Registration with '@{domain}' is not permitted. Please use a valid, permanent email address."
        )


def validate_password_complexity(password: str) -> None:
    """
    Validates that a password satisfies strict complexity requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&* etc.)
    """
    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("at least one uppercase letter (A-Z)")
    if not re.search(r'[a-z]', password):
        errors.append("at least one lowercase letter (a-z)")
    if not re.search(r'[0-9]', password):
        errors.append("at least one digit (0-9)")
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("at least one special character (!@#$%^&* etc.)")

    if errors:
        raise ValidationError(
            f"Password must contain {', '.join(errors)}."
        )


class ComplexityPasswordValidator:
    """
    Django-compatible password validator for settings.AUTH_PASSWORD_VALIDATORS.
    """
    def validate(self, password, user=None):
        validate_password_complexity(password)

    def get_help_text(self):
        return (
            "Your password must contain at least 8 characters, including at least one uppercase letter, "
            "one lowercase letter, one number, and one special character."
        )
