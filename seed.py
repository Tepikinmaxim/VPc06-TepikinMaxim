from datetime import datetime
from decimal import Decimal
from secrets import choice, randbelow

from postgres_driver import PostgresDriver


def seed_database(driver: PostgresDriver) -> None:
    users = (
        ("Анна Иванова", 28),
        ("Иван Петров", 35),
        ("Мария Смирнова", 22),
        ("Алексей Соколов", 31),
        ("Елена Кузнецова", 26),
        ("Дмитрий Морозов", 42),
        ("Ольга Волкова", 33),
        ("Сергей Лебедев", 29),
    )
    driver.create_tables()
    names = [name for name, _ in users]
    used_ages = driver.get_user_ages(names)
    inserted_users: list[tuple[int, str, int]] = []
    inserted_orders: list[tuple[int, int, Decimal, datetime]] = []

    with driver.transaction():
        for name, preferred_age in users:
            available_ages = [
                age for age in range(18, 101) if age not in used_ages[name]
            ]
            if not available_ages:
                raise RuntimeError(
                    f"Для пользователя {name} закончились уникальные возраста "
                    "в диапазоне 18–100."
                )
            age = (
                preferred_age
                if preferred_age in available_ages
                else choice(available_ages)
            )
            inserted_user = driver.add_user(name, age)
            inserted_users.append(inserted_user)
            used_ages[name].add(age)

        for user_id, _, _ in inserted_users:
            for _ in range(2 + randbelow(4)):
                amount = Decimal(randbelow(999_999) + 1) / 100
                inserted_orders.append(driver.add_order(user_id, amount))

    print("Тестовые записи добавлены.")
    print("Добавленные пользователи:")
    for user_id, name, age in inserted_users:
        print(f"  id={user_id}, name={name}, age={age}")
    print("Добавленные заказы:")
    for order_id, user_id, amount, created_at in inserted_orders:
        print(
            f"  id={order_id}, user_id={user_id}, amount={amount:.2f}, "
            f"created_at={created_at}"
        )


if __name__ == "__main__":
    with PostgresDriver() as postgres:
        seed_database(postgres)
