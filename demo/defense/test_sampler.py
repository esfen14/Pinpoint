"""Offline tests for the rehearsal resource sampler's parsing and summary."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense import sampler


class SamplerTests(unittest.TestCase):
    def test_summary_reports_minimum_ram_swap_movement_and_disk(self):
        rows=[(100,8000,10,5,40000),(105,7000,10,5,39000),(110,7500,60,9,38000)]
        summary=sampler.summarize(rows)
        self.assertEqual(summary,{'samples':3,'seconds':10,'min_available_mib':7000,'swap_in_pages':50,'swap_out_pages':4,
                                  'max_swap_pages_per_second':10.8,'min_free_disk_mib':38000})
    def test_rows_roundtrip_and_malformed_files_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'samples.txt'
            sampler.append(path,(100,8000,10,5,40000));sampler.append(path,(105,7900,12,5,39900))
            self.assertEqual(sampler.read(path),[(100,8000,10,5,40000),(105,7900,12,5,39900)])
            path.write_text('1 2 3\\n')
            with self.assertRaises(ValueError):sampler.read(path)
            path.write_text('')
            with self.assertRaises(ValueError):sampler.summarize(sampler.read(path))
    def test_counters_going_backwards_are_refused(self):
        with self.assertRaises(ValueError):sampler.summarize([(1,5000,10,10,9000),(2,5000,5,10,9000)])
    def test_sample_has_a_hard_duration_limit_and_interval_range(self):
        for args in ((0,1),(10,0),(10,61),(86401,5)):
            with self.assertRaises(ValueError):sampler.check_limits(*args)
        sampler.check_limits(3600,5)
if __name__=='__main__':unittest.main()
