import getpass
import os
from contextlib import closing, contextmanager
from decimal import Decimal
from typing import Any, Iterator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection

load_dotenv()


class PostgresDriver:
    def __init__(self) -> None:
        password = os.getenv("PGPASSWORD") or getpass.getpass("PostgreSQL password: ")
        self._connection: connection = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            dbname=os.getenv("PGDATABASE", "test"),
            user=os.getenv("PGUSER", "postgres"),
            password=password,
            connect_timeout=5,
        )
        self._transaction_depth = 0

    def __enter__(self) -> "PostgresDriver":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        if not self._connection.closed:
            self._connection.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._transaction_depth:
            self._transaction_depth += 1
            try:
                yield
            finally:
                self._transaction_depth -= 1
            return

        self._transaction_depth = 1
        try:
            with self._connection:
                yield
        finally:
            self._transaction_depth = 0

    def check_connection(self) -> bool:
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)

    def create_tables(self) -> None:
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        age INT CHECK (age >= 0)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        amount NUMERIC(10, 2) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )

    def get_user_ages(self, names: list[str]) -> dict[str, set[int]]:
        used_ages = {name: set() for name in names}
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    "SELECT name, age FROM users WHERE name = ANY(%s)",
                    (names,),
                )
                for name, age in cursor.fetchall():
                    if age is not None:
                        used_ages[name].add(age)
        return used_ages

    def add_user(self, name: str, age: int) -> tuple[int, str, int]:
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (name, age)
                    VALUES (%s, %s)
                    RETURNING id, name, age
                    """,
                    (name, age),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("Не удалось получить ID созданного пользователя.")
                return row

    def add_order(self, user_id: int, amount: Decimal) -> tuple[int, int, Decimal, Any]:
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO orders (user_id, amount)
                    VALUES (%s, %s)
                    RETURNING id, user_id, amount, created_at
                    """,
                    (user_id, amount),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("Не удалось получить созданный заказ.")
                return row

    def get_user_totals(self) -> list[tuple[int, str, Decimal]]:
        with self.transaction():
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT
                        users.id,
                        users.name,
                        COALESCE(SUM(orders.amount), 0)::NUMERIC(10, 2) AS total_amount
                    FROM users
                    LEFT JOIN orders ON orders.user_id = users.id
                    GROUP BY users.id, users.name
                    ORDER BY total_amount DESC, users.id
                    """
                )
                return cursor.fetchall()
