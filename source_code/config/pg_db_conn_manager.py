import os
from contextlib import contextmanager
from typing import List, Dict, Any, Union
import atexit

import psycopg2
from psycopg2 import pool

# ❗ IMPORTANT: Replace these with your actual database credentials
DB_HOST = os.getenv('POSTGRES_DB_HOST', 'localhost')
DB_NAME = os.getenv('POSTGRES_DB_NAME', 'investment_db')
DB_USER = os.getenv('POSTGRES_DB_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_DB_PASS')
DB_PORT = os.getenv('POSTGRES_DB_PORT', '5432')

# Connection pool configuration
MIN_CONN = int(os.getenv('POSTGRES_DB_MIN_CONN', '2'))
MAX_CONN = int(os.getenv('POSTGRES_DB_MAX_CONN', '10'))

# Global connection pool
_connection_pool = None

def init_connection_pool():
    """Initialize the database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                MIN_CONN,
                MAX_CONN,
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            print(f"Connection pool created with {MIN_CONN}-{MAX_CONN} connections")
        except psycopg2.OperationalError as e:
            print(f"Failed to create connection pool: {e}")
            raise

def close_connection_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        print("Connection pool closed")

# Register cleanup function to close pool on exit
atexit.register(close_connection_pool)

@contextmanager
def get_db_connection():
    """
    Provides a database connection from the connection pool within a context manager.
    The connection is returned to the pool upon exiting the 'with' block.
    """
    global _connection_pool
    if _connection_pool is None:
        init_connection_pool()
    
    conn = None
    try:
        conn = _connection_pool.getconn()
        if conn:
            # Reset connection state if needed
            conn.rollback()
            yield conn
        else:
            raise psycopg2.OperationalError("Could not get connection from pool")
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            _connection_pool.putconn(conn)


def dict_fetch_all(cursor) -> List[Dict[str, Any]]:
    """Returns all rows from a cursor as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_data(query: str, params: tuple = None, as_dicts: bool = True) -> Union[List[Dict[str, Any]], List[List[Any]]]:
    """
    Fetches data from the database.

    Args:
        query: The SQL query string.
        params: Optional parameters for the query.
        as_dicts: If True, returns a list of dictionaries. If False,
                  returns a list of lists. Defaults to True.

    Returns:
        A list of dictionaries or a list of lists.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if as_dicts:
                    return dict_fetch_all(cur)
                else:
                    # Fetch and return the raw data (list of tuples), then convert to list of lists
                    return [list(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def execute_query(query: str, params: tuple = None) -> int:
    """
    Executes a DML query (INSERT, UPDATE, DELETE) and commits the transaction.
    Returns the number of rows affected.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                return cur.rowcount
    except Exception as e:
        print(f"Error executing query: {e}")
        return 0


# Example Usage
if __name__ == "__main__":
    # Example 1: Fetching data as a list of dictionaries (default behavior)
    print("Fetching users as dictionaries:")
    search_param = '%%test%%'  # Use double percent signs for the LIKE wildcard
    # In the query, use a single placeholder, and the wildcard is part of the param
    users_dict = fetch_data("SELECT * FROM public.user WHERE email ilike %s;", (search_param,), as_dicts=False)
    print(users_dict)

    print("-" * 50)

    # Example 2: Fetching data as a list of lists
    print("Fetching users as lists:")
    users_list = fetch_data("SELECT * FROM public.user WHERE email ilike %s;", (search_param,), as_dicts=False)
    print(users_list)

    # Example 2: Fetching data as a list of lists
    print("Fetching users as lists:")
    users_list = fetch_data("SELECT * FROM public.user WHERE user_id = %s", (1,), as_dicts=False)
    print(users_list)
