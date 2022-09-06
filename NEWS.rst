0.2.0 (2022-09-06)
------------------

* Breaking change: require Python 3.7 or newer.

* Improve how unsuccessful jobs are handled.
  ``parq.run()`` now returns a ``Result`` instance that provides details about successful and unsuccessful jobs.

0.1.0 (2022-04-04)
------------------

* Initial release: extract the job queue from the ``epifx`` package.
