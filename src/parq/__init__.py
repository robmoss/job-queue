"""A multi-process job queue."""

import ctypes
import dataclasses
import logging
import multiprocessing
import multiprocessing.sharedctypes
import pickle
import queue
import signal
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional


@dataclasses.dataclass
class WorkerConfig:
    func: Callable[[Any], None]
    in_queue: multiprocessing.Queue
    out_queue: multiprocessing.Queue
    stop_workers: multiprocessing.sharedctypes.Synchronized
    log_level: int
    fail_early: bool = True
    trace: bool = True
    collect_results: bool = False


@dataclasses.dataclass
class Result:
    """
    The result of running a number of jobs.

    :param success: Whether all jobs completed successfully.
    :type success: bool
    :param job_count: The number of jobs that were submitted.
    :type job_count: int
    :param successful_jobs: A list that contains the arguments for each job
        that was completed successfully.
    :type successful_jobs: [Any]
    :param unsuccessful_jobs: A list that contains the arguments for each job
        that was not completed successfully.
    :type unsuccessful_jobs: [Any]
    :param failed_worker_count: The number of worker processes that terminated
        early.
    :type failed_worker_count: int
    :param job_results: An optional dictionary that maps successful job
       numbers to the returned results of those jobs. If results were not
       collected, this will be ``None``.
    :type job_results: Optional[Dict[int, Any]]

    Instances are considered true if ``success`` is true, otherwise they are
    considered false.

    >>> from parq import Result
    >>> res_good = Result(True, 0, [], [], 0)
    >>> assert res_good
    >>> res_bad = Result(False, 0, [], [], 0)
    >>> assert not res_bad
    """

    success: bool
    job_count: int
    successful_jobs: List[Any]
    unsuccessful_jobs: List[Any]
    failed_worker_count: int
    job_results: Optional[Dict[int, Any]] = None

    def __bool__(self):
        """
        Return ``True`` if all jobs completed successfully, otherwise return
        ``False``.
        """
        return self.success

    def num_successful(self):
        """Return the number of jobs that were completed successfully."""
        return len(self.successful_jobs)

    def num_unsuccessful(self):
        """Return the number of jobs that were not completed successfully."""
        return len(self.unsuccessful_jobs)


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
        except (pickle.PicklingError, TypeError, AttributeError):
            seq = try_iter(value)
            if seq is not None:
                for i in seq:
                    descend_into(value[i], path + [i])
            else:
                invalid_paths.append((path, value))

    descend_into(item, [])
    if invalid_paths:
        for (_path, value) in invalid_paths:
            msg = 'Invalid value: {}'.format(value)
            logger.error(msg)
        return True

    return False


def _worker(config):
    # Ignore the signal that raises KeyboardInterrupt exceptions; the main
    # loop will handle this exception and ensure each process terminates.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    status_ok = True
    logger = multiprocessing.log_to_stderr(config.log_level)
    counter = 0

    while True:
        if config.stop_workers.value:
            logger.debug('Worker stopping early')
            status_ok = False
            break
        try:
            job_num, args = config.in_queue.get(block=False)
            if job_num < 0:
                break
            counter += 1
            logger.debug(f'Worker received job #{job_num}: {args}')
            result = config.func(*args)
            logger.debug(f'Worker finished job #{job_num}')
            if config.collect_results:
                config.out_queue.put((job_num, result), block=True)
            else:
                config.out_queue.put(job_num, block=True)
            logger.debug(f'Worker recorded job #{job_num}')
        except queue.Empty:
            logger.debug('Queue is empty')
        except Exception:
            logger.debug('Worker caught an exception')
            if config.trace:
                logger.warning(traceback.format_exc())
            status_ok = False
            if config.fail_early:
                logger.debug('Will stop workers early')
                # NOTE: signal other worker processes to stop.
                with config.stop_workers.get_lock():
                    config.stop_workers.value = True
                break

    logger.debug('Worker sending sentinel')
    if config.collect_results:
        config.out_queue.put((-1, None), block=True)
    else:
        config.out_queue.put(-1, block=True)
    logger.info(f'Worker exiting, {counter} jobs, success = {status_ok}')
    if not status_ok:
        sys.exit(1)


def _build_job_queue(jobs):
    job_q = multiprocessing.Queue()
    job_table = {}

    job_num = 0
    for args in jobs:
        if fails_to_pickle(args):
            raise ValueError(f'Invalid arguments: {args}')
        try:
            job_q.put((job_num, args), block=False)
        except queue.Full as e:
            raise ValueError(f'Cannot add job {job_num} to the queue') from e
        job_table[job_num] = args
        job_num += 1

    return job_q, job_num, job_table


