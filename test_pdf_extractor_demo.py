#!/usr/bin/env python3
"""
Demo script to test PDF extractor with sample files from downloads folder.
"""

from pathlib import Path
from services.factory import Settings, make_pdf_extractor

def test_pdf_extraction():
    """Test PDF extraction with real files."""
    downloads_dir = Path("downloads")
    
    if not downloads_dir.exists():
        print("❌ Downloads folder not found")
        return
    
    pdf_files = list(downloads_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in downloads folder")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    
    # Test with PyMuPDF (default)
    settings = Settings(pdf_engine="pymupdf")
    extractor = make_pdf_extractor(settings)
    
    for pdf_file in pdf_files[:2]:  # Test first 2 files
        print(f"\n📄 Processing: {pdf_file.name}")
        
        try:
            pdf_bytes = pdf_file.read_bytes()
            text = extractor.extract(pdf_bytes)
            
            print(f"✅ Extracted {len(text)} characters")
            print(f"📝 First 200 chars: {text[:200]!r}")
            
            # Look for Vietnamese banking terms
            keywords = ["VPBank", "VP Bank", "Số dư", "số dư", "Giao dịch", "giao dịch", "Tài khoản", "tài khoản"]
            found_keywords = [kw for kw in keywords if kw in text]
            if found_keywords:
                print(f"🔍 Found banking keywords: {found_keywords}")
            
        except Exception as e:
            print(f"❌ Failed to process {pdf_file.name}: {e}")

if __name__ == "__main__":
    test_pdf_extraction()