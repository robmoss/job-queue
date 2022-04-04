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

.. code-block:: python

   >>> import parq
   >>> # Define a job that prints its input argument.
   >>> def my_job(n):
   ...     print('Running job #{}'.format(n))
   ...
   >>> # Define the input argument for each job.
   >>> job_inputs = [(i,) for i in range(10)]
   >>> # Run these 10 jobs using 4 processes.
   >>> success = parq.run(my_job, job_inputs, n_proc=4)
   >>> assert success

Installation
------------

You must have Python 3.6, or later, installed.
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
