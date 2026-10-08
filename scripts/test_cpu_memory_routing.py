"""Check real CPU worker routing and idle exit, without SLURM or large memory use."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_journal_directory import run, server


def check_family(binary, large):
    with tempfile.TemporaryDirectory(prefix="hq-cpu-routing-") as tmp:
        root = Path(tmp)
        env = dict(os.environ, HQ_SERVER_DIR=str(root / "server"))
        cases = [
            # CPU count, requested MiB, eligible for large family
            (1, 100, False),
            (1, 95999, False),
            (1, 96000, True),
            (6, 98303, False),
            (6, 98304, True),
        ]
        with server(binary, root, env, "--no-journal"):
            for index, (cpus, memory, _) in enumerate(cases):
                run(binary, root, env, "submit", "--name", f"routing-{index}",
                    "--cpus", str(cpus), "--resource", f"mem={memory}",
                    "--resource", "worker/cpu=1", "--", "true")

            cpus, memory, group = ((6, 192000, "cpu_large_thirtysecond") if large
                                   else (192, 766000, "cpu_base_full"))
            with (root / "worker.log").open("w") as log:
                worker = subprocess.Popen(
                    [str(binary), "worker", "start", "--detect-resources", "none",
                     "--cpus", str(cpus), "--resource", f"mem=sum({memory})",
                     "--resource", f"worker/cpu=sum({cpus})", "--group", group,
                     "--idle-timeout", "2s", "--heartbeat", "250ms"],
                    cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                )
                try:
                    # Ineligible pending tasks must not keep the worker alive.
                    worker.wait(timeout=15)
                    assert worker.returncode == 0, (root / "worker.log").read_text()
                except subprocess.TimeoutExpired as error:
                    jobs = run(binary, root, env, "--output-mode=json", "job", "list", "--all").stdout
                    workers = run(binary, root, env, "--output-mode=json", "worker", "list", "--all").stdout
                    raise AssertionError(f"Worker did not exit: {jobs}\n{workers}\n"
                                         + (root / "worker.log").read_text() + "\nSERVER:\n"
                                         + (root / "server.log").read_text()) from error
                finally:
                    if worker.poll() is None:
                        worker.kill()
                        worker.wait(timeout=5)

            jobs = json.loads(run(binary, root, env, "--output-mode=json", "job", "list", "--all").stdout)
            by_name = {job["name"]: job for job in jobs}
            for index, (_, _, task_large) in enumerate(cases):
                stats = by_name[f"routing-{index}"]["task_stats"]
                eligible = task_large == large
                assert stats["finished"] == int(eligible), (group, index, stats)
                assert stats["waiting"] == int(not eligible), (group, index, stats)
                assert stats["failed"] == 0, (group, index, stats)
            workers = json.loads(run(binary, root, env, "--output-mode=json", "worker", "list", "--all").stdout)
            assert len(workers) == 1, workers
            assert workers[0]["ended"] is not None, workers


def main():
    binary = Path(sys.argv[1]).resolve()
    for large in [True, False]:
        check_family(binary, large)
        print(f"PASS: {'large' if large else 'base'} connected worker routing and idle exit")


if __name__ == "__main__":
    main()
