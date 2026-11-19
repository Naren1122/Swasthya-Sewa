from django.urls import path
from apps.payments.web.views import (
    PaymentInitiateView,
    EsewaSuccessCallbackView,
    EsewaFailureCallbackView,
    KhaltiCallbackView,
)

urlpatterns = [
    # Payment Gateway Dispatcher (POST)
    path('payments/initiate/<uuid:appointment_id>/', PaymentInitiateView.as_view(), name='payment_initiate'),

    # eSewa v2 Callbacks (GET)
    path('payments/esewa/success/', EsewaSuccessCallbackView.as_view(), name='esewa_success'),
    path('payments/esewa/failure/', EsewaFailureCallbackView.as_view(), name='esewa_failure'),

    # Khalti v2 Callback (GET)
    path('payments/khalti/callback/', KhaltiCallbackView.as_view(), name='khalti_callback'),
]
