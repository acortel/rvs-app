import psycopg2
from db_config import POSTGRES_CONFIG

def add_suffix_column():
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Add the suffix column
        cursor.execute("""
            ALTER TABLE verifications 
            ADD COLUMN IF NOT EXISTS suffix TEXT;
        """)
        
        print("Successfully added suffix column to verifications table")
        
    except psycopg2.Error as e:
        print(f"Error adding suffix column: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    add_suffix_column() 