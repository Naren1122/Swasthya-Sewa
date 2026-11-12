import pytest
from django.core.exceptions import ValidationError
from apps.accounts.validators import PasswordComplexityValidator


class TestPasswordComplexityValidator:
    """Tests for hospital-grade password complexity rules."""

    def setup_method(self):
        self.validator = PasswordComplexityValidator()

    def test_valid_strong_password_passes(self):
        # Meets all criteria: >=8 chars, uppercase, lowercase, digit, special char
        self.validator.validate('MediCore#2026!')

    def test_missing_uppercase_fails(self):
        with pytest.raises(ValidationError, match='uppercase letter'):
            self.validator.validate('medicore#2026!')

    def test_missing_lowercase_fails(self):
        with pytest.raises(ValidationError, match='lowercase letter'):
            self.validator.validate('MEDICORE#2026!')

    def test_missing_digit_fails(self):
        with pytest.raises(ValidationError, match='digit'):
            self.validator.validate('MediCore#Pass!')

    def test_missing_special_character_fails(self):
        with pytest.raises(ValidationError, match='special character'):
            self.validator.validate('MediCore2026Pass')

