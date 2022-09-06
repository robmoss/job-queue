import logging
import multiprocessing
import os
import signal

import parq


def test_ctrl_c_handled():
    """
    Test that run() handles Ctrl+C events as expected.
    """

    def func(n, pid):
        if n == 5:
            os.kill(pid, signal.SIGINT)

    def run_queue():
        logger = multiprocessing.log_to_stderr()
        logger.setLevel(logging.INFO)

        pid = os.getpid()
        values = [(i, pid) for i in range(20)]
        n_proc = 3

        success = parq.run(func, values, n_proc=n_proc)
        assert not success

    proc = multiprocessing.Process(target=run_queue, args=[])
    proc.start()
    proc.join()
