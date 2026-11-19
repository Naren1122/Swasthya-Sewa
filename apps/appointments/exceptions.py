"""
Domain Exceptions for Appointments and Slot Reservation Engine.
"""

class BookingError(Exception):
    """Base exception for all appointment booking errors."""
    pass

class SlotUnavailableError(BookingError):
    """Raised when a time slot has already been claimed by another patient."""
    pass

class SelfBookingError(BookingError):
    """Raised when a doctor attempts to book a consultation with themselves."""
    pass

class DoctorUnavailableError(BookingError):
    """Raised when the doctor has no shift or is on approved leave on the target date."""
    pass

class AppointmentExpiredError(BookingError):
    """Raised when an action is attempted on an appointment whose hold window expired."""
    pass
