import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

# Database configuration - should be set via environment variables
DATABASE_HOST = os.getenv('DATABASE_HOST', '10.0.28.161')
DATABASE_PORT = os.getenv('DATABASE_PORT', '80')
DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'f980f7da-efd3-477d-b84a-c171929c50ea')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'cs1_0_1')

# Connection pool
connection_pool = None

def init_pool():
    """Initialize connection pool"""
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            dbname=DATABASE_NAME,
            gssencmode="disable"
        )
    return connection_pool

def get_conn():
    """Get a connection from the pool"""
    init_pool()
    return connection_pool.getconn()

def release_conn(conn):
    """Return a connection to the pool"""
    if connection_pool:
        connection_pool.putconn(conn)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = get_conn()
    try:
        yield conn
    finally:
        release_conn(conn)

def execute_query(query, params=None, fetch=True):
    """Execute a query and optionally fetch results"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if fetch:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = cursor.fetchall()
                return columns, results
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()

def execute_many(query, params_list):
    """Execute many queries with different parameters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()

# Test connection
def test_connection():
    """Test database connection"""
    try:
        conn = get_conn()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
