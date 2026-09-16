"""Stripe payment processing handler."""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime


class StripeHandler:
    """Handle Stripe payment operations."""

    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self._initialized = False

    async def initialize(self):
        """Initialize Stripe client."""
        if not self.api_key:
            print("⚠️ Stripe not configured - payment features disabled")
            return False

        try:
            import stripe
            stripe.api_key = self.api_key
            self._stripe = stripe
            self._initialized = True
            return True
        except ImportError:
            print("⚠️ Stripe package not installed: pip install stripe")
            return False

    async def create_customer(self, user_id: str, email: str,
                               name: str = None) -> dict:
        """Create a Stripe customer."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            customer = self._stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": user_id},
            )
            return {
                "customer_id": customer.id,
                "email": email,
            }
        except Exception as e:
            return {"error": str(e)}

    async def create_subscription(self, customer_id: str,
                                    price_id: str) -> dict:
        """Create a subscription."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            subscription = self._stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
                    if subscription.latest_invoice else None,
            }
        except Exception as e:
            return {"error": str(e)}

    async def create_checkout_session(self, customer_id: str,
                                        price_id: str,
                                        success_url: str,
                                        cancel_url: str) -> dict:
        """Create a Stripe Checkout session."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            session = self._stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return {
                "session_id": session.id,
                "url": session.url,
            }
        except Exception as e:
            return {"error": str(e)}

    async def create_payment_intent(self, amount: float, currency: str = "usd",
                                      customer_id: str = None) -> dict:
        """Create a one-time payment (for credits)."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            intent = self._stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                customer=customer_id,
                automatic_payment_methods={"enabled": True},
            )
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
            }
        except Exception as e:
            return {"error": str(e)}

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            subscription = self._stripe.Subscription.delete(subscription_id)
            return {
                "subscription_id": subscription.id,
                "status": "cancelled",
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get subscription details."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            subscription = self._stripe.Subscription.retrieve(subscription_id)
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ).isoformat() if subscription.current_period_end else None,
            }
        except Exception as e:
            return {"error": str(e)}

    async def handle_webhook(self, payload: str, sig_header: str) -> dict:
        """Handle Stripe webhook events."""
        if not self._initialized:
            return {"error": "Stripe not initialized"}

        try:
            event = self._stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # Route to handler
            handlers = {
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "invoice.payment_succeeded": self._handle_payment_success,
                "invoice.payment_failed": self._handle_payment_failed,
            }

            handler = handlers.get(event["type"])
            if handler:
                return await handler(event["data"]["object"])

            return {"handled": False, "type": event["type"]}

        except Exception as e:
            return {"error": str(e)}

    async def _handle_subscription_created(self, subscription: dict) -> dict:
        """Handle new subscription."""
        # Would update database
        return {"action": "subscription_created", "id": subscription.get("id")}

    async def _handle_subscription_updated(self, subscription: dict) -> dict:
        """Handle subscription update."""
        return {"action": "subscription_updated", "id": subscription.get("id")}

    async def _handle_subscription_deleted(self, subscription: dict) -> dict:
        """Handle subscription cancellation."""
        return {"action": "subscription_deleted", "id": subscription.get("id")}

    async def _handle_payment_success(self, invoice: dict) -> dict:
        """Handle successful payment."""
        return {"action": "payment_success", "amount": invoice.get("amount_paid")}

    async def _handle_payment_failed(self, invoice: dict) -> dict:
        """Handle failed payment."""
        return {"action": "payment_failed", "customer": invoice.get("customer")}

    def get_publishable_key(self) -> str:
        """Get Stripe publishable key for frontend."""
        return self.publishable_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


# Global instance
stripe_handler = StripeHandler()