def _collect_successful_job_nums(workers, done_q, results, timeout):
    """
    Collect all of the successful job numbers.

    :param workers: The worker processes.
    :param done_q: The queue to which successful job numbers are written.
    :param results: Whether ``done_q`` includes job results.
    :param timeout: The optional timeout (in seconds) when polling for job
        results; set to ``None`` to block until a result is received.
    """
    logger = logging.getLogger(__name__)
    successful_job_nums = set()
    job_results = {} if results else None
    killed_workers = set()
    sentinels = 0
    # NOTE: to avoid deadlocking when one or more worker processes terminates
    # without first sending a sentinel, we need to monitor the processes and
    # record how many have terminated unexpectedly.
    #
    # This means we cannot block indefinitely when waiting for job results.
    # Instead, we must use a finite timeout so that we can monitor the worker
    # processes on a regular basis.
    #
    # We assume that processes with non-zero exit codes have terminated
    # unexpectedly, and that this occurred before the worker was able to send
    # its sentinel.
    while sentinels < (len(workers) - len(killed_workers)):
        # Detect worker process that have terminated unexpectedly.
        for worker in workers:
            ex = worker.exitcode
            if ex is not None and ex != 0:
                killed_workers.add(worker)
        # Retrieve as many successfully-completed jobs as possible.
        try:
            if results:
                (job_num, result) = done_q.get(block=True, timeout=timeout)
                if job_num >= 0:
                    job_results[job_num] = result
            else:
                job_num = done_q.get(block=True, timeout=timeout)
        except queue.Empty:
            continue
        if job_num < 0:
            sentinels += 1
            logger.debug(f'Received {sentinels} sentinel(s)')
        else:
            logger.debug(f'Received completed job #{job_num}')
            successful_job_nums.add(job_num)

    logger.debug(f'Received {len(successful_job_nums)} successful jobs')
    return (successful_job_nums, job_results)


def run(
    func,
    iterable,
    n_proc,
    fail_early=True,
    trace=True,
    level=None,
    results=False,
    timeout=10,
):
    """
    Perform multiple jobs in parallel by spawning multiple processes.

    :param func: The function that performs a single job.
    :param iterable: A sequence of job arguments, represented as tuples and
        *unpacked* before passing to ``func`` (i.e., ``func(*args)``).
    :param n_proc: The number of processes to spawn.
    :param fail_early: Whether to stop running jobs if one fails.
    :param trace: Whether to print stack traces for jobs that raise an
        exception.
    :param level: The logging level for worker processes. By default, only
        warnings and errors will be shown.
    :param results: Whether to return the results of each job.
    :param timeout: The optional timeout (in seconds) when polling for job
        results. Set this to ``None`` to block until a result is received.

    :returns: A :class:`Result` instance.
    :rtype: parq.Result

    .. warning::

       If a worker process is terminated unexpectedly (e.g., by running out
       of memory) this function **will deadlock** if ``timeout`` is ``None``.
    """
    # Note: we avoid using multiprocessing.Pool because it does not handle
    # KeyboardInterrupt exceptions correctly. For details, see:
    # http://bryceboe.com/2012/02/14/python-multiprocessing-pool-and-keyboardinterrupt-revisited/
    logger = logging.getLogger(__name__)
    if level is None:
        level = logging.WARNING
    job_q, n_jobs, job_table = _build_job_queue(iterable)
    done_q = multiprocessing.Queue()
    stop_workers = multiprocessing.Value(ctypes.c_bool, False)
    workers = []
    worker_config = WorkerConfig(
        func=func,
        in_queue=job_q,
        out_queue=done_q,
        stop_workers=stop_workers,
        log_level=level,
        fail_early=fail_early,
        trace=trace,
        collect_results=results,
    )
    successful_job_nums = set()
    job_results = None

    # Add a sentinel value for each worker to consume.
    for _ in range(n_proc):
        job_q.put((-1, None), block=False)

    try:
        # Start the worker processes.
        if n_proc > n_jobs:
            # Spawn no more processes than there are jobs
            n_proc = n_jobs
        logger.info('Spawning {} workers for {} jobs'.format(n_proc, n_jobs))
        for i in range(n_proc):
            proc = multiprocessing.Process(
                target=_worker, args=[worker_config], name=f'parq-{i + 1}'
            )
            workers.append(proc)
            proc.start()
        logger.debug('Started all workers')

        # Wait for each worker to finish. Without this loop, we jump straight
        # to the finally clause and the KeyboardInterrupt handler (below) is
        # never triggered.
        successful_job_nums, job_results = _collect_successful_job_nums(
            workers, done_q, results, timeout
        )

        logger.debug('Joined all workers')
    except KeyboardInterrupt:
        # Force each worker to terminate.
        logger.info('Received CTRL-C, terminating {} workers'.format(n_proc))
        for worker in workers:
            worker.terminate()
    except Exception:
        traceback.print_exc()
    finally:
        successful_jobs = [
            job_table[job_num] for job_num in successful_job_nums
        ]
        unsuccessful_jobs = [
            args
            for (job_num, args) in job_table.items()
            if job_num not in successful_job_nums
        ]
        n_done = len(successful_jobs)
        success = n_done == n_jobs

        # Wait for each worker to finish.
        failed_worker_count = 0
        for ix, worker in enumerate(workers):
            worker.join()
            # Note: worker.exitcode should be 0 if it completed successfully.
            # It will be -N if it was terminated by signal N.
            # It will apparently be 1 if an exception was raised.
            # all_good = all_good and worker.exitcode == 0
            if worker.exitcode != 0:
                msg = 'Worker {} exit code: {}'
                logger.info(msg.format(ix, worker.exitcode))
                failed_worker_count += 1

    return Result(
        success=success,
        job_count=n_jobs,
        successful_jobs=successful_jobs,
        unsuccessful_jobs=unsuccessful_jobs,
        failed_worker_count=failed_worker_count,
        job_results=job_results,
    )
