#!/usr/bin/env python3
"""
Simple runner script to demonstrate the complete pipeline.
"""

from main import main

if __name__ == "__main__":
    print("🚀 Starting Bank Statement Processing Pipeline...")
    print("=" * 60)
    
    try:
        summary = main()
        print("\n" + "=" * 60)
        print("✅ Pipeline completed successfully!")
        print(f"📊 Processed: {summary['successful']}/{summary['total_files']} files")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Pipeline failed: {e}")
        exit(1)