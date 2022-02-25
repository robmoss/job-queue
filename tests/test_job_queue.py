"""Test cases for jobq.run."""

import logging
import multiprocessing
import os
import signal
import time

import jobq

# NOTE: this test runs correctly on my laptop, but fails on Gitlab CI.
# Even though the worker tasks are terminated, their exit codes are zero.
# I cannot figure out why this occurs on the CI machines, but not on mine.
def do_not_test_ctrl_c():
    """
    Test that run() handles Ctrl+C events as expected.
    """

    def job(n):
        logger = multiprocessing.get_logger()
        logger.info('Worker received {}'.format(n))
        time.sleep(0.5)
        logger.info('Worker finished with {}'.format(n))

    def run_main(num_tasks, status):
        logger = multiprocessing.get_logger()
        try:
            pid = multiprocessing.current_process().pid
            logger.info('HELLO from {}'.format(pid))
            values = [(i,) for i in range(num_tasks)]
            success = jobq.run(job, values, n_proc=2)
        except KeyboardInterrupt:
            logger.info('Caught KeyboardInterrupt, exiting')
            status.value = 19
        logger.info('Success = {}'.format(success))
        if success:
            status.value = 0
        else:
            status.value = 12
        logger.info('Status = {}'.format(status.value))
        logger.info('GOODBYE from {}'.format(pid))
        return success

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(logging.INFO)
    logger.info('Master PID is {}'.format(
        multiprocessing.current_process().pid))

    status = multiprocessing.Value('i', 0)
    num_tasks = 100
    main = multiprocessing.Process(target=run_main, args=(num_tasks, status))

    # NOTE: must wait for the process to start before interrupting it.
    main.start()
    time.sleep(1)
    logger.info('Sending signal to {}'.format(main.pid))
    if hasattr(signal, 'CTRL_C_EVENT'):
        os.kill(main.pid, signal.CTRL_C_EVENT)
    else:
        os.kill(main.pid, signal.SIGINT)

    # Wait for the process to terminate.
    main.join()

    # Ensure the status indicates that not all tasks completed successfully.
    logger.info('Status = {}'.format(status.value))
    assert status.value == 12


def test_success():

    def func(x):
        pass

    # Run the functions in parallel and ensure it completed successfully.
    values = [(i,) for i in range(10)]
    n_proc = 2
    success = jobq.run(func, values, n_proc=n_proc)
    assert success


def test_failure_early(caplog):
    # NOTE: The caplog fixture captures logging; see the pytest documentation:
    # https://docs.pytest.org/en/stable/logging.html
    caplog.set_level(logging.INFO)

    def func(x):
        if x == 3:
            raise ValueError('x == 3')

    # Run the functions in parallel and ensure it failed to complete.
    values = [(i,) for i in range(10)]
    n_proc = 2
    # NOTE: hide the exception stack trace with trace=False.
    success = jobq.run(func, values, n_proc=n_proc, trace=False)
    assert not success

    # The failure at x == 3 should result in all worker processes failing.
    failed_workers = [rec for rec in caplog.records
                      if 'exit code: 1' in rec.message]
    num_failed_workers = len(failed_workers)
    assert num_failed_workers == 2


def test_failure_late(caplog):
    # NOTE: The caplog fixture captures logging; see the pytest documentation:
    # https://docs.pytest.org/en/stable/logging.html
    caplog.set_level(logging.INFO)

    def func(x):
        if x == 3:
            raise ValueError('x == 3')

    # Run the functions in parallel and ensure it failed to complete.
    values = [(i,) for i in range(10)]
    n_proc = 2
    # NOTE: hide the exception stack trace with trace=False.
    success = jobq.run(func, values, n_proc=n_proc,
                       fail_early=False, trace=False)
    assert not success

    # The failure at x == 3 should result in only one worker process failing.
    failed_workers = [rec for rec in caplog.records
                      if 'exit code: 1' in rec.message]
    num_failed_workers = len(failed_workers)
    assert num_failed_workers == 1
