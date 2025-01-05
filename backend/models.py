from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db import Base

class Organization(Base):
    __tablename__ = "organizations"

    orgid = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    w1 = Column(Integer)
    w2 = Column(Integer)
    budget = Column(Integer)

    projects = relationship("Project", back_populates="organization")

class Project(Base):
    __tablename__ = "projects"

    orgid = Column(Integer, ForeignKey("organizations.orgid"))
    projectid = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    title = Column(String)
    create_date = Column(DateTime)
    summary = Column(String)
    cost = Column(Integer)

    organization = relationship("Organization", back_populates="projects")