"""Pydantic models for the section 4 contracts.

Session 1: input-case contracts only (what calc needs). Model-only output
and merged-result models land in later sessions. All models reject unknown
fields.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

LogEntryType = Literal[
    "StartTransaction", "StopTransaction", "StatusNotification",
    "MeterValues", "Heartbeat",
]
PaymentStatus = Literal["held", "captured", "pending", "failed", "refunded"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Complaint(StrictModel):
    text: str
    received_at: datetime


class LogEntry(StrictModel):
    ts: datetime
    type: LogEntryType
    connector_id: Optional[int] = None
    meter_wh: Optional[int] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    reason: Optional[str] = None


class Payment(StrictModel):
    method: str
    currency: str
    held: int
    captured: int
    status: PaymentStatus


class Case(StrictModel):
    case_id: str
    complaint: Complaint
    session_log: list[LogEntry]
    payment: Payment
    tariff_kes_per_kwh: float


# Session 3: model-only output contract (what rules needs). Session 4 reuses
# these for validating model replies.

Side = Literal["charger", "network", "vehicle", "driver", "payment", "unknown"]
EvidenceSource = Literal["log", "complaint", "payment", "reference"]
Language = Literal["en", "sw", "sheng", "fr", "de", "it", "zh", "pt"]


class Evidence(StrictModel):
    source: EvidenceSource
    ref: str
    note: str


class DriverMessage(StrictModel):
    language: Language
    text: str


class ModelOutput(StrictModel):
    side: Side
    cause: str
    evidence: list[Evidence]
    clause_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    driver_message: DriverMessage
    technician_note: Optional[str] = None


# Session 6: merged result contract (model fields plus code-written fields).

class RefundDraft(StrictModel):
    amount_kes: int
    requires_approval: bool


class Result(StrictModel):
    case_id: str
    side: Optional[Side] = None
    cause: Optional[str] = None
    evidence: list[Evidence] = []
    clause_ids: list[str] = []
    confidence: Optional[float] = None
    driver_message: Optional[DriverMessage] = None
    technician_note: Optional[str] = None
    calc: Optional[dict] = None
    still_open: bool
    refund_draft: Optional[RefundDraft] = None
    escalate: bool
    escalate_reasons: list[str] = []
    verification: dict[str, bool] = {}
