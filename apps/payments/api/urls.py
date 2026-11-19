from django.urls import path
from apps.payments.api.views import (
    PaymentInitiateAPIView,
    PaymentVerifyAPIView,
    PaymentListAPIView,
    PaymentDetailAPIView,
)

urlpatterns = [
    # Initiate Payment (POST)
    path('payments/initiate/', PaymentInitiateAPIView.as_view(), name='api_payment_initiate'),

    # Verify Payment Callback (POST)
    path('payments/verify/', PaymentVerifyAPIView.as_view(), name='api_payment_verify'),

    # Patient Payments History (GET)
    path('payments/', PaymentListAPIView.as_view(), name='api_payment_list'),

    # Payment Detail / Receipt (GET)
    path('payments/<uuid:payment_id>/', PaymentDetailAPIView.as_view(), name='api_payment_detail'),
]
