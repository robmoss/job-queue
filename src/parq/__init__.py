"""A multi-process job queue."""

import ctypes
import logging
import multiprocessing
import pickle
import queue
import signal
import sys
import traceback

from . import version

__package_name__ = 'parq'
__author__ = 'Rob Moss'
__email__ = 'rgmoss@unimelb.edu.au'
__copyright__ = '2016-2022, Rob Moss'
__license__ = 'BSD 3-Clause License'
__version__ = version.__version__


def fails_to_pickle(item):
    """
    Check whether an object can be serialised ("pickled"), as is required for
    simulation arguments when running simulations in parallel.

    See the ``pickle`` documentation for
    `Python 2 <https://docs.python.org/2/library/pickle.html>`__ or
    `Python 3 <https://docs.python.org/3/library/pickle.html>`__ for a list of
    types that can be pickled.
    """
    logger = logging.getLogger(__name__)

    def try_iter(value):
        if isinstance(value, dict):
            return value
        else:
            try:
                return range(len(value))
            except TypeError:
                return None

    invalid_paths = []

    def descend_into(value, path):
        try:
            pickle.dumps(value)
        except (pickle.PicklingError, TypeError):
            seq = try_iter(value)
            if seq is not None:
                for i in seq:
                    descend_into(value[i], path + [i])
            else:
                invalid_paths.append((path, value))

    descend_into(item, [])
    if invalid_paths:
        for (path, value) in invalid_paths:
            if path[0] == 2:
                path_str = "][".join(repr(p) for p in path[1:])
                msg = "Invalid value: extra[{}] = {}".format(path_str, value)
            else:
                msg = "Invalid value: {}".format(value)
            logger.error(msg)
        return True

    return False


def run(func, iterable, n_proc, fail_early=True, trace=True):
    """
    Perform multiple jobs in parallel by spawning multiple processes.

    :param func: The function that performs a single job.
    :param iterable: A sequence of job arguments, represented as tuples and
        *unpacked* before passing to ``func`` (i.e., ``func(*args)``).
    :param n_proc: The number of processes to spawn.
    :param fail_early: Whether to stop running jobs if one fails.
    :param trace: Whether to print stack traces for jobs that raise an
        exception.

    :returns: ``True`` if all jobs were successfully completed (i.e., each
        process terminated with an exit code of ``0``).
    """
    # Note: we avoid using multiprocessing.Pool because it does not handle
    # KeyboardInterrupt exceptions correctly. For details, see:
    # http://bryceboe.com/2012/02/14/python-multiprocessing-pool-and-keyboardinterrupt-revisited/
    logger = logging.getLogger(__name__)
    job_q = multiprocessing.Queue()
    stop_workers = multiprocessing.Value(ctypes.c_bool, False)
    workers = []

    def apply_func(job_q, stop_workers):
        # Ignore the signal that raises KeyboardInterrupt exceptions; the main
        # loop will handle this exception and ensure each process terminates.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        status_ok = True

        while not job_q.empty():
            if stop_workers.value:
                status_ok = False
                break
            try:
                args = job_q.get(block=False)
                func(*args)
            except queue.Empty:
                pass
            except Exception:
                if trace:
                    print(traceback.format_exc())
                status_ok = False
                if fail_early:
                    # NOTE: signal other worker processes to stop.
                    with stop_workers.get_lock():
                        stop_workers.value = True
                    break

        if not status_ok:
            sys.exit(1)

    n_job = 0
    for args in iterable:
        if fails_to_pickle(args):
            logger.error("Encountered invalid arguments, terminating")
            return
        n_job += 1
        try:
            job_q.put(args, block=False)
        except queue.Full:
            logger.error("Could not add job {} to the queue".format(n_job))
            return

    try:
        # Start the worker processes.
        if n_proc > n_job:
            # Spawn no more processes than there are jobs
            n_proc = n_job
        logger.info("Spawning {} workers for {} jobs".format(n_proc, n_job))
        for i in range(n_proc):
            proc = multiprocessing.Process(target=apply_func,
                                           args=[job_q, stop_workers])
            workers.append(proc)
            proc.start()
        # Wait for each worker to finish. Without this loop, we jump straight
        # to the finally clause and the KeyboardInterrupt handler (below) is
        # never triggered.
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        # Force each worker to terminate.
        logger.info("Received CTRL-C, terminating {} workers".format(n_proc))
        for worker in workers:
            worker.terminate()
    except Exception as e:
        print(e)
    finally:
        all_good = True
        # Wait for each worker to finish.
        for ix, worker in enumerate(workers):
            worker.join()
            # Note: worker.exitcode should be 0 if it completed successfully.
            # It will be -N if it was terminated by signal N.
            # It will apparently be 1 if an exception was raised.
            all_good = all_good and worker.exitcode == 0
            if worker.exitcode != 0:
                msg = "Worker {} exit code: {}"
                logger.info(msg.format(ix, worker.exitcode))
        return all_good
