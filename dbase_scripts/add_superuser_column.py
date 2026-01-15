"""
Database migration script to add superuser role support
Adds is_superuser column to users_list table
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Add parent directory to path to import db_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import POSTGRES_CONFIG


def add_superuser_column():
    """Add is_superuser column to users_list table if it doesn't exist"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Checking if is_superuser column already exists...")
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users_list' AND column_name = 'is_superuser'
        """)
        
        if cursor.fetchone():
            print("✓ is_superuser column already exists. No changes needed.")
            cursor.close()
            conn.close()
            return True
        
        print("Adding is_superuser column to users_list table...")
        
        # Add the column with default value FALSE
        cursor.execute("""
            ALTER TABLE users_list 
            ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE
        """)
        
        print("✓ Successfully added is_superuser column")
        
        # Set all existing users to non-superuser (FALSE) - this is actually the default
        print("Setting all existing users as non-superusers...")
        cursor.execute("""
            UPDATE users_list 
            SET is_superuser = FALSE 
            WHERE is_superuser IS NULL
        """)
        
        affected_rows = cursor.rowcount
        if affected_rows > 0:
            print(f"✓ Updated {affected_rows} users to non-superuser status")
        else:
            print("✓ All users already set to non-superuser status")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        print("\nNOTE: All existing users are now set as non-superusers.")
        print("To promote a user to superuser, use the following command:")
        print("\n  UPDATE users_list SET is_superuser = TRUE WHERE username = '<username>';")
        print("\nOr use the manage users interface after the application is updated.")
        
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def promote_user_to_superuser(username):
    """Promote a specific user to superuser status"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"Promoting user '{username}' to superuser...")
        
        # Check if user exists
        cursor.execute("SELECT username FROM users_list WHERE username = %s", (username,))
        if not cursor.fetchone():
            print(f"✗ User '{username}' not found")
            cursor.close()
            conn.close()
            return False
        
        # Update user to superuser
        cursor.execute(
            "UPDATE users_list SET is_superuser = TRUE WHERE username = %s",
            (username,)
        )
        
        print(f"✓ User '{username}' is now a superuser")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("RVS Database Migration: Add Superuser Role Support")
    print("="*60)
    
    # Run the migration
    success = add_superuser_column()
    
    if success and len(sys.argv) > 1:
        # If a username argument is provided, promote that user
        username = sys.argv[1]
        promote_user_to_superuser(username)
    
    sys.exit(0 if success else 1)
