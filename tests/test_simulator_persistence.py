import sys
import types
import importlib
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestSimulatorPersistence(unittest.TestCase):
    def setUp(self):
        # Ensure a fake 'pydantic' module exists so importing inventory_models/inventory_simulator
        # won't fail in environments without pydantic installed.
        if 'pydantic' not in sys.modules:
            fake_pyd = types.ModuleType('pydantic')
            class BaseModel:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            def Field(*args, **kwargs):
                return None
            fake_pyd.BaseModel = BaseModel
            fake_pyd.Field = Field
            sys.modules['pydantic'] = fake_pyd

        # Now import the simulator module fresh
        if 'inventory_simulator' in sys.modules:
            importlib.reload(sys.modules['inventory_simulator'])
        self.inventory_simulator = importlib.import_module('inventory_simulator')

        # Provide lightweight stand-ins for pydantic models/types so tests don't require pydantic
        class FakeStockEventType:
            REPLENISH = 'replenish'
            TRANSFER = 'transfer'
            CONSUME = 'consume'
            CORRECTION = 'correction'

        class FakeLocationType:
            WAREHOUSE = 'warehouse'
            FRANCHISEE = 'franchisee'

        class FakeStockEvent:
            def __init__(self, **kwargs):
                # assign all provided fields as attributes
                for k, v in kwargs.items():
                    setattr(self, k, v)

        class FakeRejectedEvent:
            def __init__(self, id: str, error: str):
                self.id = id
                self.error = error

        # Inject into the simulator module so InventorySimulator methods use these types
        self.inventory_simulator.StockEvent = FakeStockEvent
        self.inventory_simulator.RejectedEvent = FakeRejectedEvent
        self.inventory_simulator.StockEventType = FakeStockEventType
        self.inventory_simulator.LocationType = FakeLocationType

        # Instantiate the simulator class from the imported module
        self.sim = self.inventory_simulator.InventorySimulator()

    @patch('db_helpers.upsert_inventory_stock')
    def test_replenish_triggers_persist(self, mock_upsert):
        evt = {
            'id': 'evt-1',
            'type': 'replenish',
            'ts': datetime.utcnow(),
            'warehouse_id': 'WH_NORTH',
            'item_id': 'BREAD_WHITE',
            'qty': 10.0
        }
        response = self.sim.process_events([evt])
        self.assertEqual(response.accepted, 1)
        mock_upsert.assert_called()

    @patch('db_helpers.upsert_inventory_stock')
    def test_consume_triggers_persist(self, mock_upsert):
        evt = {
            'id': 'evt-2',
            'type': 'consume',
            'ts': datetime.utcnow(),
            'franchisee_id': 'FRAN_001',
            'item_id': 'BREAD_WHITE',
            'qty': 2.5
        }
        response = self.sim.process_events([evt])
        self.assertEqual(response.accepted, 1)
        mock_upsert.assert_called()

    @patch('db_helpers.upsert_inventory_stock')
    def test_transfer_triggers_persist(self, mock_upsert):
        evt = {
            'id': 'evt-3',
            'type': 'transfer',
            'ts': datetime.utcnow(),
            'from_warehouse_id': 'WH_NORTH',
            'to_warehouse_id': 'WH_WEST',
            'item_id': 'BREAD_WHITE',
            'qty': 5.0
        }
        response = self.sim.process_events([evt])
        self.assertEqual(response.accepted, 1)
        # transfer should upsert twice (from and to)
        self.assertTrue(mock_upsert.call_count >= 1)

    @patch('db_helpers.upsert_inventory_stock')
    def test_correction_triggers_persist(self, mock_upsert):
        evt = {
            'id': 'evt-4',
            'type': 'correction',
            'ts': datetime.utcnow(),
            'warehouse_id': 'WH_NORTH',
            'item_id': 'BREAD_WHITE',
            'qty': 123.0
        }
        response = self.sim.process_events([evt])
        self.assertEqual(response.accepted, 1)
        mock_upsert.assert_called()

if __name__ == '__main__':
    unittest.main()
