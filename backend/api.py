#!/usr/bin/env python3
"""
FastAPI Backend for GraphRAG Contract Processing Frontend
"""

import os
import sys
import asyncio
import json
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uuid

# Imports from src package

from src.batch_ingest_contracts import EnhancedBatchProcessor
from src.direct_securities_agent import DirectSecuritiesAgent
from src.neo4j_persistence import backup_neo4j_data, restore_neo4j_data

app = FastAPI(title="GraphRAG Contract Processing API", version="1.0.0")

# Constants
CACHE_FILE = "processed_contracts_cache.json"

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default port for local development  
        "https://cont-rag.vercel.app",  # Your Vercel frontend URL (corrected)
        "https://contrag-graphrag.vercel.app",  # Alternative Vercel URL
        "https://contrag.onrender.com",  # Render API URL
        "wss://contrag.onrender.com"  # Render websocket URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class AppState:
    def __init__(self):
        self.processor = None
        self.agent = None
        self.securities_agent = None  # Add this for the new chat system
        self.websocket_connections = []
        self.current_processing_job = None
        self.upload_directory = "backend/uploads"
        self.processed_data = {}
        self.current_session_contracts = {}  # Track contracts processed in current session
        
        # Ensure upload directory exists
        os.makedirs(self.upload_directory, exist_ok=True)

state = AppState()

# Pydantic models
class ProcessingStatus(BaseModel):
    status: str  # "idle", "processing", "completed", "error"
    progress: int
    current_file: Optional[str] = None
    total_files: int = 0
    processed_files: int = 0
    message: str = ""
    job_id: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    timestamp: datetime = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = None

class ContractSummary(BaseModel):
    title: str
    contract_type: str
    summary: str
    execution_date: Optional[str]
    parties_count: int
    securities_count: int
    file_path: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.disconnect(connection)

manager = ConnectionManager()

# Helper functions
async def send_log_message(message: str, level: str = "info"):
    """Send log message to all connected WebSocket clients"""
    await manager.broadcast_message({
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })

async def send_status_update(status: ProcessingStatus):
    """Send status update to all connected WebSocket clients"""
    await manager.broadcast_message({
        "type": "status",
        "data": status.dict()
    })

# Helper function to get API key from request
def get_api_key_from_request(request: Request, x_api_key: Optional[str] = Header(None)) -> str:
    """Extract API key from request headers or fall back to environment variable"""
    # Try to get from header first
    if x_api_key:
        return x_api_key
    
    # Fall back to environment variable (for backward compatibility)
    env_api_key = os.getenv("GOOGLE_API_KEY")
    if env_api_key:
        return env_api_key
    
    raise HTTPException(
        status_code=401, 
        detail="API key required. Please provide your Gemini API key in the X-API-Key header."
    )

# API Endpoints

@app.get("/")
async def root():
    return {"message": "GraphRAG Contract Processing API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "API is running"
    }

class ApiKeyRequest(BaseModel):
    api_key: str

@app.post("/validate-api-key")
async def validate_api_key(request: ApiKeyRequest):
    """Validate a Gemini API key"""
    try:
        # Set the API key temporarily for validation
        os.environ["GOOGLE_API_KEY"] = request.api_key
        
        # Try to initialize the pipeline to test the API key
        from src.securities_pipeline_runner import SecuritiesGraphRAGPipeline
        
        # Create a minimal test instance
        pipeline = SecuritiesGraphRAGPipeline()
        
        # If we get here without error, the API key is valid
        return {"valid": True, "message": "API key is valid"}
        
    except Exception as e:
        # If any error occurs, the API key is likely invalid
        return JSONResponse(
            status_code=400,
            content={"valid": False, "message": f"Invalid API key: {str(e)}"}
        )

@app.get("/status", response_model=ProcessingStatus)
async def get_status():
    """Get current processing status"""
    if state.current_processing_job:
        return state.current_processing_job
    
    return ProcessingStatus(
        status="idle",
        progress=0,
        total_files=0,
        processed_files=0,
        message="Ready to process contracts"
    )

