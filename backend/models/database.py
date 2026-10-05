import os
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Iterator


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BACKEND_DIR / "marketplace.db")))


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def transaction(immediate: bool = False) -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with closing(_connect()) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS artisans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                community TEXT NOT NULL DEFAULT 'Independent artisan',
                is_marginalized INTEGER NOT NULL DEFAULT 0 CHECK (is_marginalized IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                artisan_id TEXT NOT NULL REFERENCES artisans(id),
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL,
                description TEXT NOT NULL,
                image_url TEXT NOT NULL,
                price_paise INTEGER NOT NULL CHECK (price_paise >= 0),
                stock INTEGER NOT NULL DEFAULT 5 CHECK (stock >= 0),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES products(id),
                artisan_id TEXT NOT NULL REFERENCES artisans(id),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price_paise INTEGER NOT NULL,
                total_paise INTEGER NOT NULL,
                buyer_name TEXT NOT NULL,
                buyer_type TEXT NOT NULL CHECK (buyer_type IN ('retail', 'wholesale')),
                payment_reference TEXT NOT NULL,
                tracking_reference TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'paid',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            CREATE INDEX IF NOT EXISTS idx_products_created ON products(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_orders_artisan ON orders(artisan_id);
            """
        )
        connection.execute(
            """INSERT OR IGNORE INTO artisans (id, name, community, is_marginalized)
               VALUES (?, ?, ?, ?)""",
            ("artisan-demo", "Meera Devi", "Rural artisan collective", 1),
        )


def create_product(product: dict[str, Any]) -> dict[str, Any]:
    with transaction(immediate=True) as connection:
        connection.execute(
            """INSERT INTO products
               (id, artisan_id, title, category, tags, description, image_url, price_paise, stock)
               VALUES (:id, :artisan_id, :title, :category, :tags, :description, :image_url,
                       :price_paise, :stock)""",
            product,
        )
        row = connection.execute(
            """SELECT p.*, a.name AS artisan_name, a.community, a.is_marginalized
               FROM products p JOIN artisans a ON a.id = p.artisan_id WHERE p.id = ?""",
            (product["id"],),
        ).fetchone()
        return _product_dict(row)


def list_products() -> list[dict[str, Any]]:
    with closing(_connect()) as connection:
        rows = connection.execute(
            """SELECT p.*, a.name AS artisan_name, a.community, a.is_marginalized
               FROM products p JOIN artisans a ON a.id = p.artisan_id
               WHERE p.stock > 0 ORDER BY p.created_at DESC"""
        ).fetchall()
        return [_product_dict(row) for row in rows]


def get_product(product_id: str) -> dict[str, Any] | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            """SELECT p.*, a.name AS artisan_name, a.community, a.is_marginalized
               FROM products p JOIN artisans a ON a.id = p.artisan_id WHERE p.id = ?""",
            (product_id,),
        ).fetchone()
        return _product_dict(row) if row else None


def create_order(order: dict[str, Any]) -> dict[str, Any]:
    with transaction(immediate=True) as connection:
        product = connection.execute(
            "SELECT id, artisan_id, price_paise, stock FROM products WHERE id = ?",
            (order["product_id"],),
        ).fetchone()
        if product is None:
            raise LookupError("Product not found")
        if product["stock"] < order["quantity"]:
            raise ValueError("There is not enough stock for that quantity")

        connection.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (order["quantity"], order["product_id"]),
        )
        connection.execute(
            """INSERT INTO orders
               (id, product_id, artisan_id, quantity, unit_price_paise, total_paise, buyer_name,
                buyer_type, payment_reference, tracking_reference, status)
               VALUES (:id, :product_id, :artisan_id, :quantity, :unit_price_paise, :total_paise,
                       :buyer_name, :buyer_type, :payment_reference, :tracking_reference, :status)""",
            {**order, "artisan_id": product["artisan_id"]},
        )
        row = connection.execute(
            """SELECT o.*, p.title AS product_title, a.name AS artisan_name
               FROM orders o JOIN products p ON p.id = o.product_id
               JOIN artisans a ON a.id = o.artisan_id WHERE o.id = ?""",
            (order["id"],),
        ).fetchone()
        return dict(row)


def get_impact() -> dict[str, Any]:
    with closing(_connect()) as connection:
        totals = connection.execute(
            """SELECT COALESCE(SUM(total_paise), 0) AS earnings_paise,
                      COUNT(*) AS orders_count,
                      COUNT(DISTINCT artisan_id) AS artisans_reached,
                      COALESCE(SUM(CASE WHEN a.is_marginalized = 1 THEN total_paise ELSE 0 END), 0)
                        AS marginalized_earnings_paise,
                      COUNT(DISTINCT CASE WHEN a.is_marginalized = 1 THEN o.artisan_id END)
                        AS marginalized_artisans_reached
               FROM orders o JOIN artisans a ON a.id = o.artisan_id WHERE o.status = 'paid'"""
        ).fetchone()
        return dict(totals)


def _product_dict(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["tags"] = [tag for tag in result["tags"].split("|") if tag]
    result["is_marginalized"] = bool(result["is_marginalized"])
    return result