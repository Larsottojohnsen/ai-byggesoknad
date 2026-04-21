"""
SQLAlchemy ORM models for AI Byggesøknad.
Maps to the schema defined in infra/migrations/001_initial_schema.sql
"""
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text,
    DateTime, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class Address(Base):
    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    address_text = Column(Text, nullable=False)
    municipality = Column(Text, nullable=False)
    municipality_no = Column(Text)
    postal_code = Column(Text)
    postal_place = Column(Text)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="address")


class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    address_id = Column(UUID(as_uuid=False), ForeignKey("addresses.id"))
    municipality_no = Column(Text, nullable=False)
    municipality = Column(Text, nullable=False)
    gnr = Column(Integer, nullable=False)
    bnr = Column(Integer, nullable=False)
    fnr = Column(Integer)
    snr = Column(Integer)
    areal = Column(Float)
    building_status = Column(Text)
    raw_data = Column(JSONB)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    address_id = Column(UUID(as_uuid=False), ForeignKey("addresses.id"))
    property_id = Column(UUID(as_uuid=False), ForeignKey("properties.id"))
    address_text = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    intent_text = Column(Text, nullable=False)
    classified_measure_type = Column(Text)
    classification_confidence = Column(Float)
    status = Column(Text, nullable=False, default="draft")
    risk_level = Column(Text)
    application_required = Column(Boolean)
    readiness_score = Column(Integer)
    ai_summary = Column(Text)
    next_steps = Column(JSONB, default=list)
    document_requirements = Column(JSONB, default=list)
    warnings = Column(JSONB, default=list)
    analyzed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    address = relationship("Address", back_populates="projects")
    plan_results = relationship("PlanLayerResultORM", back_populates="project", cascade="all, delete-orphan")
    hazard_results = relationship("HazardResultORM", back_populates="project", cascade="all, delete-orphan")
    rule_results = relationship("RuleResultORM", back_populates="project", cascade="all, delete-orphan")
    document_artifacts = relationship("DocumentArtifact", back_populates="project", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="project", cascade="all, delete-orphan")


class PlanLayerResultORM(Base):
    __tablename__ = "plan_layer_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Text)
    plan_name = Column(Text)
    plan_status = Column(Text, nullable=False, default="ukjent")
    areal_formal = Column(Text, nullable=False, default="ukjent")
    hensynssoner = Column(JSONB, default=list)
    byggegrense = Column(Float)
    utnyttelsesgrad = Column(Text)
    plan_url = Column(Text)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="plan_results")


class HazardResultORM(Base):
    __tablename__ = "hazard_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    flom_fare = Column(Text, nullable=False, default="ukjent")
    skred_fare = Column(Text, nullable=False, default="ukjent")
    flom_sone_id = Column(Text)
    skred_sone_id = Column(Text)
    notes = Column(Text)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="hazard_results")


class RuleResultORM(Base):
    __tablename__ = "rule_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    rule_code = Column(Text, nullable=False)
    rule_name = Column(Text, nullable=False)
    rule_group = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="unknown")
    explanation = Column(Text)
    evidence_refs = Column(JSONB, default=list)
    is_blocking = Column(Boolean, nullable=False, default=False)
    source_version = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="rule_results")


class DocumentArtifact(Base):
    __tablename__ = "document_artifacts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    storage_url = Column(Text)
    content_text = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    ai_generated = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="document_artifacts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"))
    event_type = Column(Text, nullable=False)
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="audit_events")