@app.post("/upload")
async def upload_contracts(request: Request, files: List[UploadFile] = File(...), x_api_key: Optional[str] = Header(None)):
    """Upload contract files for processing"""
    try:
        # Get and validate API key
        api_key = get_api_key_from_request(request, x_api_key)
        
        # Set the API key for this request
        os.environ["GOOGLE_API_KEY"] = api_key
        
        uploaded_files = []
        existing_files = set()
        
        # Get list of existing files to avoid duplicates
        if os.path.exists(state.upload_directory):
            existing_files = {f for f in os.listdir(state.upload_directory) 
                            if f.lower().endswith(('.html', '.htm', '.txt'))}
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith(('.html', '.htm', '.txt')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file.filename}. Only HTML and TXT files are supported."
                )
            
            # Check for duplicate by original filename (not UUID)
            file_extension = Path(file.filename).suffix
            base_filename = Path(file.filename).stem
            
            # Check if this exact filename already exists
            filename_exists = any(existing_file.endswith(file.filename) for existing_file in existing_files)
            if filename_exists:
                await send_log_message(f"Skipping duplicate file: {file.filename}", "warning")
                continue
            
            # Create simple filename without UUID to avoid duplicates
            safe_filename = f"{base_filename}{file_extension}"
            file_path = os.path.join(state.upload_directory, safe_filename)
            
            # If file exists with exact name, skip it
            if os.path.exists(file_path):
                await send_log_message(f"File already exists, skipping: {file.filename}", "warning")
                continue
            
            # Save file
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            uploaded_files.append({
                "original_name": file.filename,
                "safe_filename": safe_filename,
                "file_path": file_path,
                "size": len(content)
            })
        
        if not uploaded_files:
            await send_log_message("No new files to upload (all were duplicates)", "warning")
            return {
                "message": "No new files uploaded (all were duplicates)",
                "files": []
            }
        
        await send_log_message(f"Successfully uploaded {len(uploaded_files)} new contract files")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
        
    except Exception as e:
        await send_log_message(f"Error uploading files: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def start_processing(request: Request, x_api_key: Optional[str] = Header(None)):
    """Start processing uploaded contracts"""
    try:
        # Get and validate API key
        api_key = get_api_key_from_request(request, x_api_key)
        
        # Set the API key for this request
        os.environ["GOOGLE_API_KEY"] = api_key
        
        if state.current_processing_job and state.current_processing_job.status == "processing":
            raise HTTPException(status_code=400, detail="Processing already in progress")
        
        # Check if there are uploaded files
        if not os.path.exists(state.upload_directory):
            raise HTTPException(status_code=400, detail="No upload directory found")
        
        # Get unique contract files from upload directory
        uploaded_files = []
        for filename in os.listdir(state.upload_directory):
            if filename.lower().endswith(('.html', '.htm', '.txt')):
                file_path = os.path.join(state.upload_directory, filename)
                if os.path.isfile(file_path):  # Ensure it's a file, not a directory
                    uploaded_files.append(filename)
        
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No contract files found in upload directory")
        
        # Remove duplicates if any (shouldn't happen with new upload logic, but just in case)
        unique_files = list(set(uploaded_files))
        
        await send_log_message(f"Found {len(unique_files)} contract files ready for processing")
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Initialize processing status with correct file count
        state.current_processing_job = ProcessingStatus(
            status="processing",
            progress=0,
            total_files=len(unique_files),
            processed_files=0,
            message="Starting contract processing...",
            job_id=job_id
        )
        
        # Start background processing
        asyncio.create_task(process_contracts_background(state.upload_directory))
        
        await send_status_update(state.current_processing_job)
        await send_log_message("Started contract processing pipeline")
        
        return {"message": "Processing started", "job_id": job_id, "file_count": len(unique_files)}
        
    except HTTPException:
        raise
    except Exception as e:
        await send_log_message(f"Error starting processing: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))

async def process_contracts_background(upload_dir: str):
    """Background task for processing contracts"""
    try:
        await send_log_message("Initializing GraphRAG pipeline...")
        
        # Clear current session contracts at start of new processing
        state.current_session_contracts = {}
        
        # Initialize processor
        state.processor = EnhancedBatchProcessor()
        
        # Initialize timing for API processing
        state.processor.start_time = time.time()
        
        # Create a custom progress callback
        async def progress_callback(current: int, total: int, file_path: str, message: str):
            state.current_processing_job.processed_files = current
            state.current_processing_job.total_files = total
            state.current_processing_job.progress = int((current / total) * 100) if total > 0 else 0
            state.current_processing_job.current_file = os.path.basename(file_path)
            state.current_processing_job.message = message
            
            await send_status_update(state.current_processing_job)
            await send_log_message(f"Processing {os.path.basename(file_path)}: {message}")
        
        # Process contracts with progress updates
        result = await process_with_progress(state.processor, upload_dir, progress_callback)
        
        # Store processed data
        state.processed_data = result
        
        # Track contracts processed in this session
        if state.processor and state.processor.processed_data_cache:
            for file_path, data in state.processor.processed_data_cache.items():
                # Only add if this file was processed in current session (check if it was in upload dir)
                if upload_dir in file_path:
                    state.current_session_contracts[file_path] = data
        
        # Mark as completed
        state.current_processing_job.status = "completed"
        state.current_processing_job.progress = 100
        state.current_processing_job.message = f"Successfully processed {len(state.current_session_contracts)} contracts in this session"
        
        await send_status_update(state.current_processing_job)
        await send_log_message(f"Contract processing completed successfully! Processed {len(state.current_session_contracts)} contracts in this session.")
        
        # Initialize agent for chat
        state.agent = DirectSecuritiesAgent()
        await send_log_message("Chat agent initialized - you can now ask questions about your contracts")
        
    except Exception as e:
        state.current_processing_job.status = "error"
        state.current_processing_job.message = f"Processing failed: {str(e)}"
        await send_status_update(state.current_processing_job)
        await send_log_message(f"Processing failed: {str(e)}", "error")

async def process_with_progress(processor, upload_dir, progress_callback):
    """Process contracts with progress updates"""
    try:
        # Find all contract files
        files = processor.find_all_contract_files(upload_dir)
        total_files = len(files)
        
        if total_files == 0:
            await progress_callback(0, 0, "", "No contract files found")
            return {"error": "No contract files found"}
        
        await progress_callback(0, total_files, "", f"Found {total_files} contracts to process")
        
        # Add a small delay to ensure the UI updates
        await asyncio.sleep(0.1)
        
        # Load cache
        processor.load_processed_cache()
        await progress_callback(0, total_files, "", "Loaded processing cache")
        await asyncio.sleep(0.1)
        
        # Process each file
        successful_count = 0
        for i, (file_path, file_type) in enumerate(files, 1):
            filename = os.path.basename(file_path)
            
            await progress_callback(i-1, total_files, file_path, f"Starting {filename}")
            await asyncio.sleep(0.1)  # Allow UI to update
            
            try:
                # Process the contract (this is synchronous - you might want to make it async)
                success = processor.process_single_contract(file_path, file_type, i, total_files)
                
                if success:
                    successful_count += 1
                    await progress_callback(i, total_files, file_path, f"✅ Processed {filename}")
                else:
                    await progress_callback(i, total_files, file_path, f"❌ Failed to process {filename}")
                
            except Exception as e:
                await progress_callback(i, total_files, file_path, f"❌ Error processing {filename}: {str(e)}")
            
            # Add delay between files to ensure smooth progress updates
            await asyncio.sleep(0.2)
        
        # Generate final report
        await progress_callback(total_files, total_files, "", "Generating final report...")
        await asyncio.sleep(0.1)
        
        result = {
            "successful_count": successful_count,
            "total_files": total_files,
            "failed_count": total_files - successful_count,
            "processed_data": processor.processed_data_cache
        }
        
        return result
        
    except Exception as e:
        await progress_callback(0, 0, "", f"Processing failed: {str(e)}")
        return {"error": str(e)}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: Request, message: ChatRequest, x_api_key: Optional[str] = Header(None)):
    """Chat with the contract analysis agent"""
    try:
        # Get and validate API key
        api_key = get_api_key_from_request(request, x_api_key)
        
        # Set the API key for this request
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Check if contracts have been processed (cache file exists)
        if not os.path.exists(CACHE_FILE):
            raise HTTPException(
                status_code=400, 
                detail="No processed contracts found. Please upload and process contracts first."
            )
        
        # Initialize securities agent if not already done
        if not state.securities_agent:
            await send_log_message("Initializing securities agent for chat...")
            state.securities_agent = DirectSecuritiesAgent()
        
        await send_log_message(f"Processing chat query: {message.message}")
        
        # Get response from the agent
        response = state.securities_agent.answer_question(message.message)
        
        await send_log_message("Chat response generated successfully")
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await send_log_message(f"Error in chat: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contracts/summary")
async def get_contracts_summary():
    """Get summary of processed contracts"""
    try:
        # Current session contracts (from this processing run)
        current_session_summaries = []
        if state.current_session_contracts:
            for file_path, data in state.current_session_contracts.items():
                current_session_summaries.append(ContractSummary(
                    title=data.get('title', 'Unknown'),
                    contract_type=data.get('contract_type', 'Unknown'),
                    summary=data.get('summary', ''),
                    execution_date=data.get('execution_date'),
                    parties_count=data.get('parties_count', 0),
                    securities_count=data.get('securities_count', 0),
                    file_path=file_path
                ))
        
        # All contracts (from cache - includes previous sessions)
        all_summaries = []
        if state.processor and state.processor.processed_data_cache:
            for file_path, data in state.processor.processed_data_cache.items():
                all_summaries.append(ContractSummary(
                    title=data.get('title', 'Unknown'),
                    contract_type=data.get('contract_type', 'Unknown'),
                    summary=data.get('summary', ''),
                    execution_date=data.get('execution_date'),
                    parties_count=data.get('parties_count', 0),
                    securities_count=data.get('securities_count', 0),
                    file_path=file_path
                ))
        
        return {
            "current_session": {
                "contracts": current_session_summaries,
                "total": len(current_session_summaries)
            },
            "all_contracts": {
                "contracts": all_summaries,
                "total": len(all_summaries)
            },
            # For backward compatibility, default to current session
            "contracts": current_session_summaries,
            "total": len(current_session_summaries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/processed-data")
async def download_processed_data():
    """Download processed contract data as JSON"""
    try:
        if not state.processor or not state.processor.processed_data_cache:
            raise HTTPException(status_code=404, detail="No processed data available")
        
        # Create temporary file with processed data
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        try:
            json.dump(state.processor.processed_data_cache, temp_file, indent=2, default=str, ensure_ascii=False)
            temp_file.flush()
        finally:
            temp_file.close()
        
        # Verify file was created and has content
        if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
            raise HTTPException(status_code=500, detail="Failed to create download file")
        
        return FileResponse(
            path=temp_file.name,
            filename=f"processed_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"Download error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=f"Failed to create download: {str(e)}")

@app.get("/download/backup")
async def download_database_backup():
    """Download Neo4j database backup"""
    try:
        backup_file = backup_neo4j_data()
        if not backup_file or not os.path.exists(backup_file):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        return FileResponse(
            path=backup_file,
            filename=os.path.basename(backup_file),
            media_type="application/json"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/reset")
async def reset_system(request: Request, x_api_key: Optional[str] = Header(None)):
    """Reset the system by clearing upload directory and cache"""
    try:
        # Get and validate API key
        api_key = get_api_key_from_request(request, x_api_key)
        
        # Set the API key for this request
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Reset processing state
        state.current_processing_job = None
        state.securities_agent = None
        state.current_session_contracts.clear()
        
        # Clear upload directory
        if os.path.exists(state.upload_directory):
            shutil.rmtree(state.upload_directory)
            os.makedirs(state.upload_directory, exist_ok=True)
        
        await send_log_message("System reset completed - upload directory cleared")
        
        return {"message": "System reset successfully"}
        
    except Exception as e:
        await send_log_message(f"Error resetting system: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    try:
        print(f"WebSocket connection attempt from: {websocket.client}")
        await manager.connect(websocket)
        print("WebSocket connection established successfully")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection", 
            "message": "Connected to GraphRAG API",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            print(f"Received WebSocket message: {data}")
            # Echo back for connection testing
            await websocket.send_json({"type": "ping", "message": "pong"})
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Removed uvicorn.run() call - use uvicorn command directly for better WebSocket support
# Run with: uvicorn api:app --host 0.0.0.0 --port 8000 --reload 