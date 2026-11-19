import json
import logging
from decimal import Decimal
from typing import Dict, Any, Tuple
import requests
from django.conf import settings
from apps.payments.models import Payment

logger = logging.getLogger(__name__)

class KhaltiPaymentService:
    """
    Khalti ePayment (v2) Gateway Integration Service.
    Handles server-to-server payment initiation (/epayment/initiate/)
    and verification lookup (/epayment/lookup/).
    """

    @classmethod
    def get_secret_key(cls) -> str:
        return getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key_f59e8b7d18b2499f886f23e0183d7414')

    @classmethod
    def get_public_key(cls) -> str:
        return getattr(settings, 'KHALTI_PUBLIC_KEY', 'test_public_key_dc74e0fd69bc4f179157dd0426915f61')

    @classmethod
    def get_initiate_url(cls) -> str:
        return getattr(settings, 'KHALTI_GATEWAY_URL', 'https://a.khalti.com/api/v2/epayment/initiate/')

    @classmethod
    def get_lookup_url(cls) -> str:
        return 'https://a.khalti.com/api/v2/epayment/lookup/'

    @classmethod
    def initiate_payment(cls, payment: Payment, return_url: str, website_url: str) -> Dict[str, Any]:
        """
        Sends server-to-server request to Khalti v2 to initiate payment.
        Amount must be in Paisa (1 NPR = 100 Paisa).
        """
        amount_paisa = int(payment.amount * 100)
        doctor_name = payment.appointment.doctor.user.full_name

        payload = {
            'return_url': return_url,
            'website_url': website_url,
            'amount': amount_paisa,
            'purchase_order_id': str(payment.transaction_uuid),
            'purchase_order_name': f"Consultation with {doctor_name}",
            'customer_info': {
                'name': payment.patient.full_name,
                'email': payment.patient.email,
                'phone': getattr(payment.patient, 'phone_number', '') or '9800000000',
            }
        }

        headers = {
            'Authorization': f"Key {cls.get_secret_key()}",
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(cls.get_initiate_url(), json=payload, headers=headers, timeout=15)
            response_data = response.json()

            if response.status_code == 200 and 'payment_url' in response_data:
                # Save pidx into payment record
                payment.gateway_ref = response_data.get('pidx')
                payment.save(update_fields=['gateway_ref', 'updated_at'])
                return {
                    'success': True,
                    'payment_url': response_data['payment_url'],
                    'pidx': response_data['pidx'],
                }
            else:
                logger.error(f"Khalti initiation failed: {response_data}")
                return {
                    'success': False,
                    'error': response_data.get('detail') or str(response_data),
                }
        except Exception as err:
            logger.exception(f"Khalti initiation exception: {str(err)}")
            return {'success': False, 'error': f"Failed to connect to Khalti: {str(err)}"}

    @classmethod
    def verify_payment(cls, pidx: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Performs server-to-server lookup verification with Khalti using pidx.
        Returns: (is_success: bool, status: str, response_data: dict)
        """
        headers = {
            'Authorization': f"Key {cls.get_secret_key()}",
            'Content-Type': 'application/json',
        }
        payload = {'pidx': pidx}

        try:
            response = requests.post(cls.get_lookup_url(), json=payload, headers=headers, timeout=15)
            data = response.json()
            status_str = data.get('status', '')

            if response.status_code == 200 and status_str == 'Completed':
                return True, status_str, data
            else:
                return False, status_str, data
        except Exception as err:
            logger.exception(f"Khalti lookup exception: {str(err)}")
            return False, 'ERROR', {'error': str(err)}
