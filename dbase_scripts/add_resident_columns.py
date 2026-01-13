import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from db_config import POSTGRES_CONFIG

def add_resident_columns():
    """Add resident columns to birth_index and death_index tables."""

    conn = None
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()

        # Define the columns to add
        columns = ['maasin_resident', 'soleyte_resident', 'leyte_resident']
        tables = ['birth_index', 'death_index']

        # Add columns to each table
        for table in tables:
            print(f"\nAdding columns to {table}...")
            for column in columns:
                try:
                    cur.execute(f"""
                        ALTER TABLE {table}
                        ADD COLUMN IF NOT EXISTS {column} BOOLEAN DEFAULT FALSE;
                    """)
                    print(f"✅ Added {column} to {table}")
                except psycopg2.Error as e:
                    print(f"❌ Error adding {column} to {table}: {str(e)}")
                    continue

        # Commit the changes
        conn.commit()
        print("\n✅ All resident columns added successfully!")

    except psycopg2.Error as e:
        print(f"❌ Database error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    add_resident_columns()