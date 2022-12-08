"""Test cases for parq.run."""

import logging
import parq


def test_success(caplog):
    # NOTE: The caplog fixture captures logging; see the pytest documentation:
    # https://docs.pytest.org/en/stable/logging.html
    caplog.set_level(logging.INFO)

    def func(x):
        pass

    # Run the functions in parallel and ensure it completed successfully.
    values = [(i,) for i in range(10)]
    n_proc = 2
    result = parq.run(func, values, n_proc=n_proc, level=logging.WARNING)
    assert result.success

    assert 'Spawning 2 workers for 10 jobs' in caplog.text
    assert result.num_successful() == 10
    assert result.num_unsuccessful() == 0


def test_success_fewer_workers(caplog):
    # NOTE: The caplog fixture captures logging; see the pytest documentation:
    # https://docs.pytest.org/en/stable/logging.html
    caplog.set_level(logging.INFO)

    def func(x):
        pass

    # Run the functions in parallel and ensure it completed successfully.
    values = [(i,) for i in range(2)]
    n_proc = 10
    result = parq.run(func, values, n_proc=n_proc, level=logging.WARNING)
    assert result.success

    assert 'Spawning 2 workers for 2 jobs' in caplog.text
    assert result.num_successful() == 2
    assert result.num_unsuccessful() == 0


def test_failure_early():

    def func(x):
        if x == 3:
            raise ValueError('x == 3')

    # Run the functions in parallel and ensure it failed to complete.
    values = [(i,) for i in range(100)]
    n_proc = 2
    result = parq.run(func, values, n_proc=n_proc, level=logging.WARNING)
    assert not result.success

    # The failure at x == 3 should result in all worker processes failing.
    assert result.failed_worker_count == 2
    assert (3,) in result.unsuccessful_jobs
    assert result.num_unsuccessful() > 2
    assert result.num_successful() < 90


def test_failure_late():

    def func(x):
        if x == 3:
            raise ValueError('x == 3')

    # Run the functions in parallel and ensure it failed to complete.
    values = [(i,) for i in range(10)]
    n_proc = 2
    result = parq.run(func, values, n_proc=n_proc, fail_early=False,
                      level=logging.WARNING)
    assert not result.success

    # The failure at x == 3 should result in only one worker process failing.
    assert result.failed_worker_count == 1
    assert (3,) in result.unsuccessful_jobs
    assert result.num_unsuccessful() == 1
    assert result.num_successful() == 9
