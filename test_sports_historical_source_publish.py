"""Offline competing-writer tests for append-only historical source publication."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sports_historical_source_publish as publisher

PREFIX = Path('benchmarks/college_nba_history_v1')
SOURCE = PREFIX/'sources'/'NBA'/'train'
PAIR = (SOURCE/'2024-10-22.json.gz', SOURCE/'2024-10-22.receipt.json')
OTHER = (SOURCE/'2024-10-23.json.gz', SOURCE/'2024-10-23.receipt.json')


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.PIPE).decode().strip()


def write_pair(repo, pair, content):
    for item in pair:
        path = Path(repo)/item
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content + item.suffix.encode())


def commit(repo, message):
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
        'commit', '-m', message)


class HistoricalPublicationRaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.remote = root/'remote.git'
        self.caller = root/'caller'
        self.writer = root/'writer'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'clone', '-q', str(self.remote), str(self.caller)], check=True)
        (self.caller/PREFIX).mkdir(parents=True)
        (self.caller/PREFIX/'COVERAGE.latest.json').write_text('{"count":0}')
        commit(self.caller, 'seed')
        git(self.caller, 'branch', '-M', 'main')
        git(self.caller, 'push', 'origin', 'main')
        git(self.remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        subprocess.run(['git', 'clone', '-q', str(self.remote), str(self.writer)], check=True)
        self.initial = git(self.caller, 'rev-parse', 'HEAD')
        write_pair(self.caller, PAIR, b'first')
        self.checks = patch.multiple(publisher,
            expected_originals=lambda: set(PAIR+OTHER),
            ORIGINAL_ROOTS=(PREFIX/'sources',),
            validate_archive=lambda root, now: {'NBA': (sum((Path(root)/pair[0]).exists() for pair in (PAIR,OTHER)), 2)})
        self.checks.start()
        self.addCleanup(self.checks.stop)
        self.coverage = patch.object(publisher, 'rebuild_coverage', side_effect=self.rebuild)
        self.coverage.start()
        self.addCleanup(self.coverage.stop)

    def rebuild(self, tree, counts, now, changed):
        target = Path(tree)/publisher.COVERAGE
        target.write_text(json.dumps({'count':counts['NBA'][0]}, sort_keys=True))

    def remote_files(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'clone', '-q', str(self.remote), directory], check=True)
            return {item: (Path(directory)/item).read_bytes() for item in (PAIR+OTHER)
                    if (Path(directory)/item).exists()}, json.loads((Path(directory)/publisher.COVERAGE).read_text())

    def publish(self, **kwargs):
        return publisher.publish(self.caller, max_attempts=kwargs.pop('max_attempts', 3),
                                 now=publisher.datetime(2026,10,26,tzinfo=publisher.timezone.utc),
                                 **kwargs)

    def test_append_only_publication_keeps_caller_unchanged(self):
        result = self.publish()
        self.assertEqual(result['status'], 'PUBLISHED')
        files, coverage = self.remote_files()
        self.assertEqual(set(files), set(PAIR))
        self.assertEqual(coverage['count'], 1)
        self.assertEqual(git(self.caller, 'rev-parse', 'HEAD'), self.initial)
        self.assertTrue(all((self.caller/p).exists() for p in PAIR))
        self.assertEqual(git(self.caller, 'status', '--porcelain').count('??'), 1)

    def test_overlapping_coverage_and_new_original_rebuild_after_race(self):
        count = [0]
        def race(tree):
            count[0] += 1
            if count[0] == 1:
                write_pair(self.writer, OTHER, b'other')
                (self.writer/publisher.COVERAGE).write_text('{"count":999}')
                commit(self.writer, 'concurrent source and coverage')
                git(self.writer, 'push', 'origin', 'main')
                return subprocess.CompletedProcess([], 1, '', '[rejected] (fetch first)')
            return subprocess.run(['git','push','origin','HEAD:main'],cwd=tree,capture_output=True,text=True)
        result = self.publish(push=race)
        files, coverage = self.remote_files()
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(set(files), set(PAIR+OTHER))
        self.assertEqual(coverage['count'], 2)
        self.assertEqual(git(self.caller, 'rev-parse', 'HEAD'), self.initial)

    def test_conflicting_original_aborts_without_overwrite(self):
        def race(tree):
            write_pair(self.writer, PAIR, b'conflict')
            commit(self.writer, 'other writer owns same original path')
            git(self.writer, 'push', 'origin', 'main')
            return subprocess.CompletedProcess([], 1, '', '[rejected] (fetch first)')
        with self.assertRaisesRegex(ValueError, 'Conflicting historical original'):
            self.publish(push=race)
        files, coverage = self.remote_files()
        self.assertEqual(files[PAIR[0]], b'conflict.gz')
        self.assertEqual(coverage['count'], 0)

    def test_bounded_race_exhaustion_does_not_push(self):
        def reject(tree):
            return subprocess.CompletedProcess([], 1, '', '[rejected] (non-fast-forward)')
        with self.assertRaisesRegex(RuntimeError, 'bounded retries'):
            self.publish(push=reject, max_attempts=2)
        files, coverage = self.remote_files()
        self.assertFalse(files)
        self.assertEqual(coverage['count'], 0)

    def test_unexpected_push_failure_is_not_retried(self):
        calls = []
        def reject(tree):
            calls.append(tree)
            return subprocess.CompletedProcess([], 1, '', 'permission denied')
        with self.assertRaisesRegex(RuntimeError, 'non-race'):
            self.publish(push=reject)
        self.assertEqual(len(calls), 1)

    def test_modified_tracked_original_is_never_republished(self):
        write_pair(self.writer, OTHER, b'original')
        commit(self.writer, 'add tracked original')
        git(self.writer, 'push', 'origin', 'main')
        git(self.caller, 'pull', '--ff-only', 'origin', 'main')
        (self.caller/OTHER[0]).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'modified or deleted'):
            self.publish()

    def test_half_pair_and_unknown_paths_fail_before_push(self):
        (self.caller/PAIR[1]).unlink()
        with self.assertRaisesRegex(ValueError, 'Unpaired'):
            self.publish()
        write_pair(self.caller, PAIR, b'first')
        unknown = SOURCE/'outside.json.gz'
        (self.caller/unknown).write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'Unplanned'):
            self.publish()

    def test_verification_failure_never_publishes(self):
        with patch.object(publisher, 'validate_archive', side_effect=ValueError('source hash mismatch')):
            with self.assertRaisesRegex(ValueError, 'source hash'):
                self.publish()
        files, coverage = self.remote_files()
        self.assertFalse(files)
        self.assertEqual(coverage['count'], 0)


if __name__ == '__main__':
    unittest.main()
