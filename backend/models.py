from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
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
    cost = Column(Integer)

    organization = relationship("Organization", back_populates="projects")
    project_chats = relationship("ProjectChat", back_populates="project")
    project_summaries = relationship("ProjectSummary", back_populates="project")
    project_metrics = relationship("ProjectMetrics", back_populates="project")

class ProjectChat(Base):
    __tablename__ = "project_chats"

    chatid = Column(Integer, primary_key=True, index=True)
    projectid = Column(Integer, ForeignKey("projects.projectid"))
    chat_history = Column(JSON)
    terminated = Column(Integer)  # 0 if not terminated, 1 if terminated

    project = relationship("Project", back_populates="project_chats")

class ProjectSummary(Base):
    __tablename__ = "project_summaries"

    summaryid = Column(Integer, primary_key=True, index=True)
    projectid = Column(Integer, ForeignKey("projects.projectid"))
    summary = Column(String)
    E_score = Column(Integer)
    S_score = Column(Integer)
    G_score = Column(Integer)
    ESG_score = Column(Integer)

    project = relationship("Project", back_populates="project_summaries")

class ProjectMetrics(Base):
    __tablename__ = "project_metrics"

    id = Column(Integer, primary_key=True, index=True)
    projectid = Column(Integer, ForeignKey("projects.projectid"))
    metricid = Column(String)
    metric_name = Column(String)
    metric_desc = Column(String)
    value = Column(Integer)

    project = relationship("Project", back_populates="project_metrics")

class Attachments(Base):
    __tablename__ = "attachments"

    file_name = Column(String, primary_key=True, index=True)
    file_path = Column(String)
    summary = Column(String)
