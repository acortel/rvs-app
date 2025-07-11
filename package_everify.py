#!/usr/bin/env python3
"""
eVerify Packaging Script
Packages the eVerify standalone application with all dependencies and resources.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_package_structure():
    """Create the package structure for the eVerify standalone app."""
    
    # Define the package directory
    package_dir = "everify_standalone_package"
    
    # Create package directory
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Files to copy
    files_to_copy = [
        "everify_standalone.py",
        "everify/",
        "qr_scanner_window.py",
        "audit_logger.py",
        "db_config.py",
        "stylesheets.py",
        "requirements.txt"
    ]
    
    # Directories to copy
    dirs_to_copy = [
        "icons/",
        "images/",
        "forms_img/"
    ]
    
    print("📦 Creating package structure...")
    
    # Copy files
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.copytree(file_path, os.path.join(package_dir, file_path))
                print(f"✅ Copied directory: {file_path}")
            else:
                shutil.copy2(file_path, package_dir)
                print(f"✅ Copied file: {file_path}")
        else:
            print(f"⚠️ File not found: {file_path}")
    
    # Copy directories
    for dir_path in dirs_to_copy:
        if os.path.exists(dir_path):
            shutil.copytree(dir_path, os.path.join(package_dir, dir_path))
            print(f"✅ Copied directory: {dir_path}")
        else:
            print(f"⚠️ Directory not found: {dir_path}")
    
    return package_dir

def create_launcher_script(package_dir):
    """Create a launcher script for the eVerify app."""
    
    launcher_content = '''#!/usr/bin/env python3
"""
eVerify Standalone Launcher
Launches the eVerify standalone application.
"""

import os
import sys
import subprocess

def main():
    # Set up environment variables (if not already set)
    if not os.getenv('CLIENT_ID'):
        print("⚠️ CLIENT_ID not set. Please set your eVerify credentials.")
        print("Example: export CLIENT_ID='your_client_id'")
        return
    
    if not os.getenv('CLIENT_SECRET'):
        print("⚠️ CLIENT_SECRET not set. Please set your eVerify credentials.")
        print("Example: export CLIENT_SECRET='your_client_secret'")
        return
    
    # Launch the eVerify standalone app
    try:
        from everify_standalone import eVerifyStandaloneForm
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = eVerifyStandaloneForm()
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error launching eVerify: {e}")

if __name__ == "__main__":
    main()
'''
    
    launcher_path = os.path.join(package_dir, "launch_everify.py")
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    print(f"✅ Created launcher script: {launcher_path}")
    return launcher_path

def create_readme(package_dir):
    """Create a README for the package."""
    
    readme_content = '''# eVerify Standalone Application

A generic standalone eVerify application that can be launched from any Python desktop application.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
export PGHOST="localhost"
export PGPORT="5432"
export PGUSER="postgres"
export PGPASSWORD="your_password"
export PGDATABASE="your_database_name"
```

## Usage

### Method 1: Direct Launch
```bash
python launch_everify.py
```

### Method 2: From Another Python Application
```python
import subprocess
subprocess.run(["python", "launch_everify.py"])
```

### Method 3: From VBA (MS Access, Excel)
```vba
Shell "python path\to\launch_everify.py", vbNormalFocus
```

### Method 4: Get Verification Results
```python
from everify_standalone import eVerifyStandaloneForm
from PySide6.QtWidgets import QApplication

app = QApplication([])
window = eVerifyStandaloneForm()
window.show()
app.exec()

# Get results after verification
result = window.get_verification_result()
if result['full_name']:
    print(f"Verified: {result['full_name']}")
    print(f"Data: {result['verification_data']}")
```

## Features

- ✅ Person verification using personal information
- ✅ QR code scanning and verification
- ✅ Face liveness check (requires liveness server)
- ✅ Database integration (PostgreSQL)
- ✅ Standalone operation (no Flask server required)
- ✅ Cross-platform compatibility
- ✅ Generic design (not tied to specific applications)

## Requirements

- Python 3.7+
- PySide6
- PostgreSQL database
- eVerify API credentials

## Troubleshooting

1. **Configuration Error**: Check your environment variables
2. **Database Error**: Ensure PostgreSQL is running and accessible
3. **Liveness Error**: Start the Flask liveness server if needed

## Integration

This package can be integrated into any desktop application by:
1. Adding a button/menu item
2. Launching the eVerify app when clicked
3. Reading results from the database or using get_verification_result()
'''
    
    readme_path = os.path.join(package_dir, "README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Created README: {readme_path}")

def create_requirements(package_dir):
    """Create a comprehensive requirements.txt for the package."""
    
    requirements_content = '''# eVerify Standalone Requirements

# Core dependencies
PySide6>=6.0.0
requests>=2.25.0
PyJWT>=2.0.0
psycopg2-binary>=2.9.0

# Optional: For QR code scanning
opencv-python>=4.5.0
pyzbar>=0.1.8

# Optional: For web engine (if using QtWebEngine)
PySide6-WebEngine>=6.0.0
'''
    
    req_path = os.path.join(package_dir, "requirements.txt")
    with open(req_path, 'w') as f:
        f.write(requirements_content)
    
    print(f"✅ Created requirements.txt: {req_path}")

def create_batch_launcher(package_dir):
    """Create a Windows batch file launcher."""
    
    batch_content = '''@echo off
echo Starting eVerify Standalone Application...
python launch_everify.py
pause
'''
    
    batch_path = os.path.join(package_dir, "launch_everify.bat")
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    
    print(f"✅ Created batch launcher: {batch_path}")

def main():
    """Main packaging function."""
    
    print("🚀 eVerify Standalone Packaging Tool")
    print("=" * 40)
    
    # Create package structure
    package_dir = create_package_structure()
    
    # Create launcher script
    create_launcher_script(package_dir)
    
    # Create README
    create_readme(package_dir)
    
    # Create requirements
    create_requirements(package_dir)
    
    # Create batch launcher (Windows)
    create_batch_launcher(package_dir)
    
    print("\n" + "=" * 40)
    print("✅ Package created successfully!")
    print(f"📁 Package location: {package_dir}")
    print("\n📋 Next steps:")
    print("1. Set your environment variables (CLIENT_ID, CLIENT_SECRET, etc.)")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Test the package: python launch_everify.py")
    print("4. Integrate into your desktop applications!")
    
    return package_dir

if __name__ == "__main__":
    main() 