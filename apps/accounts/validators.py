import re
from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    """
    Enforces healthcare-grade password complexity rules:
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*...)
    """

    def validate(self, password: str, user=None):
        errors = []

        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter (A-Z).')

        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter (a-z).')

        if not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one digit (0-9).')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=~`\[\]/\\]', password):
            errors.append('Password must contain at least one special character (!@#$%^&*...).')

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            'Your password must contain at least one uppercase letter, '
            'one lowercase letter, one digit, and one special character.'
        )

