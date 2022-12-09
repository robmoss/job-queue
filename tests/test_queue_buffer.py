"""Test cases that exceed the queue buffer."""

import multiprocessing.connection
import parq


def test_queue_buffer_many_jobs():
    """
    Run sufficiently many jobs that we exceed the completed job queue's buffer
    capacity, which causes the main process to deadlock.
    """
    num_jobs = 2 * multiprocessing.connection.BUFSIZE

    def func(x):
        pass

    values = [(i,) for i in range(num_jobs)]
    n_proc = 2
    result = parq.run(func, values, n_proc=n_proc, trace=False)
    assert result.success
    assert result.num_successful() == num_jobs
    assert result.num_unsuccessful() == 0
