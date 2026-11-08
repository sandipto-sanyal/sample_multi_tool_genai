"""Utility for connecting to a MySQL database and running queries.

Secrets are loaded from a .env file via python-dotenv. Create a .env file
alongside this module with the following keys:

    MYSQL_HOST=localhost
    MYSQL_PORT=3306
    MYSQL_USER=your_user
    MYSQL_PASSWORD=your_password
    MYSQL_DATABASE=your_database
"""

import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd


class MySQLConnector:
    """A small wrapper around a MySQL connection.

    Reads connection settings from environment variables (loaded from .env)
    so credentials never live in source code.
    """

    def __init__(self, database_name=None):
        # Load variables from .env into the environment.
        load_dotenv(override=True)

        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASSWORD")
        self.database = database_name if database_name else os.getenv("MYSQL_DATABASE")

        if not all([self.user, self.password, self.database]):
            raise ValueError(
                "Missing MySQL credentials. Please set MYSQL_USER, "
                "MYSQL_PASSWORD and MYSQL_DATABASE in your .env file."
            )

        self.connection = None

    def connect(self):
        """Open a connection to the database (idempotent)."""
        if self.connection is not None and self.connection.is_connected():
            return self.connection

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                read_timeout=30,
                # timeout=30
            )
            if self.connection.is_connected():
                print(f"Connected to MySQL database '{self.database}'.")
            return self.connection
        except Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}") from e

    def execute_query(self, query, params=None):
        """Execute a query and return the results.

        For SELECT statements a list of rows (dicts) is returned. For
        INSERT/UPDATE/DELETE the change is committed and the affected
        row count is returned.

        Args:
            query: The SQL query string. Use %s placeholders for params.
            params: Optional tuple/list of parameters to bind safely.
        """
        self.connect()

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())

            if cursor.with_rows:
                rows = cursor.fetchall()
                return pd.DataFrame(rows)

            self.connection.commit()
            return cursor.rowcount
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Query failed: {e}") from e
        finally:
            cursor.close()

    def close(self):
        """Close the database connection if it is open."""
        if self.connection is not None and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            print("MySQL connection closed.")

    # Allow use as a context manager: `with MySQLConnector() as db: ...`
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Sample usage: run a query the user provides.
    db = MySQLConnector(database_name="employees")
    create_table = '''
CREATE TABLE IF NOT EXISTS users (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(50) NOT NULL UNIQUE,
email VARCHAR(100) NOT NULL UNIQUE,
password_hash VARCHAR(255) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);'''
    insert_query = '''INSERT INTO users (username, email, password_hash)
VALUES ('sandipto', 'sandipto@example.com', 'hashed_password_here');
'''
    select_query = '''SELECT d.dept_name, AVG(s.salary) AS average_salary
FROM salaries s
JOIN dept_emp de ON s.emp_no = de.emp_no
JOIN departments d ON de.dept_no = d.dept_no
GROUP BY d.dept_name;'''

    schema_query = '''SHOW TABLES;'''
    results = db.execute_query(schema_query)

    if isinstance(results, pd.DataFrame):
        results.to_csv("report.csv", index=False)
    else:
        print(results)
