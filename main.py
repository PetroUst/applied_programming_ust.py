import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import expression

engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306/pp", echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    Username = Column(String(30), primary_key=True)
    Name = Column(String(30), nullable=False)
    Surname = Column(String(30), nullable=False)
    Email = Column(String(50), nullable=False,unique=True)
    Password = Column(String(300), nullable=False)
    Ticket = relationship("Ticket", overlaps="Ticket")
    Role = Column(String(30), nullable=False)

class Ticket(Base):
    __tablename__ = 'Tickets'
    TicketId = Column(Integer, primary_key=True)
    Price = Column(Integer, nullable=False)
    IsBooked = Column(sqlalchemy.Boolean, nullable=False)
    IsPaid = Column(sqlalchemy.Boolean, nullable=False)
    # Line = Column(Integer, nullable=True)
    # Place = Column(Integer, nullable=True)
    Username = Column(String(15), ForeignKey("Users.Username"))
    EventId = Column(Integer, ForeignKey("Events.EventId"))
    Event = relationship("Event", overlaps="Ticket")
    User = relationship("User", overlaps="Ticket")

class Event(Base):
    __tablename__ = "Events"
    EventId = Column(Integer, primary_key=True)
    EventName = Column(String(40), nullable=False)
    Time = Column(String(20), nullable=False)
    City = Column(String(15), nullable=False)
    Location = Column(String(30), nullable=False)
    Price = Column(Integer, nullable=False)
    MaxTickets = Column(Integer,nullable=False)
    Ticket = relationship("Ticket",overlaps="Ticket")
    Username = Column(String(15), ForeignKey("Users.Username"))


# Base.metadata.create_all(engine)


