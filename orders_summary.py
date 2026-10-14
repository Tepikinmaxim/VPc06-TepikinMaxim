import sys

import psycopg2
from postgres_driver import PostgresDriver


def show_order_totals(driver: PostgresDriver) -> None:
    try:
        rows = driver.get_user_totals()
    except psycopg2.Error as error:
        print(f"Ошибка PostgreSQL при получении сводки заказов: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print("Сумма заказов по пользователям:")
    for _, name, total_amount in rows:
        print(f"{name} — {total_amount:.2f}")


if __name__ == "__main__":
    with PostgresDriver() as postgres:
        show_order_totals(postgres)
