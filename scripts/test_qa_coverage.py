"""Offline coverage claims must match sources and every expected item."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('qa_coverage.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class CoverageTests(unittest.TestCase):
    def fixture(self, root):
        catalog={'TC-SS-04':dict(expectations=['Hidden sidebar and redirect'],procedure='Sign in and navigate')}
        adapter=root/'client/e2e/permissions.ts';adapter.parent.mkdir(parents=True)
        adapter.write_text("test('TC-SS-04: permission', () => { /* qa-evidence:TC-SS-04:E1 */ });")
        config=root/'client/playwright.qa.config.ts';config.write_text('// isolated config')
        registry=c.blank_registry(catalog)
        record=registry['cases']['TC-SS-04']
        record.update(status='implemented',mode='scripted automation',reviewed_by='Reviewer',
            reviewed_at='2026-10-18',procedure_review='All written steps accounted for',
            prerequisites=['Existing disposable Staff account'],recovery=['Log out and close context'],
            adapter=dict(path='client/e2e/permissions.ts',title='TC-SS-04: permission',
                         project='qa-permissions',config='client/playwright.qa.config.ts'),
            source_hashes={str(p.relative_to(root)):c.file_hash(p) for p in (adapter,config)},
            items={'E1':dict(marker='qa-evidence:TC-SS-04:E1',method='UI assertions')})
        return catalog,registry

    def test_complete_source_review_is_implementation_not_runtime_pass(self):
        with tempfile.TemporaryDirectory() as d:
            catalog,r=self.fixture(Path(d));c.validate(r,catalog,Path(d))
            preview=c.render(r,catalog)
            self.assertIn('not a runtime result',preview)
            self.assertIn('TC-SS-04',preview)
            self.assertNotIn('| PASS |',preview)

    def test_missing_unknown_or_stale_case_claim_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            catalog,r=self.fixture(Path(d))
            for edit in ('missing','unknown','changed'):
                altered=copy.deepcopy(r)
                if edit=='missing':altered['cases'].clear()
                elif edit=='unknown':altered['cases']['TC-XX-01']=copy.deepcopy(next(iter(r['cases'].values())))
                else:altered['cases']['TC-SS-04']['case_hash']='0'*64
                with self.subTest(edit=edit),self.assertRaises(ValueError):c.validate(altered,catalog,Path(d))

    def test_missing_expected_item_or_assertion_marker_cannot_claim_implemented(self):
        with tempfile.TemporaryDirectory() as d:
            catalog,r=self.fixture(Path(d));r['cases']['TC-SS-04']['items']={}
            with self.assertRaisesRegex(ValueError,'expected'):c.validate(r,catalog,Path(d))
            r['cases']['TC-SS-04']['status']='partial'
            c.validate(r,catalog,Path(d))
            r['cases']['TC-SS-04']['items']={'E2':dict(marker='invented',method='guess')}
            with self.assertRaises(ValueError):c.validate(r,catalog,Path(d))

    def test_source_drift_path_escape_and_missing_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);catalog,r=self.fixture(root)
            for field,value in [('reviewed_by',''),('source_hashes',{}),('adapter',dict(path='../escape'))]:
                altered=copy.deepcopy(r);altered['cases']['TC-SS-04'][field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):c.validate(altered,catalog,root)
            (root/'client/e2e/permissions.ts').write_text('// changed')
            with self.assertRaisesRegex(ValueError,'changed'):c.validate(r,catalog,root)

    def test_full_registry_includes_all_cases_without_inventing_coverage(self):
        catalog=c.catalog.load_catalog();r=c.blank_registry(catalog);c.validate(r,catalog)
        self.assertEqual(len(r['cases']),239)
        self.assertTrue(all(v['status']=='unmapped' and not v['items'] for v in r['cases'].values()))


if __name__=='__main__':unittest.main()
