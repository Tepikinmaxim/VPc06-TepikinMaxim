import unittest

from postgres_driver import PostgresDriver


class PostgreSQLConnectionTest(unittest.TestCase):
    def test_connects_and_runs_query(self) -> None:
        with PostgresDriver() as postgres:
            self.assertTrue(postgres.check_connection())


if __name__ == "__main__":
    unittest.main()
