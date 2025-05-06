"""
Migration script to add the similarity_details column to the documents table in PostgreSQL.
Run this script to update the database schema.
"""
import os
import sys
import psycopg2
from psycopg2 import sql


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.app import app

def migrate_postgres_database():
    """Add similarity_details column to documents table if it doesn't exist."""
    with app.app_context():


        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Database URI: {db_uri}")

        if not db_uri.startswith('postgresql://'):
            print("This script is for PostgreSQL databases only.")
            return


        db_uri = db_uri.replace('postgresql://', '')
        auth, rest = db_uri.split('@')

        if ':' in auth:
            username, password = auth.split(':')
        else:
            username = auth
            password = ''

        if '/' in rest:
            host_port, dbname = rest.split('/')
        else:
            host_port = rest
            dbname = ''

        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = '5432'

        print(f"Connecting to PostgreSQL database: {dbname} on {host}:{port} as {username}")


        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=username,
                password=password,
                host=host,
                port=port
            )
            conn.autocommit = True
            cursor = conn.cursor()

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'similarity_details'
            """)
            column_exists = cursor.fetchone() is not None

            if not column_exists:
                print("Adding similarity_details column to documents table...")
                cursor.execute(
                    sql.SQL("ALTER TABLE documents ADD COLUMN similarity_details TEXT")
                )
                print("Column added successfully.")
            else:
                print("similarity_details column already exists.")

            conn.close()
            print("Database migration completed successfully.")

        except Exception as e:
            print(f"Error during database migration: {e}")
            return

if __name__ == "__main__":
    migrate_postgres_database()
