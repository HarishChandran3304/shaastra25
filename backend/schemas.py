from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Project schemas
class ProjectBase(BaseModel):
    company_name: str
    title: str
    summary: str
    cost: int

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    projectid: int
    orgid: int
    create_date: datetime

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