import unittest
from unittest.mock import MagicMock, patch

from db_helpers import upsert_inventory_stock

class TestDBHelpers(unittest.TestCase):
    @patch('db_helpers._get_conn_from_seeder_or_psycopg2')
    def test_upsert_inventory_stock_calls_db(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Run upsert
        upsert_inventory_stock(('warehouse', 'WH_TEST', 'ITEM_X'), 42.5)

        # Assert cursor executed upsert SQL
        assert mock_cursor.execute.call_count >= 1
        # Check that commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
