from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    npwp = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    users = relationship("User", back_populates="company")
    shipments = relationship("Shipment", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="staf")  # staf, reviewer, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    company = relationship("Company", back_populates="users")


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("company_id", "shipment_number", name="uq_shipments_company_shipment_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    shipment_number = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255), nullable=False)
    bl_number = Column(String(100), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    currency = Column(String(10), default="USD")
    exchange_rate = Column(Numeric(15, 2), default=16000.00)
    cif_total_idr = Column(Numeric(18, 2), default=0.00)
    total_duty_idr = Column(Numeric(18, 2), default=0.00)

    # Readiness & Status
    readiness_status = Column(String(50), default="incomplete")  # ready, incomplete, blocked
    status = Column(String(50), default="draft")  # draft, analyzing, needs_clarification, needs_review, needs_documents, ready, submitted, arrived, failed
    input_version = Column(Integer, default=1)
    needs_action_rule_change = Column(Boolean, default=False)

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company", back_populates="shipments")
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="shipment", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    line_no = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(12, 2), default=1.0)
    uom = Column(String(50), default="UNIT")
    unit_price = Column(Numeric(15, 2), default=0.0)
    total_price_cif = Column(Numeric(18, 2), default=0.0)

    hs_code_proposed = Column(String(20), nullable=True)
    hs_code_accepted = Column(String(20), nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    risk_level = Column(String(50), default="low")  # low, medium, high
    status = Column(String(50), default="draft")  # draft, classified, needs_clarification, review, approved, rejected, out_of_scope
    is_approved = Column(Boolean, default=False)
    version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    shipment = relationship("Shipment", back_populates="items")
    clarifications = relationship("Clarification", back_populates="item")
    duty_calculations = relationship("DutyCalculation", back_populates="item")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)  # INVOICE, PACKING_LIST, BL, DATASHEET, LARTAS_PERMIT
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    parsed_content = Column(Text, nullable=True)
    status = Column(String(50), default="provided")  # provided, missing, pending, not_needed
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    shipment = relationship("Shipment", back_populates="documents")


class HSCode(Base):
    __tablename__ = "hs_codes"

    id = Column(Integer, primary_key=True, index=True)
    hs_code = Column(String(20), unique=True, nullable=False, index=True)
    description_id = Column(Text, nullable=False)
    description_en = Column(Text, nullable=True)
    bm_rate = Column(Numeric(5, 2), default=5.0)
    ppn_rate = Column(Numeric(5, 2), default=11.0)
    pph_rate = Column(Numeric(5, 2), default=2.5)
    lartas_coverage = Column(String(50), default="unknown")  # verified_rules, verified_none, unknown
    last_checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    source = Column(String(100), default="BTKI 2022")


class LartasRuleEntity(Base):
    __tablename__ = "lartas_rules"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # NULL for official, company_id for simulation
    hs_prefix = Column(String(20), nullable=False, index=True)
    requirement_key = Column(String(100), nullable=False)
    permit_name = Column(String(255), nullable=False)
    issuing_agency = Column(String(100), nullable=False)
    rule_group = Column(String(100), nullable=False)
    supersedes_rule_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    source = Column(String(100), default="INSW Official")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("shipment_items.id"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    requirement_code = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    agency = Column(String(100), nullable=False)
    status = Column(String(50), default="missing")  # provided, missing, pending, not_needed
    required_before_submission = Column(Boolean, default=True)
    resolution_reason = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)


class DutyCalculation(Base):
    __tablename__ = "duty_calculations"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("shipment_items.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    cif_idr = Column(Numeric(18, 2), nullable=False)
    bm_percentage = Column(Numeric(5, 2), default=5.0)
    bm_idr = Column(Numeric(18, 2), nullable=False)
    ppn_percentage = Column(Numeric(5, 2), default=11.0)
    ppn_idr = Column(Numeric(18, 2), nullable=False)
    pph_percentage = Column(Numeric(5, 2), default=2.5)
    pph_idr = Column(Numeric(18, 2), nullable=False)
    total_duties_idr = Column(Numeric(18, 2), nullable=False)
    is_current = Column(Boolean, default=True)
    calculation_version = Column(Integer, default=1)
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    item = relationship("ShipmentItem", back_populates="duty_calculations")


class Clarification(Base):
    __tablename__ = "clarifications"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("shipment_items.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    attribute = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, answered, cancelled
    answer = Column(Text, nullable=True)
    answer_source = Column(String(50), nullable=True)  # supplier_email, staff_form, datasheet_upload
    resolution_evidence = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    answered_at = Column(DateTime(timezone=True), nullable=True)

    item = relationship("ShipmentItem", back_populates="clarifications")


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("shipment_items.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    review_type = Column(String(50), default="classification")  # classification, compliance
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="open")  # open, approved, modified, rejected, superseded
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    decided_at = Column(DateTime(timezone=True), nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    parent_run_id = Column(Integer, nullable=True)
    mode = Column(String(50), default="assist")  # assist, auto
    input_version = Column(Integer, default=1)
    target_item_ids = Column(JSON, nullable=True)  # list of item IDs or None for full run
    status = Column(String(50), default="queued")  # queued, running, succeeded, failed
    outcome = Column(String(50), nullable=True)  # complete, waiting_external, action_required
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    cost_usd = Column(Numeric(10, 4), default=0.0)
    total_tokens = Column(Integer, default=0)

    shipment = relationship("Shipment", back_populates="agent_runs")
    steps = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    seq = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    step_outcome = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    run = relationship("AgentRun", back_populates="steps")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    dedupe_key = Column(String(255), unique=True, nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    status = Column(String(50), default="queued")  # queued, processing, completed, failed
    heartbeat_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class OutboxMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    dedupe_key = Column(String(255), unique=True, nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    delivery_status = Column(String(50), default="pending")  # pending, sent, failed, unknown
    provider_message_id = Column(String(255), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ClassificationMemory(Base):
    __tablename__ = "classification_memory"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    item_description = Column(Text, nullable=False)
    hs_code = Column(String(20), nullable=False)
    matched_attributes = Column(JSON, nullable=True)
    decision_source = Column(String(50), default="human_review")  # must be human decision
    human_decision_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    superseded_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # NULL for global, company_id for simulation
    regulation_number = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    hs_prefix = Column(String(20), nullable=False)
    requirement_code = Column(String(100), nullable=False)
    is_simulation = Column(Boolean, default=False)
    effective_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AuthThrottleEntity(Base):
    __tablename__ = "auth_throttle"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    attempt_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    success = Column(Boolean, default=False)
