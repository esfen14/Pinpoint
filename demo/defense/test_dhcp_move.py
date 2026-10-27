"""Offline preflight tests for a DHCP address transition."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.dhcp_move import plan_move

class DhcpMoveTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog()
        self.reservations={d.name:d.address for d in self.catalog.devices if d.mode=='dhcp'}
        self.observed={name:[value] for name,value in self.reservations.items()}
    def test_valid_move_preserves_other_reservations(self):
        plan=plan_move(self.catalog,'dynweb01','10.77.1.25',self.reservations,self.observed)
        self.assertEqual(plan['before']['dynweb01'],'10.77.1.20')
        self.assertEqual(plan['after']['dynweb01'],'10.77.1.25')
        self.assertEqual(plan['after']['dynweb02'],'10.77.1.24')
        self.assertEqual(self.reservations['dynweb01'],'10.77.1.20')
    def test_rejects_invalid_or_conflicting_requests_and_observations(self):
        for target,address in [('web03','10.77.1.25'),('dynweb01','10.77.1.21'),('dynweb01','10.77.1.15'),('dynweb01','10.77.1.30'),('dynweb01','10.77.1.25;id')]:
            with self.assertRaises(ValueError):plan_move(self.catalog,target,address,self.reservations,self.observed)
        for observations in [{},dict(self.observed,dynweb02=[]),dict(self.observed,dynweb02=['10.77.1.20'])]:
            with self.assertRaises(ValueError):plan_move(self.catalog,'dynweb01','10.77.1.25',self.reservations,observations)
    def test_same_address_is_a_noop(self):
        plan=plan_move(self.catalog,'dynweb01','10.77.1.20',self.reservations,self.observed)
        self.assertFalse(plan['change'])

if __name__=='__main__':unittest.main()
