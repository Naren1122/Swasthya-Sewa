import base64
import hmac
import hashlib
import json
import urllib.parse
from decimal import Decimal
from typing import Dict, Any, Tuple
import requests
from django.conf import settings
from apps.payments.models import Payment

class EsewaPaymentService:
    """
    eSewa ePPS (v2) Gateway Integration Service.
    Handles HMAC-SHA256 signature generation, payload formatting,
    response decoding, and cryptographic anti-tampering verification.
    """

    @classmethod
    def get_merchant_code(cls) -> str:
        return getattr(settings, 'ESEWA_MERCHANT_CODE', 'EPAYTEST')

    @classmethod
    def get_secret_key(cls) -> str:
        return getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')

    @classmethod
    def get_gateway_url(cls) -> str:
        return getattr(settings, 'ESEWA_GATEWAY_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')

    @classmethod
    def generate_signature(cls, message: str) -> str:
        """
        Generates Base64 encoded HMAC-SHA256 signature for a message string.
        """
        secret = cls.get_secret_key().encode('utf-8')
        signature = hmac.new(secret, message.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')

    @classmethod
    def initiate_payment(cls, payment: Payment, success_url: str, failure_url: str) -> Dict[str, Any]:
        """
        Builds the signed eSewa checkout payload dictionary for frontend submission.
        """
        # Format total amount without trailing zeros if whole number
        amount_str = f"{payment.amount:.2f}".rstrip('0').rstrip('.') if '.' in f"{payment.amount:.2f}" else f"{payment.amount:.2f}"
        # Ensure at least 1 or 2 decimals if needed, or exact float string
        amount_str = f"{payment.amount:.0f}" if payment.amount == int(payment.amount) else f"{payment.amount:.2f}"

        product_code = cls.get_merchant_code()
        transaction_uuid = str(payment.transaction_uuid)

        # eSewa v2 signature string: total_amount,transaction_uuid,product_code
        signature_message = f"total_amount={amount_str},transaction_uuid={transaction_uuid},product_code={product_code}"
        signature = cls.generate_signature(signature_message)

        return {
            'action_url': cls.get_gateway_url(),
            'fields': {
                'amount': amount_str,
                'tax_amount': '0',
                'total_amount': amount_str,
                'transaction_uuid': transaction_uuid,
                'product_code': product_code,
                'product_service_charge': '0',
                'product_delivery_charge': '0',
                'success_url': success_url,
                'failure_url': failure_url,
                'signed_field_names': 'total_amount,transaction_uuid,product_code',
                'signature': signature,
            }
        }

    @classmethod
    def decode_response_data(cls, encoded_data: str) -> Dict[str, Any]:
        """
        Decodes eSewa's base64 encoded response parameter into a dictionary.
        """
        try:
            decoded_bytes = base64.b64decode(encoded_data)
            return json.loads(decoded_bytes.decode('utf-8'))
        except Exception as err:
            return {'error': f"Failed to decode eSewa response: {str(err)}"}

    @classmethod
    def verify_payment(cls, encoded_data: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifies eSewa v2 callback response:
        1. Decodes base64 payload
        2. Validates HMAC-SHA256 signature against signed_field_names
        3. Verifies status == 'COMPLETE'
        Returns: (is_valid: bool, transaction_uuid: str, decoded_data: dict)
        """
        data = cls.decode_response_data(encoded_data)
        if 'error' in data:
            return False, '', data

        received_signature = data.get('signature', '')
        signed_field_names = data.get('signed_field_names', '')
        status = data.get('status', '')
        transaction_uuid = data.get('transaction_uuid', '')

        if not received_signature or not signed_field_names or not transaction_uuid:
            return False, transaction_uuid, data

        # Reconstruct message in the exact order specified by signed_field_names
        fields = signed_field_names.split(',')
        message_parts = [f"{field}={data.get(field, '')}" for field in fields if field != 'signature']
        message = ','.join(message_parts)

        expected_signature = cls.generate_signature(message)

        if not hmac.compare_digest(received_signature, expected_signature):
            return False, transaction_uuid, {**data, 'error': 'Signature verification failed. Potential tampering detected.'}

        if status != 'COMPLETE':
            return False, transaction_uuid, {**data, 'error': f"Payment status not complete: {status}"}

        return True, transaction_uuid, data
