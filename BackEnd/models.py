# Third file to create is the modles file. This is to create databse tables
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
    email = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class School(Base, PasswordMixin):
    __tablename__ = "schools"

    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    school_address = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False)
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    bookings = relationship("Booking", back_populates="school", cascade="all, delete-orphan")


class Company(Base, PasswordMixin):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    company_email = Column(String(100), nullable=False, unique=True)
    industry_type = Column(String(100), nullable=False)
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    available_times = relationship("AvailableTime", back_populates="company", cascade="all, delete-orphan")


class AvailableTime(Base):
    __tablename__ = "available_times"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    company = relationship("Company", back_populates="available_times")
    bookings = relationship("Booking", back_populates="available_time", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("available_times.schedule_id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.school_id", ondelete="CASCADE"), nullable=False)
    status = Column(
        Enum("pending", "confirmed", "cancelled", name="booking_status"),
        nullable=False,
        server_default=text("'pending'")
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    school = relationship("School", back_populates="bookings")
    available_time = relationship("AvailableTime", back_populates="bookings")
