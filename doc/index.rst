A multi-process job queue
=========================

Welcome to the parq_ documentation.
This package implements a queue that distributes jobs over multiple processes.

License
-------

The code is distributed under the terms of the BSD 3-Clause license (see
``LICENSE``), and the documentation is distributed under the terms of the
`Creative Commons BY-SA 4.0 license
<http://creativecommons.org/licenses/by-sa/4.0/>`_.

A simple example
----------------

This package provides a single function :func:`parq.run`, which runs jobs using multiple Python processes and returns a :class:`parq.Result` value when all jobs have completed.

.. code-block:: python

   >>> import parq
   >>> # Define a job that prints its input argument.
   >>> def my_job(n):
   ...     print(f'Running job #{n}')
   ...
   >>> # Define the input argument for each job.
   >>> job_inputs = [(i,) for i in range(10)]
   >>> # Run these 10 jobs using 4 processes.
   >>> success = parq.run(my_job, job_inputs, n_proc=4)
   >>> assert success

Job return values
-----------------

By default, **the return value of each job is ignored**.
You can instruct :func:`parq.run` to record the return value of each job by passing ``results=True``.
The ``job_results`` field will then contain a dictionary that maps job numbers (0, 1, 2, ...) to return values.

.. code-block:: python

   >>> import parq
   >>> # Define a job that doubles its input argument.
   >>> def double_input(x):
   ...     return 2 * x
   ...
   >>> # Define the input argument for each job.
   >>> job_inputs = [(i,) for i in range(10)]
   >>> # Run these 10 jobs using 4 processes.
   >>> result = parq.run(double_input, job_inputs, n_proc=4, results=True)
   >>> # Check that we obtained the expected results.
   >>> assert result.job_results == {i: 2 * i for i in range(10)}

.. warning::

   If you use :func:`parq.run` to run jobs that return very large data structures, you should consider saving the results of each job to an external file, rather than passing ``results=True``.

Installation
------------

You must have Python 3.8, or later, installed.
On Windows, the simplest option is to use `Anaconda <https://docs.continuum.io/anaconda/>`__.
You can install parq_ with ``pip``.
This is best done in a `virtual environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`__.

To install the parq package:
   .. code-block:: shell

      pip install parq

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   Home <self>
   api
   changelog
   contributing
   release-process
