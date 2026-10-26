"""Keep import packaging source-only without reading real local credentials."""
import tempfile
import unittest
from pathlib import Path
from scripts.package_replit import FILES, source_files


class ReplitPackageTests(unittest.TestCase):
    def fixture(self, root):
        for name in FILES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic source fixture')

    def test_allowlist_excludes_runtime_data_and_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            for name in ('.env', '.env.local', 'var/records.sqlite3',
                         'careerquest/.env', 'careerquest/__pycache__/cached.py',
                         'frontend/node_modules/package/index.js'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic excluded fixture')
            (root / 'careerquest/api.py').write_text('# source')
            names = {name for _, name in source_files(root)}
            self.assertEqual(names, set(FILES) | {'careerquest/api.py'})

    def test_linked_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / 'careerquest').mkdir(exist_ok=True)
            (root / 'careerquest/linked.py').symlink_to(root / 'README.md')
            with self.assertRaisesRegex(ValueError, 'Refusing linked source'):
                list(source_files(root))
