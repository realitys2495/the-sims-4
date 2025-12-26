from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import asyncio
import aiohttp
import re
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class DownloadConfig(BaseModel):
    google_drive_url: str
    expected_checksum: Optional[str] = None

class DownloadStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = "TheSims4.zip"
    total_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    status: str = "idle"  # idle, downloading, paused, verifying, verified, extracting, installing, completed, error
    speed: float = 0.0
    eta: str = "--:--:--"
    checksum_status: str = "pending"
    checksum_calculated: Optional[str] = None
    google_drive_url: Optional[str] = None
    download_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DownloadCreate(BaseModel):
    google_drive_url: str
    filename: Optional[str] = "TheSims4.zip"
    download_path: Optional[str] = "C:\\Users\\Downloads\\TheSims4"

# Global download state
download_tasks = {}
download_paused = {}

def extract_file_id(url: str) -> str:
    """Extract file ID from Google Drive URL"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def get_download_url(file_id: str) -> str:
    """Get direct download URL for Google Drive file"""
    return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

async def get_file_info(file_id: str) -> dict:
    """Get file info from Google Drive"""
    download_url = get_download_url(file_id)
    async with aiohttp.ClientSession() as session:
        async with session.head(download_url, allow_redirects=True) as response:
            content_length = response.headers.get('Content-Length', 0)
            content_disposition = response.headers.get('Content-Disposition', '')
            filename = "TheSims4.zip"
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            return {
                "size": int(content_length) if content_length else 81604378624,  # 76GB default
                "filename": filename
            }

@api_router.get("/")
async def root():
    return {"message": "The Sims 4 Downloader API"}

@api_router.post("/downloads", response_model=DownloadStatus)
async def create_download(download: DownloadCreate):
    """Initialize a new download"""
    file_id = extract_file_id(download.google_drive_url)
    
    try:
        file_info = await get_file_info(file_id)
    except Exception:
        file_info = {"size": 81604378624, "filename": download.filename or "TheSims4.zip"}
    
    status = DownloadStatus(
        filename=download.filename or file_info.get("filename", "TheSims4.zip"),
        total_size=file_info.get("size", 81604378624),
        google_drive_url=download.google_drive_url,
        download_path=download.download_path,
        status="idle"
    )
    
    doc = status.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.downloads.insert_one(doc)
    download_paused[status.id] = False
    
    return status

@api_router.get("/downloads/{download_id}", response_model=DownloadStatus)
async def get_download_status(download_id: str):
    """Get download status"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    for field in ['created_at', 'updated_at']:
        if isinstance(doc.get(field), str):
            doc[field] = datetime.fromisoformat(doc[field])
    
    return DownloadStatus(**doc)

@api_router.get("/downloads", response_model=List[DownloadStatus])
async def list_downloads():
    """List all downloads"""
    docs = await db.downloads.find({}, {"_id": 0}).to_list(100)
    for doc in docs:
        for field in ['created_at', 'updated_at']:
            if isinstance(doc.get(field), str):
                doc[field] = datetime.fromisoformat(doc[field])
    return docs

@api_router.post("/downloads/{download_id}/start")
async def start_download(download_id: str, background_tasks: BackgroundTasks):
    """Start or resume download"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download_paused[download_id] = False
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "downloading", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    background_tasks.add_task(simulate_download, download_id, doc.get('total_size', 81604378624))
    
    return {"message": "Download started", "id": download_id}

async def simulate_download(download_id: str, total_size: int):
    """Simulate download progress for demo purposes"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    downloaded = doc.get('downloaded_size', 0) if doc else 0
    
    chunk_size = total_size // 100  # 1% per update
    
    while downloaded < total_size:
        if download_paused.get(download_id, False):
            await db.downloads.update_one(
                {"id": download_id},
                {"$set": {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return
        
        downloaded += chunk_size
        if downloaded > total_size:
            downloaded = total_size
        
        progress = (downloaded / total_size) * 100
        speed = chunk_size / 0.5  # bytes per second
        remaining_bytes = total_size - downloaded
        eta_seconds = remaining_bytes / speed if speed > 0 else 0
        
        hours = int(eta_seconds // 3600)
        minutes = int((eta_seconds % 3600) // 60)
        seconds = int(eta_seconds % 60)
        eta = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {
                "downloaded_size": downloaded,
                "progress": progress,
                "speed": speed,
                "eta": eta,
                "status": "downloading",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        await asyncio.sleep(0.5)
    
    # Download complete, start verification
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "verifying",
            "checksum_status": "calculating",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Simulate checksum calculation
    await asyncio.sleep(3)
    
    fake_checksum = hashlib.sha256(f"TheSims4_{download_id}".encode()).hexdigest()
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "verified",
            "checksum_status": "verified",
            "checksum_calculated": fake_checksum,
            "progress": 100,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Auto-start extraction after verification
    await asyncio.sleep(1)
    await simulate_extraction(download_id)

async def simulate_extraction(download_id: str):
    """Simulate ZIP extraction process"""
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "extracting",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Simulate extraction time
    await asyncio.sleep(4)
    
    # Extraction complete, finalize installation
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "installing",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await asyncio.sleep(2)
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

@api_router.post("/downloads/{download_id}/pause")
async def pause_download(download_id: str):
    """Pause download"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download_paused[download_id] = True
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Download paused", "id": download_id}

@api_router.post("/downloads/{download_id}/resume")
async def resume_download(download_id: str, background_tasks: BackgroundTasks):
    """Resume paused download"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download_paused[download_id] = False
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "downloading", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    background_tasks.add_task(simulate_download, download_id, doc.get('total_size', 81604378624))
    
    return {"message": "Download resumed", "id": download_id}

@api_router.delete("/downloads/{download_id}")
async def delete_download(download_id: str):
    """Delete a download"""
    download_paused[download_id] = True
    result = await db.downloads.delete_one({"id": download_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"message": "Download deleted", "id": download_id}

@api_router.post("/downloads/{download_id}/install")
async def start_installation(download_id: str, background_tasks: BackgroundTasks):
    """Start installation after download"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    if doc.get('status') != 'verified':
        raise HTTPException(status_code=400, detail="Download must be verified before installation")
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "installing", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    background_tasks.add_task(simulate_installation, download_id)
    
    return {"message": "Installation started", "id": download_id}

async def simulate_installation(download_id: str):
    """Simulate installation process"""
    await asyncio.sleep(5)
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
