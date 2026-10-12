from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserOut(BaseModel):
    id: str
    name: str
    role: str
    status: str
    phone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResourceOut(BaseModel):
    id: str
    service_name: str
    capacity: int
    status: str
    base_value: Decimal
    charge_applicable: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestCreateSchema(BaseModel):
    resource_id: str = Field(..., description="Target certificate resource ID")
    name: str = Field(..., min_length=1, description="Applicant full name")
    phone: str = Field(..., min_length=10, max_length=10, description="10-digit mobile number")
    description: str = Field(..., min_length=1, description="Request purpose/description")
    reference: str = Field(..., min_length=1, description="Student / institutional reference")
    base_value: Optional[Decimal] = Field(default=Decimal("0.00"), description="Base value for calculation")
    idempotency_key: str = Field(..., min_length=5, description="Unique client idempotency token")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Applicant name cannot be blank or whitespace.")
        return stripped

    @field_validator("phone")
    def validate_phone(cls, v: str) -> str:
        stripped = v.strip()
        if not (stripped.isdigit() and len(stripped) == 10):
            raise ValueError("Phone number must contain exactly 10 digits.")
        return stripped

    @field_validator("description")
    def validate_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Description cannot be blank.")
        return stripped

    @field_validator("reference")
    def validate_reference(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Reference cannot be blank.")
        return stripped


class ChargePreviewRequest(BaseModel):
    resource_id: str
    base_value: Optional[Decimal] = Decimal("0.00")


class ChargePreviewResponse(BaseModel):
    resource_id: str
    charge_applicable: bool
    base_value: Decimal
    calculated_charge: Decimal
    explanation: str


class StatusHistoryOut(BaseModel):
    id: int
    reference_id: str
    actor_id: str
    old_status: Optional[str]
    new_status: str
    event_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestOut(BaseModel):
    id: str
    user_id: str
    resource_id: str
    name: str
    phone: str
    description: str
    reference: str
    base_value: Decimal
    service_charge: Decimal
    status: str
    snapshot_data: Dict[str, Any]
    idempotency_key: str
    resource_reserved: bool
    resource_released: bool
    created_at: datetime
    updated_at: datetime
    status_history: List[StatusHistoryOut] = []

    model_config = ConfigDict(from_attributes=True)


class AdvanceStatusSchema(BaseModel):
    target_status: str
