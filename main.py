#!/usr/bin/env python3
"""
Main script to process bank statements from Google Drive:
1. Connect to Google Drive
2. List files in specified folder
3. Download PDF files
4. Extract text content
5. Save extracted text
"""

import os
import logging
from pathlib import Path
from typing import List

from infrastructure.gdrive.google_drive_gateway import GoogleDriveGateway
from infrastructure.gdrive.drive_gateway import DriveFile
from services.factory import Settings, make_pdf_extractor
from infrastructure.llm import LLMFactory
from config import app_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, app_settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatementProcessor:
    """Main processor for bank statement files."""
    
    def __init__(self):
        self.output_dir = Path(app_settings.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "pdfs").mkdir(exist_ok=True)
        (self.output_dir / "texts").mkdir(exist_ok=True)
        
        # LLM output directory
        self.llm_output_dir = Path(app_settings.llm_output_dir)
        self.llm_output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.drive_gateway = self._init_drive_gateway()
        self.pdf_extractor = self._init_pdf_extractor()
        self.llm_provider = self._init_llm_provider()
    
    def _init_drive_gateway(self) -> GoogleDriveGateway:
        """Initialize Google Drive gateway."""
        creds_path = app_settings.gdrive_credentials
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"{creds_path} not found. Please download OAuth credentials "
                "from Google Cloud Console and place them in the project root."
            )
        
        logger.info("🔐 Initializing Google Drive connection...")
        
        if app_settings.gdrive_auth_mode == "oauth":
            return GoogleDriveGateway.from_oauth(
                app_settings.gdrive_credentials, 
                app_settings.gdrive_token
            )
        else:
            if not app_settings.gdrive_sa_key:
                raise ValueError("Service account key path is required when using service account authentication")
            return GoogleDriveGateway.from_service_account(app_settings.gdrive_sa_key)
    
    def _init_pdf_extractor(self):
        """Initialize PDF extractor."""
        settings = Settings(pdf_engine=app_settings.pdf_engine)
        return make_pdf_extractor(settings)
    
    def _init_llm_provider(self):
        """Initialize LLM provider."""
        logger.info(f"🤖 Initializing LLM provider: {app_settings.llm_provider}")
        
        # Initialize Langfuse if credentials are provided
        if app_settings.langfuse_secret_key and app_settings.langfuse_public_key:
            logger.info("🔍 Initializing Langfuse for LLM observability")
            LLMFactory.initialize_langfuse(
                secret_key=app_settings.langfuse_secret_key,
                public_key=app_settings.langfuse_public_key,
                host=app_settings.langfuse_host
            )
        
        return LLMFactory.create_provider(
            base_url = app_settings.llm_base_url,
            provider_type=app_settings.llm_provider,
            api_key=app_settings.llm_api_key,
            model=app_settings.llm_model,
            temperature=app_settings.llm_temperature
        )
    
    def find_target_folder(self) -> DriveFile:
        """Find the target folder in Google Drive."""
        folder_name = app_settings.target_folder_name
        logger.info(f"📁 Searching for '{folder_name}' folder...")
        
        folder_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        folders = self.drive_gateway.list_files(folder_query)
        
        if not folders:
            raise ValueError(f"Folder '{folder_name}' not found in Google Drive")
        
        folder = folders[0]
        logger.info(f"✅ Found folder: {folder.name} (ID: {folder.id})")
        return folder
    
    def list_pdf_files(self, folder: DriveFile) -> List[DriveFile]:
        """List all PDF files in the target folder."""
        logger.info(f"📋 Listing PDF files in '{folder.name}'...")
        
        # Query for PDF files in the folder
        files_query = f"'{folder.id}' in parents and trashed = false and mimeType = 'application/pdf'"
        files = self.drive_gateway.list_files(files_query)
        
        if app_settings.max_files:
            files = files[:app_settings.max_files]
        
        logger.info(f"📋 Found {len(files)} PDF files to process")
        for i, file in enumerate(files, 1):
            logger.info(f"  {i}. {file.name} (Size: {file.size} bytes)")
        
        return files
    
    def download_file(self, file: DriveFile) -> Path:
        """Download a file and save it locally."""
        pdf_path = self.output_dir / "pdfs" / file.name
        
        if pdf_path.exists():
            logger.info(f"⏭️  Skipping download: {file.name} (already exists)")
            return pdf_path
        
        logger.info(f"⬇️  Downloading: {file.name}")
        
        try:
            # Use download_to_file method for direct file saving
            self.drive_gateway.download_to_file(file.id, pdf_path)
            logger.info(f"✅ Downloaded: {file.name} ({pdf_path.stat().st_size} bytes)")
            return pdf_path
        except Exception as e:
            logger.error(f"❌ Failed to download {file.name}: {e}")
            raise
    
    def extract_text(self, pdf_path: Path, file_name: str) -> str:
        """Extract text from a PDF file."""
        # Create text filename (replace .pdf with .txt)
        text_filename = file_name.replace('.pdf', '.txt')
        text_path = self.output_dir / "texts" / text_filename
        
        # Check if text file already exists
        if text_path.exists():
            logger.info(f"⏭️  Skipping extraction: {file_name} (text already exists)")
            text = text_path.read_text(encoding='utf-8')
            logger.info(f"✅ Loaded existing text: {len(text)} characters from {text_filename}")
            return text
        
        logger.info(f"📄 Extracting text from: {file_name}")
        
        # Check if text file already exists
        if text_path.exists():
            logger.info(f"⏭️  Skipping extraction: {file_name} (text already exists)")
            text = text_path.read_text(encoding='utf-8')
            logger.info(f"✅ Loaded existing text: {len(text)} characters from {text_filename}")
            return text
        
        try:
            pdf_bytes = pdf_path.read_bytes()
            text = self.pdf_extractor.extract(pdf_bytes, password=app_settings.pdf_password)
            
            logger.info(f"✅ Extracted {len(text)} characters from {file_name}")
            return text
        except Exception as e:
            logger.error(f"❌ Failed to extract text from {file_name}: {e}")
            raise
    
    def save_text(self, text: str, file_name: str) -> Path:
        """Save extracted text to a file."""
        # Create text filename (replace .pdf with .txt)
        text_filename = file_name.replace('.pdf', '.txt')
        text_path = self.output_dir / "texts" / text_filename
        
        text_path.write_text(text, encoding='utf-8')
        logger.info(f"💾 Saved text: {text_path}")
        return text_path
    
    def process_with_llm(self, text: str, file_name: str) -> Path:
        """Process text with LLM to extract structured transaction data."""
        # Create JSON filename (replace .pdf with .json)
        json_filename = file_name.replace('.pdf', '.json')
        json_path = self.llm_output_dir / json_filename
        
        logger.info(f"🤖 Processing with LLM: {file_name}")
        
        try:
            # Process text with LLM using prompt ID from config
            self.llm_provider.process_text_file(
                text_content=text,
                system_prompt_or_id=app_settings.llm_prompt_id,
                output_path=json_path,
                use_prompt_library=True
            )
            logger.info(f"✅ LLM processing complete: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"❌ LLM processing failed for {file_name}: {e}")
            raise
    
    def process_file(self, file: DriveFile) -> dict:
        """Process a single file: download -> extract -> save -> LLM."""
        logger.info(f"\n🔄 Processing: {file.name}")
        
        result = {
            "file_name": file.name,
            "file_id": file.id,
            "success": False,
            "error": None,
            "pdf_path": None,
            "text_path": None,
            "json_path": None,
            "text_length": 0
        }
        
        try:
            # Download PDF
            pdf_path = self.download_file(file)
            result["pdf_path"] = str(pdf_path)
            
            # Extract text
            text = self.extract_text(pdf_path, file.name)
            result["text_length"] = len(text)
            
            # Save text
            text_path = self.save_text(text, file.name)
            result["text_path"] = str(text_path)
            
            # Process with LLM
            json_path = self.process_with_llm(text, file.name)
            result["json_path"] = str(json_path)
            
            result["success"] = True
            logger.info(f"✅ Successfully processed: {file.name}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Failed to process {file.name}: {e}")
        
        return result
    
    def process_all(self) -> dict:
        """Process all files in the target folder."""
        logger.info("🚀 Starting bank statement processing pipeline...")
        
        summary = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        try:
            # Find target folder
            folder = self.find_target_folder()
            
            # List PDF files
            files = self.list_pdf_files(folder)
            summary["total_files"] = len(files)
            
            if not files:
                logger.warning("⚠️  No PDF files found to process")
                return summary
            
            # Process each file
            for i, file in enumerate(files, 1):
                logger.info(f"\n📊 Progress: {i}/{len(files)}")
                
                result = self.process_file(file)
                summary["results"].append(result)
                
                if result["success"]:
                    summary["successful"] += 1
                else:
                    summary["failed"] += 1
            
            # Print final summary
            self.print_summary(summary)
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
        
        return summary
    
    def print_summary(self, summary: dict):
        """Print processing summary."""
        logger.info(f"\n📊 Processing Summary:")
        logger.info(f"  Total files: {summary['total_files']}")
        logger.info(f"  Successful: {summary['successful']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Output directory: {self.output_dir.absolute()}")
        
        if summary["failed"] > 0:
            logger.info(f"\n❌ Failed files:")
            for result in summary["results"]:
                if not result["success"]:
                    logger.info(f"  - {result['file_name']}: {result['error']}")

def main():
    """Main entry point."""
    processor = StatementProcessor()
    
    try:
        summary = processor.process_all()
        
        if summary["successful"] > 0:
            logger.info(f"\n🎉 Successfully processed {summary['successful']} files!")
        
        # Flush Langfuse to ensure all traces are sent
        from infrastructure.llm.langfuse_wrapper import LangfuseWrapper
        LangfuseWrapper.flush()
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        raise
    finally:
        # Always flush Langfuse on exit
        from infrastructure.llm.langfuse_wrapper import LangfuseWrapper
        LangfuseWrapper.flush()

if __name__ == "__main__":
    main()