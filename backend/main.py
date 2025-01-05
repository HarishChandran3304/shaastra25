from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

import shutil
import os
from datetime import datetime
from pathlib import Path
import asyncio

import models, schemas
from db import engine, get_db
from Scripts.process import DocumentQuerySystem, answer_with_llm


UPLOAD_DIR = Path("uploads/")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/organizations/", response_model=schemas.Organization)
def create_organization(organization: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    db_organization = models.Organization(**organization.dict())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization

@app.get("/organizations/", response_model=List[schemas.Organization])
def read_organizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    organizations = db.query(models.Organization).offset(skip).limit(limit).all()
    return organizations

@app.get("/organizations/{organization_id}", response_model=schemas.Organization)
def read_organization(organization_id: int, db: Session = Depends(get_db)):
    db_organization = db.query(models.Organization).filter(models.Organization.orgid == organization_id).first()
    if db_organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return db_organization

@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects

@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.projectid == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.post("/project_chats/", response_model=schemas.ProjectChat)
def create_project_chat(project_chat: schemas.ProjectChatCreate, db: Session = Depends(get_db)):
    db_project_chat = models.ProjectChat(**project_chat.dict())
    db.add(db_project_chat)
    db.commit()
    db.refresh(db_project_chat)
    return db_project_chat

@app.get("/project_chats/", response_model=List[schemas.ProjectChat])
def read_project_chats(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    project_chats = db.query(models.ProjectChat).offset(skip).limit(limit).all()
    return project_chats

@app.get("/project_chats/{chat_id}", response_model=schemas.ProjectChat)
def read_project_chat(chat_id: int, db: Session = Depends(get_db)):
    db_project_chat = db.query(models.ProjectChat).filter(models.ProjectChat.chatid == chat_id).first()
    if db_project_chat is None:
        raise HTTPException(status_code=404, detail="Project Chat not found")
    return db_project_chat

@app.post("/project_summaries/", response_model=schemas.ProjectSummary)
def create_project_summary(project_summary: schemas.ProjectSummary, db: Session = Depends(get_db)):
    db_project_summary = models.ProjectSummary(**project_summary.dict())
    db.add(db_project_summary)
    db.commit()
    db.refresh(db_project_summary)
    return db_project_summary

@app.get("/project_summaries/", response_model=List[schemas.ProjectSummary])
def read_project_summaries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    project_summaries = db.query(models.ProjectSummary).offset(skip).limit(limit).all()
    return project_summaries

@app.get("/project_summaries/{summary_id}", response_model=schemas.ProjectSummary)
def read_project_summary(summary_id: int, db: Session = Depends(get_db)):
    db_project_summary = db.query(models.ProjectSummary).filter(models.ProjectSummary.summaryid == summary_id).first()
    if db_project_summary is None:
        raise HTTPException(status_code=404, detail="Project Summary not found")
    return db_project_summary

@app.post("/project_metrics/", response_model=schemas.ProjectMetrics)
def create_project_metrics(project_metrics: schemas.ProjectMetrics, db: Session = Depends(get_db)):
    db_project_metrics = models.ProjectMetrics(**project_metrics.dict())
    db.add(db_project_metrics)
    db.commit()
    db.refresh(db_project_metrics)
    return db_project_metrics

@app.get("/project_metrics/", response_model=List[schemas.ProjectMetrics])
def read_project_metrics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    project_metrics = db.query(models.ProjectMetrics).offset(skip).limit(limit).all()
    return project_metrics

@app.get("/project_metrics/{metric_id}", response_model=schemas.ProjectMetrics)
def read_project_metrics(metric_id: int, db: Session = Depends(get_db)):
    db_project_metrics = db.query(models.ProjectMetrics).filter(models.ProjectMetrics.id == metric_id).first()
    if db_project_metrics is None:
        raise HTTPException(status_code=404, detail="Project Metrics not found")
    return db_project_metrics


@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Verify file type
        if not file.content_type == "application/pdf":
            return JSONResponse(
                status_code=400,
                content={"message": "Only PDF files are allowed"}
            )
        
        # Create unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        secure_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / secure_filename
        
        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Summarize the document
        query_system = DocumentQuerySystem(file_path)
        response = query_system.summarize()
        print(response.text)

        # Add to database
        db_attachment = models.Attachments(file_name=secure_filename, file_path=str(file_path), summary=response.text)
        print(db_attachment.summary)
        db.add(db_attachment)
        db.commit()
        db.refresh(db_attachment)
        
        return {
            "filename": secure_filename,
            "file_path": str(file_path),
            "summary": response,
            "message": "File uploaded successfully"
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"An error occurred: {str(e)}"}
        )
    
    finally:
        file.file.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, filename: str, db: Session = Depends(get_db)):
    await websocket.accept()

    summary = db.query(models.Attachments, ).filter(models.Attachments.file_name == filename).first().summary
    if summary is None:
        await websocket.send_text("File not found")
        return
    
    scenario = "Summary until now: " + str(summary)
    string = f'''The user's responses till now: '''

    while True:
        result = answer_with_llm(scenario, string)
        await websocket.send_text(result["response"])

        if result["status"] == 1:
            print("Conversation ended")
            break

        else:
            scenario = await websocket.receive_text()
            string += "\n" + scenario
