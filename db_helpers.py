"""
Database helper utilities for inventory persistence.
"""
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def _get_conn_from_seeder_or_psycopg2():
    """Try to obtain a psycopg2 connection from seed_mcdonalds_inventory.get_db_connection if available,
    otherwise fall back to a direct psycopg2.connect with sensible defaults.
    """
    try:
        from seed_mcdonalds_inventory import get_db_connection  # type: ignore
        conn = get_db_connection()
        return conn
    except Exception:
        try:
            import psycopg2
        except Exception:
            logger.debug("psycopg2 not available; cannot persist to DB")
            return None

        try:
            # Default connection parameters used elsewhere in repo
            conn = psycopg2.connect(host="localhost", database="logistics", user="postgres", password="postgres", port=5432)
            return conn
        except Exception as e:
            logger.debug(f"Failed to connect to Postgres for persistence: {e}")
            return None


def upsert_inventory_stock(key: Tuple[str, str, str], qty: float):
    """Upsert a single inventory stock row into `inventory_stock`.

    key: (location_type, location_id, item_id)
    qty: new quantity (decimal)

    This function is best-effort and will log instead of raising if DB is unavailable.
    """
    loc_type, loc_id, item_id = key

    conn = _get_conn_from_seeder_or_psycopg2()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        # Ensure the item exists in inventory_items to satisfy FK constraint
        try:
            cur.execute("SELECT 1 FROM inventory_items WHERE item_id = %s", (item_id,))
            if cur.fetchone() is None:
                try:
                    cur.execute(
                        "INSERT INTO inventory_items (item_id, name, category, unit, shelf_life_days) VALUES (%s, %s, %s, %s, %s)",
                        (item_id, item_id, 'unknown', 'each', None)
                    )
                except Exception:
                    logger.debug(f"Could not insert placeholder inventory_items row for {item_id}")

        except Exception:
            # If query fails, continue to upsert attempt
            logger.debug("Error while ensuring inventory_items row exists; continuing to upsert")

        # Upsert into inventory_stock
        cur.execute(
            """
            INSERT INTO inventory_stock (location_type, location_id, item_id, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (location_type, location_id, item_id)
            DO UPDATE SET quantity = EXCLUDED.quantity, last_updated = CURRENT_TIMESTAMP
            """,
            (loc_type, loc_id, item_id, qty)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception(f"Failed to upsert inventory_stock for {key}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
