# Third file to create is the models file. This is to create database tables
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Text, Boolean, text
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class PasswordMixin:
    password_hash = Column(String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Admin(Base, PasswordMixin):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=False, unique=True, index=True)  # ✅ indexed for login/search
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)  # ✅ faster sorting/filtering


class School(Base, PasswordMixin):
    __tablename__ = "schools"

    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255), nullable=False, index=True)  # ✅ often searched by name
    email = Column(String(100), nullable=False, unique=True, index=True)  # ✅ for login
    school_address = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False, index=True)  # ✅ filter schools by region
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)  # ✅ sometimes searched
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False, index=True)  # ✅ filter verified schools
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)

    bookings = relationship("Booking", back_populates="school", cascade="all, delete-orphan")


class Company(Base, PasswordMixin):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)  # ✅ search by name
    company_email = Column(String(100), nullable=False, unique=True, index=True)  # ✅ for login
    industry_type = Column(String(100), nullable=False, index=True)  # ✅ filter by industry
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)  # ✅ sometimes searched
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False, index=True)  # ✅ filter verified companies
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)

    available_times = relationship("AvailableTime", back_populates="company", cascade="all, delete-orphan")


class AvailableTime(Base):
    __tablename__ = "available_times"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)  # ✅ FK joins
    start_date = Column(DateTime, nullable=False, index=True)  # ✅ scheduling queries
    end_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)

    company = relationship("Company", back_populates="available_times")
    bookings = relationship("Booking", back_populates="available_time", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("available_times.schedule_id", ondelete="CASCADE"), nullable=False, index=True)  # ✅ FK joins
    school_id = Column(Integer, ForeignKey("schools.school_id", ondelete="CASCADE"), nullable=False, index=True)  # ✅ FK joins
    status = Column(
        Enum("pending", "confirmed", "cancelled", name="booking_status"),
        nullable=False,
        server_default=text("'pending'"),
        index=True  # ✅ filter bookings by status
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)

    school = relationship("School", back_populates="bookings")
    available_time = relationship("AvailableTime", back_populates="bookings")
