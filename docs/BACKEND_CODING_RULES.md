# Backend Engineering Standards & Coding Rules
## Production-Grade Architecture, Scalability, Maintainability & Performance

This document establishes the mandatory backend coding standards for **Swasthya-Sewa**. These rules are followed by senior software engineers to ensure the system remains scalable, maintainable, readable, and free of redundant data or dangerous race conditions.

---

## 1. Architecture & Separation of Concerns

### Rule 1.1: "Thin Views, Rich Domain/Service Layer, Dumb Models"
Never place business logic, calculations, or third-party API calls inside Django views or template tags.

* **Views (`views.py`):** Responsible **only** for HTTP protocol concerns (parsing request arguments, calling a service, and returning an HTTP/HTMX response or template).
* **Service Layer (`services.py`):** The brain of the application. Contains all business logic, slot chunking algorithms, state machines, payment signature verifications, and concurrency locks.
* **Models (`models.py`):** Responsible **only** for data schema, field constraints, relationships, and simple data representation (`__str__`).
* **Tasks (`tasks.py`):** Celery background jobs that call services asynchronously.

```python
# ❌ BAD: Business logic and database mutations directly in views
def book_slot_view(request):
    slot_id = request.POST.get('slot_id')
    # Direct DB mutation with race condition in view!
    slot = Slot.objects.get(id=slot_id)
    slot.is_booked = True
    slot.save()
    send_mail(...)  # Synchronous email blocks HTTP thread!
    return render(request, 'success.html')

# ✅ SENIOR APPROACH: View delegates to a dedicated atomic service
@require_POST
@patient_required
def book_slot_view(request):
    form = SlotBookingForm(request.POST)
    if not form.is_valid():
        return render(request, 'partials/booking_error.html', {'errors': form.errors}, status=400)
    
    try:
        # Business logic encapsulated in service layer
        appointment = AppointmentBookingService.hold_slot(
            patient=request.user,
            slot_data=form.cleaned_data
        )
        return render(request, 'partials/payment_modal.html', {'appointment': appointment})
    except SlotUnavailableError as exc:
        return render(request, 'partials/slot_conflict_alert.html', {'message': str(exc)}, status=409)
```

---

## 2. Database Optimization & Query Scalability

### Rule 2.1: The "Zero N+1 Query" Rule
Never evaluate a foreign key or many-to-many relationship inside a template loop or Python iterator without eager loading.

* Use `select_related()` for single-valued relationships (`ForeignKey`, `OneToOneField`).
* Use `prefetch_related()` for multi-valued relationships (`ManyToManyField`, reverse `ForeignKey`).

```python
# ❌ BAD: Triggers 1 query for appointments + N queries for doctor profile + N queries for user!
appointments = Appointment.objects.filter(patient=request.user)
for appt in appointments:
    print(appt.doctor.user.full_name)  # N+1 DB hit on every iteration

# ✅ SENIOR APPROACH: Executes exactly 1 optimized SQL JOIN
appointments = Appointment.objects.filter(patient=request.user).select_related(
    'doctor__user'
).only(
    'id', 'appointment_date', 'start_time', 'status',
    'doctor__user__full_name', 'doctor__department'
)
```

### Rule 2.2: Mandatory Indexing Strategy
Every column used in `filter()`, `exclude()`, `order_by()`, or `JOIN` operations **must** have a database index.
* Always index foreign keys and state fields (`status`, `appointment_date`, `day_of_week`).
* Use **Composite Indexes** for multi-column queries (`doctor_id` + `appointment_date`).
* Use **Partial / Filtered Indexes** to keep index trees compact and fast:
  ```python
  class Meta:
      indexes = [
          models.Index(
              fields=['doctor', 'appointment_date'],
              name='idx_doctor_active_appts',
              condition=models.Q(status__in=['PENDING_PAYMENT', 'CONFIRMED'])
          )
      ]
  ```

### Rule 2.3: Limit & Paginate Every Collection
Never execute an unbounded `.all()` query on tables that grow over time (`Appointments`, `Payments`, `Logs`).
* Always enforce pagination (e.g. 15–25 records per page) with `django.core.paginator` or HTMX infinite scroll.

---

## 3. Data Integrity, Single Source of Truth & Zero Redundancy

### Rule 3.1: Never Store Compute-Derived Data in DB Columns
If a value can be reliably computed from existing columns, **do not store it as a separate database column**. Redundant columns inevitably fall out of sync when updates occur.

```python
# ❌ BAD: Redundant column that causes data inconsistency
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()  # Redundant! User model already has email.
    total_completed_appointments = models.IntegerField(default=0) # Redundant counter!

# ✅ SENIOR APPROACH: Single Source of Truth
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    @property
    def email(self) -> str:
        return self.user.email  # Derived dynamically from User
        
    def get_completed_appointments_count(self) -> int:
        return self.appointments.filter(status='COMPLETED').count()
```

### Rule 3.2: Use Explicit Constraints at the Database Level
Do not rely solely on Python `if` checks to enforce data validity; validate at the PostgreSQL engine level using `CheckConstraint` and `UniqueConstraint`:

```python
class Meta:
    constraints = [
        # Prevent end_time being before start_time
        models.CheckConstraint(
            check=models.Q(end_time__gt=models.F('start_time')),
            name='check_valid_shift_time'
        ),
        # Prevent multiple active bookings for same doctor at same time
        models.UniqueConstraint(
            fields=['doctor', 'appointment_date', 'start_time'],
            condition=models.Q(status__in=['PENDING_PAYMENT', 'CONFIRMED']),
            name='unique_active_slot_per_doctor'
        )
    ]
```

