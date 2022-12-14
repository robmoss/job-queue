"""Test cases for retrieving job results."""

import parq


def test_results_simple():
    """
    Ensure that we can retrieve the results of a small number of jobs, where
    each job returns a scalar value.
    """
    job_count = 10
    n_proc = 4

    values = [(i,) for i in range(job_count)]

    def func(x):
        return 2 * x

    result = parq.run(func, values, n_proc, results=True)
    assert result

    # Check the result of each job.
    for i in range(job_count):
        assert result.job_results[i] == 2 * i


def test_results_large():
    """
    Ensure that we can retrieve the results of many jobs, where each job
    returns a large data structure.
    """

    job_count = 200
    result_length = 1_000_000
    n_proc = 2

    values = [(i,) for i in range(job_count)]

    def func(x):
        return [x for _ in range(result_length)]

    result = parq.run(func, values, n_proc, results=True)
    assert result

    # Check the result of each job.
    for i in range(job_count):
        output = result.job_results[i]
        assert len(output) == result_length
