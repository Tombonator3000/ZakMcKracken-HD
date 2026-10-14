#!/usr/bin/env python3
"""Sjekker patchkontrollen i engine/build-pages.py med små midlertidige git-repoer.

Fra Dig-HD-Web (a8e4474, engine/tests/test-build-pages.py), tilpasset Zak: verify_patches
gir også stiene patchene berører, så nye filer (dighd.cpp, verbhjul.cpp) kommer med i
kildearkivet på nettsiden.

Bruk:  python3 engine/tests/test-build-pages.py -v
"""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('build_pages', Path(__file__).resolve().parents[1] / 'build-pages.py')
BUILD_PAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_PAGES)


class PatchStackTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dighd-patch-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'existing.txt').write_text('base\n')
        (self.repo / 'untouched.txt').write_text('keep\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Patch Test', '-c', 'user.email=patch-test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'baseline')
        (self.repo / 'existing.txt').write_text('first\n')
        (self.repo / 'new file.txt').write_text('created\n')
        self.git('add', '.')
        first = self.root / '0001.patch'
        first.write_bytes(self.git('diff', '--cached', 'HEAD'))
        (self.repo / 'existing.txt').write_text('second\n')
        (self.repo / 'new file.txt').write_text('created\nsecond\n')
        second = self.root / '0002.patch'
        second.write_bytes(self.git('diff'))
        self.patches = [first, second]
        # The real index intentionally contains only the first patch, and an
        # unrelated worktree edit must survive both success and failure.
        (self.repo / 'untouched.txt').write_text('user work\n')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def snapshot(self):
        index = hashlib.sha256((self.repo / '.git/index').read_bytes()).hexdigest()
        files = {str(path.relative_to(self.repo)): path.read_bytes()
                 for path in self.repo.iterdir() if path.is_file()}
        return index, files

    def test_accepts_stacked_patches_without_mutating_source_or_index(self):
        before = self.snapshot()
        paths = BUILD_PAGES.verify_patches(self.repo, self.patches)
        self.assertEqual(self.snapshot(), before)
        # The new file is not tracked by git, but must go into the source archive
        self.assertEqual(paths, {'existing.txt', 'new file.txt'})

    def test_rejects_a_missing_later_change_without_mutating_source_or_index(self):
        (self.repo / 'new file.txt').write_text('created\n')
        before = self.snapshot()
        with self.assertRaises(subprocess.CalledProcessError):
            BUILD_PAGES.verify_patches(self.repo, self.patches)
        self.assertEqual(self.snapshot(), before)

    def test_rejects_extra_changes_in_a_patched_file(self):
        (self.repo / 'existing.txt').write_text('second\nextra\n')
        before = self.snapshot()
        with self.assertRaises(subprocess.CalledProcessError):
            BUILD_PAGES.verify_patches(self.repo, self.patches)
        self.assertEqual(self.snapshot(), before)


class StackOrderTest(unittest.TestCase):
    def test_engine_patches_before_browser_patches(self):
        stack = BUILD_PAGES.patch_stack()
        names = [p.parent.name + '/' + p.name for p in stack]
        self.assertEqual(names[:2], ['patches/0001-dighd-hd-grafikk.patch', 'patches/0002-verbhjul.patch'])
        self.assertTrue(all(name.startswith('patches-web/') for name in names[2:]))


if __name__ == '__main__':
    unittest.main()
