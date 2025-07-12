#!/usr/bin/env python3
"""
Test script to list and download all files from Google Drive folder:
mydrive/SaoKe/Hanh/Debit_VP_Bank
"""

import os
from pathlib import Path
from infrastructure.gdrive.google_drive_gateway import GoogleDriveGateway

def test_list_and_download_files():
    """Test listing and downloading all files from the specified folder."""
    
    # Check if credentials file exists
    if not os.path.exists("credentials.json"):
        print("❌ Error: credentials.json not found in project root")
        print("Please download your OAuth credentials from Google Cloud Console")
        print("and place them as 'credentials.json' in the project root")
        return
    
    try:
        # Initialize Google Drive Gateway
        print("🔐 Initializing Google Drive Gateway...")
        gw = GoogleDriveGateway.from_oauth("credentials.json", "token.json")
        print("✅ Successfully authenticated with Google Drive")
        
        # First, find the Debit_VP_Bank folder
        print("\n📁 Searching for Debit_VP_Bank folder...")
        folder_query = "name = 'Debit_VP_Bank' and mimeType = 'application/vnd.google-apps.folder'"
        folders = gw.list_files(folder_query)
        
        if not folders:
            print("❌ Debit_VP_Bank folder not found")
            return
        
        folder = folders[0]  # Get the first (and should be only) folder
        print(f"✅ Found folder: {folder.name} (ID: {folder.id})")
        
        # Now list all files inside this folder
        print(f"\n📋 Listing all files inside '{folder.name}' folder...")
        files_query = f"'{folder.id}' in parents and trashed = false"
        files = gw.list_files(files_query)
        
        print(f"\n📋 Found {len(files)} files in the folder:")
        for i, file in enumerate(files, 1):
            print(f"  {i}. {file.name} (ID: {file.id}, Size: {file.size} bytes, Type: {file.mime_type})")
        
        if not files:
            print("\n❌ No files found in the folder. Please check:")
            print("  1. The folder contains files")
            print("  2. You have access to the files")
            return
        
        # Create downloads directory
        download_dir = Path("downloads")
        download_dir.mkdir(exist_ok=True)
        
        # Download all files
        print(f"\n⬇️  Downloading {len(files)} files to 'downloads/' directory...")
        
        for i, file in enumerate(files, 1):
            try:
                print(f"  {i}/{len(files)} Downloading: {file.name}")
                
                # Skip folders - we only want to download actual files
                if file.mime_type == "application/vnd.google-apps.folder":
                    print(f"    ⏭️  Skipping folder: {file.name}")
                    continue
                
                # Download the file
                file_data = gw.download(file.id)
                
                # Save to file
                file_path = download_dir / file.name
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                print(f"    ✅ Downloaded: {file.name} ({len(file_data)} bytes)")
                
            except Exception as e:
                print(f"    ❌ Failed to download {file.name}: {e}")
        
        print(f"\n🎉 Download complete! Files saved to: {download_dir.absolute()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("  1. Make sure credentials.json is in the project root")
        print("  2. Run 'python test_oauth.py' first to authenticate")
        print("  3. Check that you have access to the Google Drive folder")

if __name__ == "__main__":
    test_list_and_download_files() 