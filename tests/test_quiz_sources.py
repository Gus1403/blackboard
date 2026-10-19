import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

class SourceQuizTests(unittest.TestCase):
    def test_source_prompt_and_five_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / 'lessons').mkdir(); (ws / 'sources').mkdir()
            source = ws / 'sources/practice.txt'
            source.write_text('Q1: example practice question')
            lesson = ws / 'lessons/0001-test.md'
            lesson.write_text('---\ncourse: ECE\n---\n::: quiz\ntopics: logic\n:::\n')
            item = {'q': 'Variant', 'options': ['1','2','3','4','5'], 'key': 4, 'why': 'practice.txt Q1, changed inputs'}
            with patch.object(sys, 'argv', ['quiz.py', str(lesson), '{"mode":"mcq"}']), patch('shutil.which', return_value='/bin/claude'), patch('subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps([item]))) as call:
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(ROOT / 'bin/quiz.py'), run_name='__main__')
            self.assertEqual(result.exception.code, 0)
            prompt = call.call_args.args[0][2]
            self.assertIn(str(source), prompt)
            self.assertIn('SOURCE FIDELITY', prompt)
            self.assertIn('Read the relevant files', prompt)
            self.assertIn('::: mcq q1 e', lesson.read_text())
            self.assertIn('- 5', lesson.read_text())

if __name__ == '__main__': unittest.main()
