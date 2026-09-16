"""Billing history and invoice management."""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    VOID = "void"


@dataclass
class Invoice:
    """Invoice record."""
    id: str
    user_id: str
    amount: float
    currency: str
    status: InvoiceStatus
    description: str
    items: List[dict]
    created_at: datetime
    paid_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None


class BillingManager:
    """Manage billing and invoices."""

    def __init__(self):
        self._invoices: Dict[str, List[Invoice]] = {}
        self._payment_methods: Dict[str, list] = {}

    def create_invoice(self, user_id: str, amount: float,
                        description: str, items: List[dict] = None) -> Invoice:
        """Create a new invoice."""
        invoice_id = f"inv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:8]}"

        invoice = Invoice(
            id=invoice_id,
            user_id=user_id,
            amount=amount,
            currency="usd",
            status=InvoiceStatus.PENDING,
            description=description,
            items=items or [],
            created_at=datetime.now(),
            due_date=datetime.now() + timedelta(days=7),
        )

        if user_id not in self._invoices:
            self._invoices[user_id] = []
        self._invoices[user_id].append(invoice)

        return invoice

    def mark_paid(self, invoice_id: str) -> Optional[Invoice]:
        """Mark invoice as paid."""
        for user_invoices in self._invoices.values():
            for invoice in user_invoices:
                if invoice.id == invoice_id:
                    invoice.status = InvoiceStatus.PAID
                    invoice.paid_at = datetime.now()
                    return invoice
        return None

    def get_invoices(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user's invoices."""
        invoices = self._invoices.get(user_id, [])
        return [
            {
                "id": inv.id,
                "amount": inv.amount,
                "currency": inv.currency,
                "status": inv.status.value,
                "description": inv.description,
                "created_at": inv.created_at.isoformat(),
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            }
            for inv in invoices[-limit:]
        ]

    def get_billing_summary(self, user_id: str) -> dict:
        """Get billing summary for a user."""
        invoices = self._invoices.get(user_id, [])

        total_paid = sum(
            inv.amount for inv in invoices
            if inv.status == InvoiceStatus.PAID
        )
        total_pending = sum(
            inv.amount for inv in invoices
            if inv.status == InvoiceStatus.PENDING
        )

        # This month's charges
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = [
            inv for inv in invoices
            if inv.created_at >= month_start
        ]

        return {
            "total_paid": total_paid,
            "total_pending": total_pending,
            "this_month": sum(inv.amount for inv in this_month),
            "invoice_count": len(invoices),
            "next_payment_due": next(
                (inv.due_date.isoformat() for inv in invoices
                 if inv.status == InvoiceStatus.PENDING),
                None
            ),
        }

    def generate_usage_invoice(self, user_id: str, usage: dict) -> Invoice:
        """Generate invoice based on usage."""
        items = []
        total = 0

        for service, data in usage.get("by_service", {}).items():
            items.append({
                "description": f"{service.title()} - {data.get('count', 0)} generations",
                "amount": data.get("cost", 0),
                "quantity": data.get("count", 1),
            })
            total += data.get("cost", 0)

        # Add any overage charges
        if usage.get("overage", 0) > 0:
            items.append({
                "description": "Usage overage",
                "amount": usage["overage"],
                "quantity": 1,
            })
            total += usage["overage"]

        return self.create_invoice(
            user_id=user_id,
            amount=total,
            description="Monthly usage charges",
            items=items,
        )

    def add_payment_method(self, user_id: str, method_type: str,
                            last_four: str, is_default: bool = False) -> dict:
        """Add a payment method."""
        if user_id not in self._payment_methods:
            self._payment_methods[user_id] = []

        method = {
            "id": f"pm_{len(self._payment_methods[user_id]) + 1}",
            "type": method_type,
            "last_four": last_four,
            "is_default": is_default,
            "added_at": datetime.now().isoformat(),
        }

        if is_default:
            for m in self._payment_methods[user_id]:
                m["is_default"] = False

        self._payment_methods[user_id].append(method)
        return method

    def get_payment_methods(self, user_id: str) -> list:
        """Get user's payment methods."""
        return self._payment_methods.get(user_id, [])


# Global instance
billing_manager = BillingManager()