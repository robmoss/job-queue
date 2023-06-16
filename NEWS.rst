0.3.0 (2023-06-16)
------------------

* Add support for returning the result of each job.

* Avoid deadlock when worker processes are terminated unexpectedly.

* Set the default worker logging level to ``logging.WARNING``.

* Log job exceptions as warnings.

0.2.3 (2022-12-12)
------------------

* Avoid potential synchronisation issues when jobs are very quick to complete.

* Simplify how completed jobs are collected, avoiding a potential busy-loop.

* Log the number of jobs completed by each worker process.

0.2.2 (2022-12-09)
------------------

* Support extremely large numbers of jobs.

0.2.1 (2022-12-09)
------------------

* Breaking change: require Python 3.8 or newer.

* Provide control over worker process logging.

* Avoid potential deadlocks when job arguments are extremely large.

0.2.0 (2022-09-06)
------------------

* Breaking change: require Python 3.7 or newer.

* Improve how unsuccessful jobs are handled.
  ``parq.run()`` now returns a ``Result`` instance that provides details about successful and unsuccessful jobs.

0.1.0 (2022-04-04)
------------------

* Initial release: extract the job queue from the ``epifx`` package.
