from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

# ProjectMetrics schemas
class ProjectMetricsBase(BaseModel):
    metricid: str
    metric_name: str
    metric_desc: str
    value: int

class ProjectMetricsCreate(ProjectMetricsBase):
    projectid: int

class ProjectMetrics(ProjectMetricsBase):
    id: int
    projectid: int

    class Config:
        from_attributes = True

# ProjectSummary schemas
class ProjectSummaryBase(BaseModel):
    E_score: int
    S_score: int
    G_score: int
    ESG_score: int
    summary: str

class ProjectSummaryCreate(ProjectSummaryBase):
    projectid: int

class ProjectSummary(ProjectSummaryBase):
    summaryid: int
    projectid: int

    class Config:
        from_attributes = True

# ProjectChat schemas
class ProjectChatBase(BaseModel):
    chat_history: Dict[str, Any]
    terminated: int

class ProjectChatCreate(ProjectChatBase):
    projectid: int

class ProjectChat(ProjectChatBase):
    chatid: int
    projectid: int

    class Config:
        from_attributes = True

# Project schemas
class ProjectBase(BaseModel):
    company_name: str
    title: str
    cost: int

class ProjectCreate(ProjectBase):
    orgid: int

class Project(ProjectBase):
    projectid: int
    orgid: int
    create_date: datetime
    project_chats: List[ProjectChat] = []
    project_summaries: List[ProjectSummary] = []
    project_metrics: List[ProjectMetrics] = []

    class Config:
        from_attributes = True

# Organization schemas
class OrganizationBase(BaseModel):
    name: str
    w1: int
    w2: int
    budget: int

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    orgid: int
    projects: List[Project] = []

    class Config:
        from_attributes = True

# Response Models for nested data
class ProjectWithDetails(Project):
    organization: Organization
    project_chats: List[ProjectChat]
    project_summaries: List[ProjectSummary]
    project_metrics: List[ProjectMetrics]

    class Config:
        from_attributes = True