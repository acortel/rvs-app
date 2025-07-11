import psycopg2
import logging
from .config import get_config

logger = logging.getLogger(__name__)

class EVerifyDB:
    def __init__(self, config=None):
        if config is None:
            config = get_config()['POSTGRES_CONFIG']
        self.config = config

    def get_connection(self):
        return psycopg2.connect(**self.config)

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def store_verification(self, person_data: dict):
        # person_data should contain all required fields
        values = (
            person_data.get('reference'),
            person_data.get('code'),
            person_data.get('first_name'),
            person_data.get('middle_name'),
            person_data.get('last_name'),
            person_data.get('birth_date'),
            person_data.get('face_key'),
            person_data.get('gender'),
            person_data.get('marital_status'),
            person_data.get('municipality'),
            person_data.get('province')
        )
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO verifications (
                    reference, code, first_name, middle_name, last_name, birth_date,
                    face_key, gender, marital_status, municipality, province
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', values)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_verification(self, reference=None, first_name=None, middle_name=None, last_name=None, suffix=None, birth_date=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if reference:
                cursor.execute('''
                    SELECT * FROM verifications WHERE reference = %s
                ''', (reference,))
            else:
                cursor.execute('''
                    SELECT * FROM verifications WHERE 
                        UPPER(COALESCE(first_name, '')) = %s AND
                        ( (middle_name IS NULL AND %s IS NULL) OR UPPER(COALESCE(middle_name, '')) = COALESCE(%s, '') ) AND
                        UPPER(COALESCE(last_name, '')) = %s AND
                        ( (suffix IS NULL AND %s IS NULL) OR UPPER(COALESCE(suffix, '')) = COALESCE(%s, '') ) AND
                        COALESCE(birth_date, '') = %s
                ''', (
                    first_name.upper() if first_name else '',
                    middle_name, middle_name.upper() if middle_name else '',
                    last_name.upper() if last_name else '',
                    suffix, suffix.upper() if suffix else '',
                    birth_date
                ))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            cursor.close()
            conn.close()