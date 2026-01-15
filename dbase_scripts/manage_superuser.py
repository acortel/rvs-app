"""
Utility script to manage superuser roles
Usage:
  python manage_superuser.py list                    - List all users with their superuser status
  python manage_superuser.py promote <username>    - Promote user to superuser
  python manage_superuser.py demote <username>     - Demote user from superuser
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from tabulate import tabulate

# Add parent directory to path to import db_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import POSTGRES_CONFIG


def list_users():
    """List all users with their superuser status"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        print("\nUsers in System:")
        print("="*70)
        
        cursor.execute("""
            SELECT username, firstname, lastname, is_superuser 
            FROM users_list 
            ORDER BY firstname, lastname
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the system.")
            cursor.close()
            conn.close()
            return True
        
        # Prepare data for table display
        table_data = []
        for username, firstname, lastname, is_superuser in users:
            status = "✓ SUPERUSER" if is_superuser else "  User"
            table_data.append([username, firstname, lastname, status])
        
        headers = ["Username", "First Name", "Last Name", "Role"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def promote_user(username):
    """Promote a user to superuser"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT firstname, lastname, is_superuser FROM users_list WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if not result:
            print(f"✗ User '{username}' not found")
            cursor.close()
            conn.close()
            return False
        
        firstname, lastname, is_superuser = result
        
        if is_superuser:
            print(f"✓ User '{username}' ({firstname} {lastname}) is already a superuser")
            cursor.close()
            conn.close()
            return True
        
        # Update user to superuser
        cursor.execute(
            "UPDATE users_list SET is_superuser = TRUE WHERE username = %s",
            (username,)
        )
        
        print(f"✓ Successfully promoted '{username}' ({firstname} {lastname}) to superuser")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def demote_user(username):
    """Demote a superuser to regular user"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT firstname, lastname, is_superuser FROM users_list WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if not result:
            print(f"✗ User '{username}' not found")
            cursor.close()
            conn.close()
            return False
        
        firstname, lastname, is_superuser = result
        
        if not is_superuser:
            print(f"✓ User '{username}' ({firstname} {lastname}) is already a regular user")
            cursor.close()
            conn.close()
            return True
        
        # Update user to regular user
        cursor.execute(
            "UPDATE users_list SET is_superuser = FALSE WHERE username = %s",
            (username,)
        )
        
        print(f"✓ Successfully demoted '{username}' ({firstname} {lastname}) to regular user")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def print_usage():
    """Print usage information"""
    print("\nUsage: python manage_superuser.py <command> [arguments]")
    print("\nCommands:")
    print("  list                   - List all users with their roles")
    print("  promote <username>    - Promote a user to superuser")
    print("  demote <username>     - Demote a superuser to regular user")
    print("\nExamples:")
    print("  python manage_superuser.py list")
    print("  python manage_superuser.py promote john_doe")
    print("  python manage_superuser.py demote jane_smith")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        success = list_users()
    elif command == "promote":
        if len(sys.argv) < 3:
            print("Error: username argument required")
            print_usage()
            sys.exit(1)
        success = promote_user(sys.argv[2])
    elif command == "demote":
        if len(sys.argv) < 3:
            print("Error: username argument required")
            print_usage()
            sys.exit(1)
        success = demote_user(sys.argv[2])
    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)
    
    sys.exit(0 if success else 1)
