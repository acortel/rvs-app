import psycopg2
from db_config import POSTGRES_CONFIG

def add_released_by_column():
    """Add released_by column to the releasing_log table."""
    
    # SQL commands to modify the table
    sql_commands = [
        # Add the new column
        """
        ALTER TABLE releasing_log
        ADD COLUMN released_by TEXT;
        """,
        
        # Set default value for existing records
        """
        UPDATE releasing_log
        SET released_by = 'system_migration'
        WHERE released_by IS NULL;
        """,
        
        # Make the column NOT NULL
        """
        ALTER TABLE releasing_log
        ALTER COLUMN released_by SET NOT NULL;
        """
    ]
    
    conn = None
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        # Execute each SQL command
        for sql in sql_commands:
            try:
                print(f"\nExecuting: {sql.strip()}")
                cur.execute(sql)
                print("✅ Command executed successfully")
                
            except psycopg2.Error as e:
                # If the column already exists, continue with the next command
                if "column already exists" in str(e).lower():
                    print("Column already exists, continuing with next step...")
                    continue
                else:
                    raise e
        
        # Commit the changes
        conn.commit()
        print("\n✅ Successfully added released_by column to releasing_log table!")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"\n❌ Error modifying table: {error}")
    finally:
        if conn is not None:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("Starting migration to add released_by column...")
    add_released_by_column() 