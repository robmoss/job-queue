import pytest
import parq


def test_invalid_args_exception():
    """
    Test that providing arguments that cannot be pickled raises a ValueError.
    """

    def func(*args):
        print(args)

    def cannot_pickle():
        """Can only pickle top-level functions."""
        pass

    n_proc = 2

    values = [(i, cannot_pickle) for i in range(4)]
    with pytest.raises(ValueError, match='Invalid arguments:'):
        parq.run(func, values, n_proc=n_proc)

    values = [({'function': cannot_pickle},) for i in range(4)]
    with pytest.raises(ValueError, match='Invalid arguments:'):
        parq.run(func, values, n_proc=n_proc)

    values = [({'x': {'y': {'z': cannot_pickle}}},) for i in range(4)]
    with pytest.raises(ValueError, match='Invalid arguments:'):
        parq.run(func, values, n_proc=n_proc)
