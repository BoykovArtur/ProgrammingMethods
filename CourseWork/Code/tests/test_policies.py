import os
import sys
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MONITOR = os.path.join(ROOT, 'drone', 'modules', 'monitor', 'module')
sys.path.insert(0, MONITOR)

from policies import policies, check_operation  # noqa: E402


event_id = 0


def next_event():
    global event_id
    event_id += 1
    return str(event_id)


class TestPolicies(unittest.TestCase):
    def test_wms_to_communication(self):
        self.assertTrue(
            check_operation(next_event(), {
                'source': 'wms',
                'deliver_to': 'communication',
            })
        )

    def test_orchestrator_to_movement(self):
        self.assertTrue(
            check_operation(next_event(), {
                'source': 'emergency-braking',
                'deliver_to': 'movement-system',
            })
        )

    def test_denied(self):
        self.assertFalse(
            check_operation(next_event(), {
                'source': 'drone',
                'deliver_to': 'evil',
            })
        )

    def test_policies_nonempty(self):
        self.assertGreater(len(policies), 5)


if __name__ == '__main__':
    unittest.main()
