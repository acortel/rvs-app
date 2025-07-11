"""
Example usage of the eVerify package in a desktop application.
"""

import os
from everify import EVerifyClient, EVerifyDB, validate_config

def main():
    """Example of how to use the eVerify package."""
    
    # 1. Validate configuration
    try:
        config = validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # 2. Initialize the client
    client = EVerifyClient(
        client_id=config['CLIENT_ID'],
        client_secret=config['CLIENT_SECRET']
    )
    
    # 3. Test database connection
    db = EVerifyDB()
    if db.test_connection():
        print("✅ Database connection successful")
    else:
        print("⚠️ Database connection failed - some features may not work")
    
    # 4. Example: Verify a person
    print("\n--- Example: Person Verification ---")
    result = client.verify_person({
        "first_name": "JANE",
        "last_name": "DOE", 
        "birth_date": "1990-01-01"
    })
    
    if "error" in result:
        print(f"❌ Verification failed: {result['error']}")
    else:
        print("✅ Verification successful")
        print(f"Result: {result}")
    
    # 5. Example: Check if liveness server is available
    print("\n--- Example: Liveness Check ---")
    if client.is_liveness_server_available():
        print("✅ Liveness server is available")
        # client.start_liveness_check()  # Uncomment to open browser
    else:
        print("⚠️ Liveness server is not available")
    
    print("\n--- eVerify package is ready for integration! ---")

if __name__ == "__main__":
    main() 