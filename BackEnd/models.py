# Third file to create is the modles file. This is to create databse tables
from sqlalchemy import Column, Integer , String, ForeignKey, Enum , DateTime , Text , CHAR
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
Base = declarative_base() 


class admin(Base):
    __tablename__="admin"
    id = Column(Integer,primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique =True)  
    created_at = Column(DateTime, nullable=False)
      
    def set_password(self,password):
        self.passwword_hash = generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    
class school(Base):
    __tablename__ = "school"    
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
    
    booking = relationship("bookings",back_populates="school", cascade="all,delete-orphan")
    
    def set_password(self,password):
        self.passwword_hash = generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    
class company(Base):
    __tablename__ = "company"
    company_id = Column(Integer , primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    company_email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    industry_type = Column(String(100), nullable=False)
    contact_person = Column(String(100), nullable=False)
    phone_number  = Column(String(20), nullable=False)
    website = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    is_verified = Column(Enum('True'| 'False'), default='False')
    created_at = Column(DateTime, nullable=False)
    
    available_time = relationship("available_time", back_populates="company", cascade = "all, delete_orphan")

    def set_password(self,password):
        self.set_password = generate_password_hash(password)
    def check_password(self,password):  
        self.check_password = check_password_hash(password)
        
class available_time(Base):
    __tablename__ = 'available_time'
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(ForeignKey, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=False)
    
    company = relationship("company", back_populates = "available_time")
    
  
class booking(Base):
    __tablename__ = 'booking'  
    school_id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(ForeignKey, Integer)
    status = Column(Enum('pending'| 'confirmed' | 'cancelled') default='pending')
    created_at = Column(DateTime, nullable=False)
    
    school = relationship("School", back_populates="booking")
    
    
    