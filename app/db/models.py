from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    status: Mapped[str] = mapped_column(String(32), default="active")

    claims: Mapped[list["Claim"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    verdicts: Mapped[list["Verdict"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    event: Mapped[Event] = relationship(back_populates="claims")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    verdicts: Mapped[list["Verdict"]] = relationship(back_populates="claim", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(Text, unique=True)
    domain: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    independence_chain_id: Mapped[str] = mapped_column(String(64), default="")
    rating_status: Mapped[str] = mapped_column(String(64), default="not_connected")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    evidence: Mapped[list["Evidence"]] = relationship(back_populates="source")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    stance: Mapped[str] = mapped_column(String(16), default="neutral")  # supports/refutes/neutral
    snippet: Mapped[str] = mapped_column(Text, default="")
    snippet_hash: Mapped[str] = mapped_column(String(64), default="")
    retrieved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    claim: Mapped[Claim] = relationship(back_populates="evidence")
    source: Mapped[Source] = relationship(back_populates="evidence")


class Verdict(Base):
    __tablename__ = "verdicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(32))  # supported/refuted/mixed/insufficient_evidence/outdated/not_checkable
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    counter_argument: Mapped[str] = mapped_column(Text, default="")
    evidence_gaps: Mapped[list] = mapped_column(JSON, default=list)
    model: Mapped[str] = mapped_column(String(128), default="")
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    event: Mapped[Event] = relationship(back_populates="verdicts")
    claim: Mapped[Claim] = relationship(back_populates="verdicts")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String(32))  # check/deep_check/track_run
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued/running/done/failed/cancelled
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chat_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    chat_id: Mapped[int] = mapped_column(Integer)
    interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    next_run_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_run_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evidence_fingerprint: Mapped[str] = mapped_column(String(64), default="")
    last_verdict_version: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    event: Mapped[Event] = relationship(back_populates="subscriptions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="update")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    sent_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    __table_args__ = (UniqueConstraint("subscription_id", "content_hash", name="uq_sub_content"),)


class IMChannelConfig(Base):
    """Per-platform instant-messaging connection settings, edited from the admin wizard.

    Credentials are stored as JSON (masked on read). Replaces the old
    "edit .env + restart container" workflow so users can connect a channel
    interactively and test it immediately.
    """

    __tablename__ = "im_channel_configs"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    bound_chat_id: Mapped[str] = mapped_column(String(255), default="")
    last_test_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_test_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class RatingSnapshot(Base):
    __tablename__ = "rating_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    system: Mapped[str] = mapped_column(String(32))  # newsguard/adfontes/allsides/...
    status: Mapped[str] = mapped_column(String(32), default="not_connected")  # not_connected/connected
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bias: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    license_note: Mapped[str] = mapped_column(Text, default="")