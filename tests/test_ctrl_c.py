import logging
import multiprocessing
import os
import signal
import sys

import parq


def test_ctrl_c_handled():
    """
    Test that run() handles Ctrl+C events as expected.
    """

    def func(n, pid):
        if n == 5:
            os.kill(pid, signal.SIGINT)

    def run_queue(count):
        logger = multiprocessing.log_to_stderr()
        logger.setLevel(logging.WARNING)

        pid = os.getpid()
        values = [(i, pid) for i in range(count)]
        n_proc = 3

        success = parq.run(func, values, n_proc=n_proc)
        if success:
            sys.exit(0)
        else:
            sys.exit(42)

    # Ensure that Ctrl+C causes the workers to fail.
    proc = multiprocessing.Process(target=run_queue, args=[20])
    proc.start()
    proc.join()
    assert proc.exitcode == 42

    # Ensure that without Ctrl+C the workers succeed.
    proc = multiprocessing.Process(target=run_queue, args=[4])
    proc.start()
    proc.join()
    assert proc.exitcode == 0
