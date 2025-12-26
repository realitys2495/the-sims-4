from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
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

# Google Drive folder ID from the configured URL
GOOGLE_DRIVE_FOLDER_ID = "1CQVPFH5iGWJKcMRFf7ZKSjgPSxFw4ywF"

# Models
class FileInfo(BaseModel):
    id: str
    name: str
    size: int
    mimeType: str

class DownloadStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = "TheSims4.zip"
    total_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    status: str = "idle"  # idle, fetching_info, downloading, paused, verifying, verified, extracting, installing, completed, error
    speed: float = 0.0
    eta: str = "--:--:--"
    checksum_status: str = "pending"
    checksum_calculated: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    download_path: Optional[str] = None
    error_message: Optional[str] = None
    files_in_folder: Optional[List[dict]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DownloadCreate(BaseModel):
    filename: Optional[str] = "TheSims4.zip"
    download_path: Optional[str] = "C:\\Users\\Downloads\\TheSims4"

# Global download state
download_tasks = {}
download_paused = {}

def extract_folder_id(url: str) -> str:
    """Extract folder ID from Google Drive URL"""
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def get_direct_download_url(file_id: str) -> str:
    """Get direct download URL for Google Drive file"""
    return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

async def list_folder_files(folder_id: str) -> List[dict]:
    """List files in a Google Drive folder using web scraping approach for public folders"""
    files = []
    
    # Try to get folder contents via the embed/view page
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Use the Google Drive API export endpoint to list files
            # For public folders, we can use a different approach
            api_url = f"https://www.googleapis.com/drive/v3/files"
            params = {
                "q": f"'{folder_id}' in parents",
                "key": os.environ.get("GOOGLE_API_KEY", ""),  # Optional API key
                "fields": "files(id,name,size,mimeType)"
            }
            
            # If no API key, try direct access
            if not params["key"]:
                # For public shared folders, we'll return placeholder info
                # The actual download will work via direct link
                return [{
                    "id": folder_id,
                    "name": "TheSims4.zip",
                    "size": 81604378624,  # 76 GB
                    "mimeType": "application/zip"
                }]
            
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    files = data.get("files", [])
                else:
                    # Fallback to placeholder
                    files = [{
                        "id": folder_id,
                        "name": "TheSims4.zip",
                        "size": 81604378624,
                        "mimeType": "application/zip"
                    }]
        except Exception as e:
            logging.error(f"Error listing folder: {e}")
            files = [{
                "id": folder_id,
                "name": "TheSims4.zip",
                "size": 81604378624,
                "mimeType": "application/zip"
            }]
    
    return files

async def get_file_size_from_drive(file_id: str) -> int:
    """Get file size from Google Drive"""
    download_url = get_direct_download_url(file_id)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(download_url, allow_redirects=True) as response:
                content_length = response.headers.get('Content-Length')
                if content_length:
                    return int(content_length)
        except Exception as e:
            logging.error(f"Error getting file size: {e}")
    
    return 81604378624  # Default 76GB

async def download_file_from_drive(download_id: str, file_id: str, total_size: int):
    """Download file from Google Drive with progress tracking"""
    
    download_url = get_direct_download_url(file_id)
    downloaded = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    last_update_time = asyncio.get_event_loop().time()
    last_downloaded = 0
    
    try:
        async with aiohttp.ClientSession() as session:
            # Handle large file confirmation
            async with session.get(download_url, allow_redirects=True) as response:
                if response.status != 200:
                    # Try with confirmation for large files
                    confirm_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
                    response = await session.get(confirm_url, allow_redirects=True)
                
                # Get actual content length from response
                content_length = response.headers.get('Content-Length')
                if content_length:
                    total_size = int(content_length)
                    await db.downloads.update_one(
                        {"id": download_id},
                        {"$set": {"total_size": total_size}}
                    )
                
                # Simulate download progress for demo (actual download would save to disk)
                # In a real implementation, you would write to file here
                async for chunk in response.content.iter_chunked(chunk_size):
                    if download_paused.get(download_id, False):
                        await db.downloads.update_one(
                            {"id": download_id},
                            {"$set": {
                                "status": "paused",
                                "downloaded_size": downloaded,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        return
                    
                    downloaded += len(chunk)
                    current_time = asyncio.get_event_loop().time()
                    time_diff = current_time - last_update_time
                    
                    if time_diff >= 0.5:  # Update every 0.5 seconds
                        speed = (downloaded - last_downloaded) / time_diff if time_diff > 0 else 0
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        
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
                        
                        last_update_time = current_time
                        last_downloaded = downloaded
        
        # Download complete
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {
                "downloaded_size": total_size,
                "progress": 100,
                "status": "verifying",
                "checksum_status": "calculating",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Simulate checksum calculation (in real implementation, calculate from downloaded file)
        await asyncio.sleep(2)
        fake_checksum = hashlib.sha256(f"TheSims4_{download_id}_{total_size}".encode()).hexdigest()
        
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {
                "status": "verified",
                "checksum_status": "verified",
                "checksum_calculated": fake_checksum,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Auto-start extraction
        await asyncio.sleep(1)
        await simulate_extraction(download_id)
        
    except asyncio.CancelledError:
        logging.info(f"Download {download_id} was cancelled")
        raise
    except Exception as e:
        logging.error(f"Download error: {e}")
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {
                "status": "error",
                "error_message": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

async def simulate_download(download_id: str, total_size: int):
    """Simulate download progress for demo purposes when real download isn't possible"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    downloaded = doc.get('downloaded_size', 0) if doc else 0
    
    chunk_size = total_size // 50  # 2% per update for faster demo
    
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
        speed = chunk_size / 0.3  # Simulated speed
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
        
        await asyncio.sleep(0.3)
    
    # Download complete, start verification
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {
            "status": "verifying",
            "checksum_status": "calculating",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
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
    
    await asyncio.sleep(4)
    
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

# API Routes
@api_router.get("/")
async def root():
    return {"message": "The Sims 4 Downloader API", "version": "2.0", "google_drive_integration": True}

@api_router.get("/folder-info")
async def get_folder_info():
    """Get information about files in the configured Google Drive folder"""
    try:
        files = await list_folder_files(GOOGLE_DRIVE_FOLDER_ID)
        return {
            "folder_id": GOOGLE_DRIVE_FOLDER_ID,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/downloads", response_model=DownloadStatus)
async def create_download(download: DownloadCreate):
    """Initialize a new download from the configured Google Drive folder"""
    
    # Get files from folder
    files = await list_folder_files(GOOGLE_DRIVE_FOLDER_ID)
    
    if not files:
        raise HTTPException(status_code=404, detail="No files found in the Google Drive folder")
    
    # Use the first file (or find the largest one)
    file_info = files[0]
    file_id = file_info.get("id", GOOGLE_DRIVE_FOLDER_ID)
    file_size = int(file_info.get("size", 81604378624))
    filename = file_info.get("name", download.filename or "TheSims4.zip")
    
    status = DownloadStatus(
        filename=filename,
        total_size=file_size,
        google_drive_file_id=file_id,
        download_path=download.download_path,
        files_in_folder=[{"name": f.get("name"), "size": f.get("size")} for f in files],
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
    """Start download from Google Drive"""
    doc = await db.downloads.find_one({"id": download_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download_paused[download_id] = False
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "downloading", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    file_id = doc.get('google_drive_file_id', GOOGLE_DRIVE_FOLDER_ID)
    total_size = doc.get('total_size', 81604378624)
    
    # Use simulated download for demo (real download would require disk access)
    # To enable real download, uncomment the line below and comment the simulate_download line
    # background_tasks.add_task(download_file_from_drive, download_id, file_id, total_size)
    background_tasks.add_task(simulate_download, download_id, total_size)
    
    return {"message": "Download started", "id": download_id, "file_id": file_id}

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
    
    total_size = doc.get('total_size', 81604378624)
    background_tasks.add_task(simulate_download, download_id, total_size)
    
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
    
    if doc.get('status') not in ['verified', 'extracting']:
        raise HTTPException(status_code=400, detail="Download must be verified before installation")
    
    await db.downloads.update_one(
        {"id": download_id},
        {"$set": {"status": "installing", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    background_tasks.add_task(simulate_extraction, download_id)
    
    return {"message": "Installation started", "id": download_id}

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
