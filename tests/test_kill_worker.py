"""Test cases that kill worker processes."""

import os
import parq
import time


def test_kill_worker_single():
    """
    Kill a single worker process.
    """

    def func(kill):
        # NOTE: make each job take a non-zero amount of time to complete.
        time.sleep(0.01)
        if kill:
            os.kill(os.getpid(), 9)

    n_proc = 2
    n_jobs = 16
    timeout = 1
    kill_at = 7

    values = [(i == kill_at,) for i in range(n_jobs)]

    result = parq.run(
        func,
        values,
        n_proc=n_proc,
        timeout=timeout,
    )

    assert not result.success
    assert len(result.successful_jobs) == n_jobs - 1
    assert len(result.unsuccessful_jobs) == 1
    assert result.failed_worker_count == 1


def test_kill_worker_all():
    """
    Kill all worker processes.
    """

    def func(kill):
        # NOTE: make each job take a non-zero amount of time to complete.
        time.sleep(0.01)
        if kill:
            os.kill(os.getpid(), 9)

    n_proc = 2
    n_jobs = 16
    timeout = 1
    kill_from = 7

    values = [(i >= kill_from,) for i in range(n_jobs)]

    result = parq.run(
        func,
        values,
        n_proc=n_proc,
        timeout=timeout,
    )

    assert not result.success
    assert len(result.successful_jobs) <= kill_from
    assert len(result.unsuccessful_jobs) >= (n_jobs - kill_from)
    assert result.failed_worker_count == n_proc
