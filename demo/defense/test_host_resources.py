"""Offline tests for pilot preflight resource and subnet rules."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.host_resources import swap_rate, check_host_resources, reject_foreign_overlaps


class HostResourceTests(unittest.TestCase):
    def test_reserve_disk_and_swap_thrash_are_each_refused(self):
        self.assertTrue(check_host_resources(3072,20480,0))
        for args in [(3071,40000,0),(8000,20479,0),(8000,40000,51)]:
            with self.assertRaises(ValueError):check_host_resources(*args)
    def test_invalid_inventory_is_refused(self):
        for args in [(-1,40000,0),('8000',40000,0),(8000,40000,-1),(True,40000,0)]:
            with self.assertRaises(ValueError):check_host_resources(*args)
    def test_swap_rate_uses_both_directions_and_rejects_bad_samples(self):
        self.assertEqual(swap_rate((10,20),(110,70),5),30)
        for args in [((10,20),(5,70),5),((10,20),(10,20),0),((1,),(2,3),1),((-1,0),(0,0),1)]:
            with self.assertRaises(ValueError):swap_rate(*args)
    def test_owned_subnet_is_allowed_once_and_all_other_overlaps_refused(self):
        base=['192.168.57.0/24','192.168.57.1','172.17.0.0/16']
        self.assertTrue(reject_foreign_overlaps(base+['10.77.1.0/27'],'10.77.1.0/27'))
        for extra in (['10.77.1.0/27'],['10.0.0.0/8'],['10.77.1.5'],['10.77.1.0/28'],['10.77.0.0/16']):
            with self.assertRaises(ValueError):reject_foreign_overlaps(base+['10.77.1.0/27']+extra,'10.77.1.0/27')
        for broken in (base,base+['bad'],base+['10.77.1.0/27',None]):
            with self.assertRaises(ValueError):reject_foreign_overlaps(broken,'10.77.1.0/27')
if __name__=='__main__':unittest.main()
