from decimal import Decimal
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.resource import Resource
from app.models.request import ServiceRequest

ACTIVE_STATUSES = ["SUBMITTED", "APPROVED", "IN_PROGRESS"]
VALID_TRANSITIONS = {
    "SUBMITTED": ["APPROVED", "CANCELLED"],
    "APPROVED": ["IN_PROGRESS"],
    "IN_PROGRESS": ["COMPLETED"],
    "COMPLETED": [],
    "CANCELLED": []
}


class ValidationService:
    @staticmethod
    def validate_details(name: str, phone: str, description: str, reference: str) -> Tuple[bool, str]:
        """
        BR5: Name cannot be blank. Phone must contain exactly 10 digits.
        Required description/reference fields must be valid.
        """
        if not name or not name.strip():
            return False, "Applicant name cannot be blank."
        
        if not phone or not phone.strip():
            return False, "Phone number cannot be blank."
        
        clean_phone = phone.strip()
        if not (clean_phone.isdigit() and len(clean_phone) == 10):
            return False, "Phone number must contain exactly 10 digits."
        
        if not description or not description.strip():
            return False, "Description cannot be blank."
            
        if not reference or not reference.strip():
            return False, "Reference cannot be blank."

        return True, ""

    @staticmethod
    def validate_eligibility(user: Optional[User], resource: Optional[Resource]) -> Tuple[bool, str]:
        """
        BR2: Both user and requested resource must be active and eligible.
        Revalidate immediately before acceptance. Capacity must be > 0.
        """
        if not user:
            return False, "User not found."
        if user.status != "ACTIVE":
            return False, f"User account '{user.id}' is inactive/ineligible."
        
        if not resource:
            return False, "Certificate resource not found."
        if resource.status != "ACTIVE":
            return False, f"Certificate service '{resource.id}' is currently inactive."
        if resource.capacity <= 0:
            return False, f"Certificate service '{resource.id}' has zero available capacity."

        return True, ""

    @staticmethod
    def validate_request_limit(user_id: str, db: Session) -> Tuple[bool, str]:
        """
        BR1: A user may have at most FIVE active requests of this type. Reject the sixth.
        Active: SUBMITTED, APPROVED, IN_PROGRESS.
        """
        active_count = db.query(ServiceRequest).filter(
            ServiceRequest.user_id == user_id,
            ServiceRequest.status.in_(ACTIVE_STATUSES)
        ).count()

        if active_count >= 5:
            return False, f"User quota exceeded: already has {active_count} active requests (maximum allowed is 5)."
        return True, ""

    @staticmethod
    def calculate_charge(resource: Resource, base_value: Optional[Decimal]) -> Decimal:
        """
        BR4: When a chargeable amount applies:
        - Base value below ₹1,000: charge ₹50.
        - Base value ₹1,000 or above: charge ₹0.
        - No chargeable amount: charge ₹0.
        Use decimal-safe monetary calculations.
        """
        if not resource.charge_applicable:
            return Decimal("0.00")
        
        val = base_value if base_value is not None else Decimal("0.00")
        if val < Decimal("1000.00"):
            return Decimal("50.00")
        else:
            return Decimal("0.00")

    @staticmethod
    def validate_transition(current_status: str, target_status: str, actor_role: str) -> Tuple[bool, str]:
        """
        BR8 & BR10:
        Only allow: SUBMITTED -> APPROVED -> IN_PROGRESS -> COMPLETED
        Users may cancel only SUBMITTED requests.
        Administrator cannot skip stages or reopen completed/cancelled requests.
        """
        if current_status not in VALID_TRANSITIONS:
            return False, f"Unknown current status: {current_status}"

        allowed_next = VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed_next:
            return False, f"Invalid transition from '{current_status}' to '{target_status}'. Stage skipping or reopening terminal states is prohibited."

        if target_status == "CANCELLED":
            # Cancellation must only be initiated when request is SUBMITTED
            if current_status != "SUBMITTED":
                return False, "Only requests in SUBMITTED status can be cancelled."
        else:
            # Stage progression requires ADMINISTRATOR
            if actor_role != "ADMINISTRATOR":
                return False, "Only Administrator can advance request stages."

        return True, ""
