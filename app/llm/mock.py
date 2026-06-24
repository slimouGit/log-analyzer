import json

from app.llm.base import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM client for testing and demo purposes."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a realistic demo response without calling a real LLM."""
        return json.dumps({
            "incident_type": "application_error",
            "severity": "high",
            "affected_component": "payment service / checkout controller",
            "short_summary": "Payment capture fails due to null coupon object during discount calculation",
            "probable_root_cause": "The coupon object is not validated before calling getDiscount(). A null reference is passed to applyDiscount() method.",
            "important_log_lines": [
                "java.lang.NullPointerException: Cannot invoke \"Coupon.getDiscount()\" because \"coupon\" is null",
                "at com.shop.checkout.PaymentService.applyDiscount(PaymentService.java:87)",
                "Request failed for orderId=ORD-10492, customerId=C-9921"
            ],
            "recommended_debug_steps": [
                "Add null check before calling coupon.getDiscount() in PaymentService.applyDiscount()",
                "Verify coupon object initialization in CheckoutController.pay()",
                "Add logging to trace coupon value before applyDiscount call",
                "Check if optional discount code validation is missing"
            ],
            "possible_fix_direction": "Add defensive null check: if (coupon != null) { coupon.getDiscount(); } or use Optional<Coupon> pattern",
            "test_cases": [
                "test_checkout_without_coupon_code",
                "test_checkout_with_null_coupon_object",
                "test_checkout_with_invalid_coupon_format",
                "test_payment_service_handles_missing_discount"
            ],
            "confidence": 0.92
        })
