# Third file to create is the models file. This is to create database tables
from config import engine
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Enum, DateTime, Text, Boolean, text,
    UniqueConstraint, CheckConstraint, and_, or_
)
from sqlalchemy.orm import declarative_base, relationship, Session
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


# Password Hashing Mixin
class PasswordMixin:
    password_hash = Column(String(255), nullable=False)

    def set_password(self, password: str):
        """Hashes and stores a password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Validates a password against stored hash"""
        return check_password_hash(self.password_hash, password)


# Utility: Check Overlapping Schedules 
def is_overlapping(session: Session, company_id: int, start_date, end_date) -> bool:
    """Check if a new schedule overlaps with existing schedules for a company"""
    return session.query(AvailableTime).filter(
        AvailableTime.company_id == company_id,
        or_(
            and_(AvailableTime.start_date <= start_date, AvailableTime.end_date > start_date),
            and_(AvailableTime.start_date < end_date, AvailableTime.end_date >= end_date),
            and_(AvailableTime.start_date >= start_date, AvailableTime.end_date <= end_date),
        )
    ).first() is not None


# Admin Table
class Admin(Base, PasswordMixin):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<Admin(id={self.id}, email={self.email})>"


# School Table 
class School(Base, PasswordMixin):
    __tablename__ = "schools"

    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255), nullable=False, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    school_address = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False, index=True)
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)

    is_verified = Column(Boolean, default=False, index=True)  # Must be approved by admin
    is_active   = Column(Boolean, default=True, index=True)   # Soft delete flag ✅

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    bookings = relationship("Booking", back_populates="school", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<School(id={self.school_id}, name={self.school_name}, active={self.is_active})>"


# Company Table 
class Company(Base, PasswordMixin):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    company_email = Column(String(100), nullable=False, unique=True, index=True)
    industry_type = Column(String(100), nullable=False, index=True)
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)

    is_verified = Column(Boolean, default=False, index=True)  # Must be approved by admin
    is_active   = Column(Boolean, default=True, index=True)   # Soft delete flag ✅

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    available_times = relationship("AvailableTime", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.company_id}, name={self.company_name}, active={self.is_active})>"

# Available Times Table 
class AvailableTime(Base):
    __tablename__ = "available_times"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    company = relationship("Company", back_populates="available_times")
    bookings = relationship("Booking", back_populates="available_time", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="check_valid_schedule_dates"),
    )

    def __repr__(self):
        return f"<AvailableTime(id={self.schedule_id}, company_id={self.company_id})>"


# Booking Table 
class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("available_times.schedule_id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.school_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        Enum("pending", "confirmed", "cancelled", name="booking_status"),
        nullable=False,
        server_default=text("'pending'"),
        index=True
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    school = relationship("School", back_populates="bookings")
    available_time = relationship("AvailableTime", back_populates="bookings")

    __table_args__ = (
        UniqueConstraint("schedule_id", "school_id", name="uq_school_schedule_booking"),
    )

    def __repr__(self):
        return f"<Booking(id={self.booking_id}, status={self.status})>"
    
if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")