from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, DECIMAL, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    unit = Column(String(100))
    job = Column(String(100))
    group_shift = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    handovers = relationship('Handover', back_populates='creator', foreign_keys='Handover.created_by')

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    req_id = Column(String(100), unique=True, nullable=False)
    mode = Column(String(50))
    requester = Column(String(255))
    category = Column(String(100))
    subcategory = Column(String(100))
    subject = Column(Text)
    technician = Column(String(255))
    sla_name = Column(String(100))
    priority = Column(String(50))
    created_time = Column(DateTime)
    resolved_time = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NetworkLink(Base):
    __tablename__ = 'network_links'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    sensor_name = Column(String(255))
    device = Column(String(255))
    location = Column(String(255))
    isp = Column(String(100))
    target_sla = Column(DECIMAL(5, 2))
    up_time = Column(Integer)
    down_time = Column(Integer)
    avg_traffic = Column(DECIMAL(10, 2))
    volume = Column(DECIMAL(10, 2))
    last_updated = Column(DateTime, default=datetime.utcnow)

class SocEvent(Base):
    __tablename__ = 'soc_events'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    date = Column(DateTime)
    threat_name = Column(String(255))
    category = Column(String(100))
    action = Column(String(100))
    severity = Column(String(50))
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)

class Handover(Base):
    __tablename__ = 'handovers'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    text = Column(Text, nullable=False)
    site = Column(String(255))
    priority = Column(String(50))
    date = Column(DateTime)
    shift = Column(String(50))
    open = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship('User', back_populates='handovers', foreign_keys=[created_by])

class AccessRequest(Base):
    __tablename__ = 'access_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
