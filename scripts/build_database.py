import random
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path("data/enterprise.db")
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
DEPARTMENTS = ["Engineering", "Sales", "Customer Success", "Marketing", "Operations"]
PRODUCTS = ["Core Platform", "Analytics Add-on", "Premium Support", "Integrations Suite"]


def create_schema(conn):
    conn.executescript(
        """
        DROP TABLE IF EXISTS revenue;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS employee_satisfaction;

        CREATE TABLE revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            region TEXT NOT NULL,
            amount REAL NOT NULL
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            churn_date TEXT,
            status TEXT NOT NULL
        );

        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            units INTEGER NOT NULL
        );

        CREATE TABLE employee_satisfaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarter TEXT NOT NULL,
            department TEXT NOT NULL,
            score REAL NOT NULL
        );
        """
    )


def month_range(start_year, start_month, count):
    year, month = start_year, start_month
    for _ in range(count):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month > 12:
            month = 1
            year += 1


def populate_revenue(conn, rng):
    base_by_region = {
        "North America": 420000,
        "Europe": 310000,
        "Asia Pacific": 260000,
        "Latin America": 140000,
    }
    rows = []
    for i, month in enumerate(month_range(2024, 1, 24)):
        for region, base in base_by_region.items():
            growth = 1 + (i * 0.015)
            noise = rng.uniform(0.9, 1.1)
            amount = round(base * growth * noise, 2)
            rows.append((month, region, amount))
    conn.executemany(
        "INSERT INTO revenue (month, region, amount) VALUES (?, ?, ?)", rows
    )


def populate_customers(conn, rng):
    rows = []
    for i in range(1, 121):
        region = rng.choice(REGIONS)
        signup_year = rng.choice([2023, 2024, 2025])
        signup_month = rng.randint(1, 12)
        signup_date = date(signup_year, signup_month, rng.randint(1, 28))
        churned = rng.random() < 0.18
        churn_date = None
        status = "active"
        if churned:
            churn_month = min(signup_month + rng.randint(1, 10), 12)
            churn_year = signup_year if churn_month >= signup_month else signup_year + 1
            churn_date = date(churn_year, churn_month, rng.randint(1, 28)).isoformat()
            status = "churned"
        rows.append(
            (f"Customer {i}", region, signup_date.isoformat(), churn_date, status)
        )
    conn.executemany(
        "INSERT INTO customers (name, region, signup_date, churn_date, status) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def populate_sales(conn, rng):
    rows = []
    for month in month_range(2024, 1, 24):
        year, mon = month.split("-")
        for _ in range(rng.randint(15, 25)):
            day = rng.randint(1, 28)
            sale_date = f"{year}-{mon}-{day:02d}"
            region = rng.choice(REGIONS)
            product = rng.choice(PRODUCTS)
            units = rng.randint(1, 40)
            unit_price = rng.uniform(200, 1500)
            amount = round(units * unit_price, 2)
            rows.append((sale_date, region, product, amount, units))
    conn.executemany(
        "INSERT INTO sales (sale_date, region, product, amount, units) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def populate_employee_satisfaction(conn, rng):
    rows = []
    quarters = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2"]
    for quarter in quarters:
        for department in DEPARTMENTS:
            score = round(rng.uniform(3.2, 4.6), 2)
            rows.append((quarter, department, score))
    conn.executemany(
        "INSERT INTO employee_satisfaction (quarter, department, score) VALUES (?, ?, ?)",
        rows,
    )


def build(db_path=None):
    db_path = Path(db_path) if db_path else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        populate_revenue(conn, rng)
        populate_customers(conn, rng)
        populate_sales(conn, rng)
        populate_employee_satisfaction(conn, rng)
        conn.commit()
    finally:
        conn.close()
    print(f"Built {db_path}")
    return db_path


if __name__ == "__main__":
    build()
