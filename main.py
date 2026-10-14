
from seed import seed_database
from postgres_driver import PostgresDriver


def main() -> None:
    with PostgresDriver() as postgres:
        postgres.create_tables()
        while True:
            print("\n=== Управление базой данных ===")
            print("1. Создать таблицы")
            print("2. Добавить тестовые данные")
            print("3. Показать сумму заказов по пользователям")
            print("0. Выход")
            choice = input("Выберите действие: ").strip()

            if choice == "1":
                postgres.create_tables()
                print("Таблицы готовы.")
            elif choice == "2":
                seed_database(postgres)
            elif choice == "3":
                for _, name, total in postgres.get_user_totals():
                    print(f"{name} — {total:.2f}")
            elif choice == "0":
                print("Выход.")
                break
            else:
                print("Неизвестный пункт меню. Введите 1, 2, 3 или 0.")


if __name__ == "__main__":
    main()
