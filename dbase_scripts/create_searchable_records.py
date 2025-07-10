import psycopg2
import sqlite3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from db_config import POSTGRES_CONFIG

def create_searchable_records_table():
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create the searchable_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS searchable_records (
                id SERIAL PRIMARY KEY,
                text1_column TEXT,
                text2_column TEXT
            )
        """)
        
        print("Successfully created searchable_records table in PostgreSQL")
        
        # Connect to SQLite and get existing data
        sqlite_conn = sqlite3.connect("recordsstatus.db")
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get data from SQLite
        sqlite_cursor.execute("SELECT text1_column, text2_column FROM records_status")
        records = sqlite_cursor.fetchall()
        
        if records:
            # Insert data into PostgreSQL
            for record in records:
                cursor.execute(
                    "INSERT INTO searchable_records (text1_column, text2_column) VALUES (%s, %s)",
                    record
                )
            print(f"Successfully migrated {len(records)} records from SQLite to PostgreSQL")
        else:
            # Insert default values if no records exist
            default_values = ["LIVE BIRTH: 1985 to 1989", "LIVE BIRTH: 1982 to 1989"]
            cursor.execute(
                "INSERT INTO searchable_records (text1_column, text2_column) VALUES (%s, %s)",
                default_values
            )
            print("Inserted default values into searchable_records table")
        
    except psycopg2.Error as e:
        print(f"PostgreSQL Error: {e}")
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
        if 'sqlite_conn' in locals():
            sqlite_conn.close()

if __name__ == "__main__":
    create_searchable_records_table() 