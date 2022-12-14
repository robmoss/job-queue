A multi-process job queue
=========================

|version| |docs| |tests| |coverage|

Description
-----------

This package implements a queue that distributes jobs over multiple processes.

License
-------

The code is distributed under the terms of the `BSD 3-Clause license <https://opensource.org/licenses/BSD-3-Clause>`_ (see
``LICENSE``), and the documentation is distributed under the terms of the
`Creative Commons BY-SA 4.0 license
<http://creativecommons.org/licenses/by-sa/4.0/>`_.

Usage
-----

.. code-block:: python

   import parq

   # Define a job that prints its input argument.
   def my_job(n):
       print(f'Running job #{n}')

   # Define the input argument for each job.
   job_inputs = [(i,) for i in range(10)]

   # Run these 10 jobs using 4 processes.
   success = parq.run(my_job, job_inputs, n_proc=4)
   assert success

See the `online documentation <https://parq.readthedocs.io/en/latest/>`_ for further details.

Installation
------------

To install the latest release::

    pip install parq

To install the latest development version, clone this repository and run::

    pip install .

.. |version| image:: https://badge.fury.io/py/parq.svg
   :alt: Latest version
   :target: https://pypi.org/project/parq/

.. |docs| image::  https://readthedocs.org/projects/parq/badge/
   :alt: Documentation
   :target: https://parq.readthedocs.io/

.. |tests| image:: https://gitlab.unimelb.edu.au/rgmoss/job-queue/badges/master/pipeline.svg
   :alt: Test cases
   :target: https://gitlab.unimelb.edu.au/rgmoss/job-queue

.. |coverage| image:: https://gitlab.unimelb.edu.au/rgmoss/job-queue/badges/master/coverage.svg
   :alt: Test coverage
   :target: https://gitlab.unimelb.edu.au/rgmoss/job-queue
