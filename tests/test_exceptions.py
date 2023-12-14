"""Test cases for exceptions that depend on system resource depletion."""

import multiprocessing
import parq
import pytest
import queue


def test_generic_exception(monkeypatch, capsys):
    """
    Test that parq.run() catches exceptions other than KeyboardInterrupt, and
    prints a traceback to stderr.
    """

    def mock_process_exception(*args, **kwargs):
        raise Exception()

    def func(x):
        pass

    values = [(i,) for i in range(2)]
    n_proc = 10

    with monkeypatch.context() as m:
        m.setattr(multiprocessing, 'Process', mock_process_exception)

        # Check that the jobs failed.
        result = parq.run(func, values, n_proc=n_proc)
        assert not result.success

        # Check that the exception was printed to stderr.
        captured = capsys.readouterr()
        assert 'Traceback ' in captured.err
        assert '    raise Exception()\n' in captured.err


def test_queue_full_exception(monkeypatch):
    """
    Test that parq.run() reports when jobs cannot be added to a full queue.
    """

    class MockQueue:
        def put(*args, **kwargs):
            raise queue.Full()

    def func(x):
        pass

    values = [(i,) for i in range(2)]
    n_proc = 10

    with monkeypatch.context() as m:
        m.setattr(multiprocessing, 'Queue', MockQueue)

        # Check that creating the job queue fails.
        expected_msg = r'^Cannot add job \d+ to the queue$'
        with pytest.raises(ValueError, match=expected_msg):
            parq.run(func, values, n_proc=n_proc)
