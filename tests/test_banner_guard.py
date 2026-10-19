import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BIN = Path(__file__).resolve().parents[1] / 'bin'
spec = importlib.util.spec_from_file_location('banner_guard', BIN / 'banner_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class BannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = os.environ.copy()
        os.environ['BLACKBOARD_HOME'] = str(self.root / 'state')
        os.environ['BLACKBOARD_SCAN'] = str(self.root)
        guard.HOME = self.root / 'state'
        self.a = self.lesson('a', b'first')
        self.b = self.lesson('b', b'second')

    def tearDown(self):
        os.environ.clear(); os.environ.update(self.old)
        self.temp.cleanup()

    def lesson(self, name, data):
        directory = self.root / name / 'lessons'
        (directory / 'assets').mkdir(parents=True)
        (directory / 'assets/banner.jpg').write_bytes(data)
        path = directory / '0001-test.md'
        path.write_text('---\ntitle: Test\nphoto: assets/banner.jpg\n---\n')
        return path

    def test_unique_and_renamed_copy(self):
        self.assertEqual(guard.audit(), [])
        (self.b.parent / 'assets/copy.jpg').write_bytes(b'first')
        self.b.write_text('---\nphoto: assets/copy.jpg\n---\n')
        self.assertIn('DUPLICATE', guard.audit()[0])
        result = subprocess.run([sys.executable, str(BIN / 'banner_guard.py'), '--lesson', str(self.b)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        render = subprocess.run(['zsh', str(BIN.parent / 'board/render.sh'), str(self.b)], capture_output=True)
        self.assertEqual(render.returncode, 1)
        self.assertIn(b'Duplicate banner', render.stderr)
        self.assertFalse((guard.HOME / 'state.json').exists())

    def test_reservations_sources_and_self_reroll(self):
        args = (b'new', 'https://example/photo', 'Title by Artist')
        self.assertTrue(guard.claim(self.a, *args, self.a.parent / 'assets', '0001'))
        self.assertIsNone(guard.claim(self.b, b'reencoded', args[1], 'different', self.b.parent / 'assets', '0001'))
        self.assertIsNone(guard.claim(self.b, b'reencoded', 'different', args[2], self.b.parent / 'assets', '0001'))
        self.assertTrue(guard.claim(self.a, *args, self.a.parent / 'assets', '0001'))

    def test_concurrent_claims(self):
        code = "import sys;sys.path.insert(0,sys.argv[1]);from banner_guard import claim;print(bool(claim(sys.argv[2],b'race','source','credit',sys.argv[3],'0001')))"
        processes = [subprocess.Popen([sys.executable, '-c', code, str(BIN), str(p), str(p.parent / 'assets')], stdout=subprocess.PIPE) for p in (self.a, self.b)]
        self.assertEqual(sorted(p.communicate()[0].strip() for p in processes), [b'False', b'True'])

if __name__ == '__main__': unittest.main()
