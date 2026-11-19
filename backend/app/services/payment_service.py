"""Payment & Refund Provider Interface and Implementations.

Per product requirement:
"Do not claim a payment has been refunded unless a payment provider confirms it.
If no payment integration exists, implement a clearly labeled manual refund workflow
or mock provider. Keep an auditable record of case actions."
"""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BasePaymentProvider(ABC):
    @abstractmethod
    def process_refund(
        self,
        order_id: int,
        amount: int,
        reason: str,
        admin_id: Optional[int] = None,
        manual_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass


class MockPaymentProvider(BasePaymentProvider):
    """Clearly labeled mock and manual refund provider for demonstration and test orders."""

    def process_refund(
        self,
        order_id: int,
        amount: int,
        reason: str,
        admin_id: Optional[int] = None,
        manual_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        ref_id = manual_reference.strip() if manual_reference and manual_reference.strip() else f"REFUND-MOCK-{uuid.uuid4().hex[:8].upper()}"
        is_manual = bool(manual_reference and manual_reference.strip())

        return {
            "success": True,
            "status": "refunded_manual_recorded" if is_manual else "refunded_mock_simulated",
            "provider_name": "Manual Record" if is_manual else "Mock Payment Gateway (Simulation)",
            "is_real_money": False,
            "reference_id": ref_id,
            "amount": amount,
            "currency": "INR",
            "timestamp": utcnow().isoformat(),
            "reason": reason,
            "confirmation_note": (
                f"Manual bank/UPI transaction recorded with reference '{ref_id}'. "
                "No automated credit card chargeback occurred."
                if is_manual
                else f"Simulated mock payment refund processed successfully (Reference: {ref_id}). "
                "This is a demonstration marketplace: no actual currency was debited or credited."
            ),
        }


def get_payment_provider() -> BasePaymentProvider:
    return MockPaymentProvider()
