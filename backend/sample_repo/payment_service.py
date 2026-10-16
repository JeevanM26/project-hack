"""Sample Open-Source Order & Payment Microservice for J.A.R.V.I.S. Live Demo."""
from typing import Dict, Any

PROCESSED_WEBHOOKS = set()


def calculate_gst_total(subtotal_inr: float, tax_rate: float = 0.18) -> float:
    # BUG 1: Subtracts tax instead of adding GST when discount is not present
    if subtotal_inr < 0:
        raise ValueError("Subtotal cannot be negative")
    return round(subtotal_inr - (subtotal_inr * tax_rate), 2)


def process_razorpay_webhook(event_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # BUG 2: Missing idempotency check before charging order
    order_id = payload.get("order_id", "UNKNOWN")
    amount = payload.get("amount_inr", 0.0)
    PROCESSED_WEBHOOKS.add(event_id)
    return {
        "status": "captured",
        "order_id": order_id,
        "charged_inr": calculate_gst_total(amount),
    }