---

## 4. Concurrency, Race Conditions & Idempotency

### Rule 4.1: Pessimistic Locking on Finite Resources
Whenever two users can contend for the same finite resource (e.g., booking the same 10:20 AM slot), always execute the state change inside a database transaction with `select_for_update()`:

```python
from django.db import transaction

def reserve_slot_atomic(doctor, date, time_slot, patient):
    with transaction.atomic():
        # Acquire row lock; blocks any concurrent transaction attempting to read with lock
        existing_booking = Appointment.objects.select_for_update().filter(
            doctor=doctor,
            appointment_date=date,
            start_time=time_slot,
            status__in=['CONFIRMED', 'PENDING_PAYMENT']
        ).first()

        if existing_booking:
            raise SlotUnavailableError("Slot is no longer available.")

        return Appointment.objects.create(...)
```

### Rule 4.2: Idempotent Payment & Webhook Handlers
A webhook or payment callback might be delivered multiple times by eSewa or Khalti due to network retries.
* Every payment transaction must have a unique `transaction_uuid`.
* The callback handler must check if the payment is already marked `SUCCESS`; if so, return HTTP 200 immediately without re-triggering business events or sending duplicate confirmation emails.

---

## 5. Code Readability & Maintainability Standards

### Rule 5.1: Strict Typing & Descriptive Names
Every function in the service and utility layers must include **Type Hints** and **Return Types** (PEP 484).

```python
# ❌ BAD: Cryptic abbreviations, no types
def get_sl(d, dt):
    # What is d? Doctor ID? Doctor object? What is dt? String or date?
    ...

# ✅ SENIOR APPROACH: Self-documenting, typed signature
from datetime import date
from typing import List, Dict, Any

def generate_available_slots(
    doctor: DoctorProfile, 
    target_date: date
) -> List[Dict[str, Any]]:
    """
    Computes all open, bookable slots for a doctor on a specific date,
    subtracting active appointments and scheduled leaves.
    """
```

### Rule 5.2: The "Rule of Three" (AHA: Avoid Hasty Abstractions)
* Do not build complex generic inheritance hierarchies or abstract factories before a piece of code is duplicated at least three times.
* Prefer **duplication over the wrong abstraction** in the early stages, but once duplicated across three distinct modules, extract it into a clean, testable utility.

---

## 6. Asynchronous Processing & Background Tasks

### Rule 6.1: Never Run Blocking I/O Inside HTTP Request Threads
The HTTP request-response cycle must finish in **$< 150\text{ms}$**. Any operation that involves external network latency or heavy CPU computation must be delegated to Celery:

| Belongs in Synchronous HTTP Thread | Must be Offloaded to Celery Worker |
| :--- | :--- |
| Database reads & atomic row locks | Transactional email & SMS alerts |
| Form validation & CSRF checks | Cloudinary heavy image watermarking |
| Rendering HTMX HTML partials | Auto-expiry timeout tasks (`countdown=600`) |
| Returning immediate status codes | Celery Beat periodic reminders |

### Rule 6.2: Pass IDs, Never Model Instances to Celery Tasks
Never pass full Django model instances as arguments to Celery tasks; always pass primary keys (`UUID` or `int`). Passing model instances leads to stale data bugs because the instance was serialized in the past.

```python
# ❌ BAD: Serializes Python object state at time of queueing
send_appointment_confirmation.delay(appointment)

# ✅ SENIOR APPROACH: Pass UUID; task refetches fresh state from DB
@shared_task
def send_appointment_confirmation(appointment_id: str) -> None:
    try:
        appointment = Appointment.objects.select_related('patient', 'doctor__user').get(id=appointment_id)
        # Process email with fresh data
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found.")
```

---

## 7. Error Handling, Logging & Defensive Coding

### Rule 7.1: Never Suppress Exceptions Silently
Never write bare `except:` or `except Exception: pass`. Always catch specific exceptions, log with structured context, and return a user-friendly error.

```python
# ❌ DANGEROUS: Masks bugs, database connection drops, and syntax errors
try:
    process_payment()
except:
    pass

# ✅ SENIOR APPROACH: Specific exception, structured logging, user feedback
import logging
logger = logging.getLogger(__name__)

try:
    PaymentGatewayService.verify_khalti_payment(pidx=pidx)
except PaymentVerificationFailedError as exc:
    logger.warning("Khalti verification rejected for pidx=%s: %s", pidx, str(exc))
    return render(request, 'partials/payment_failed.html', {'error': str(exc)}, status=400)
except requests.exceptions.RequestException as exc:
    logger.critical("Khalti API network unreachable: %s", str(exc), exc_info=True)
    return render(request, 'partials/gateway_error.html', status=503)
```

---

## 8. Summary Checklist for Code Reviews

Before committing backend code, verify:
- [ ] Are views thin ($< 25$ lines of code per view)?
- [ ] Is all domain logic isolated in `apps/*/services.py`?
- [ ] Are there zero N+1 queries (all foreign relations eager loaded with `select_related`)?
- [ ] Are all columns used in filters or ordering indexed in PostgreSQL?
- [ ] Are finite state transitions guarded with atomic `select_for_update()` locks?
- [ ] Are all external API calls and emails offloaded to Celery?
- [ ] Are primary keys passed to Celery tasks instead of model instances?
- [ ] Does every function have type annotations and a clear return type?
