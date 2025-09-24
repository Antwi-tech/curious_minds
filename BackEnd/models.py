# Third file to create is the modles file. This is to create databse tables
from sqlalchemy import Column, Integer , String, ForeignKey, Enum , DateTime , Text , CHAR
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
Base = declarative_base() 

"""
-- Admins
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

"""


class admin(Base):
    __tablename__="admin"
    id = Column(Integer,primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
        


"""
-- Schools
CREATE TABLE IF NOT EXISTS schools (
    school_id INT AUTO_INCREMENT PRIMARY KEY,
    school_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    region VARCHAR(100),
    contact_person VARCHAR(100),
    phone_number VARCHAR(20),
    website VARCHAR(100),
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
class schools(Base):
    __tablename__ = "schools"    
    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255),nullable=False)
    email = Column(String(100), nullable=False,unique=True)
    password_hash = Column(String(255), nullable=False)
    school_address = Column(String(255), nullable=False)
    region = Column(String(100), nulable=False)
    contact_person = Column(String(100), nullable= False)
    phone_number = Column(String(20), nullable=False)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Enum('True'| 'False'), default='False')
    created_at = Column(DateTime, nullable=False)
    
    booking = relationship("bookings",back_populates="school", cascade="all,delate-orphan")
    
    