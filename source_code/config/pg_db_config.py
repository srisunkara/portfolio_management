import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


def get_instance():
    return DatabaseConfig()


class DatabaseConfig:
    def __init__(self):
        self.db_host = os.getenv('POSTGRES_DB_HOST', 'localhost')
        self.db_name = os.getenv('POSTGRES_DB_NAME', 'investment_db')
        self.db_user = os.getenv('POSTGRES_DB_USER', 'postgres')
        self.db_pass = os.getenv('POSTGRES_DB_PASS')
        self.db_port = os.getenv('POSTGRES_DB_PORT', '5432')

    def get_connection_string(self):
        return f"host={self.db_host} dbname={self.db_name} user={self.db_user} password={self.db_pass} port={self.db_port}"

    @contextmanager
    def get_db_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.get_connection_string())
            yield conn
        finally:
            if conn is not None:
                conn.close()

    @contextmanager
    def get_db_cursor(self):
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                conn.commit()
            finally:
                cursor.close()

    def execute_query(self, query, params=None):
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def test_connection(self):
        return self.execute_query("SELECT 1")[0]['?column?']


if __name__ == "__main__":
    config = DatabaseConfig()
    print(config.get_connection_string())
    print(config.test_connection())
    print(config.execute_query("SELECT * FROM user"))
