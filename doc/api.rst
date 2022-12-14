API documentation
=================

.. module:: parq

This package provides a single function :func:`parq.run`, which runs jobs using multiple Python processes and returns a :class:`parq.Result` value when all jobs have completed.

.. note::

   By default, **the return value of each job is ignored**.
   To obtain the return value of each job, pass ``results=True`` to :func:`parq.run`.

.. warning::

   If you use :func:`parq.run` to run many jobs that each return a very large data structure, you should consider saving the results of each job to an external file, rather than passing ``results=True``.

.. autofunction:: parq.run

.. autoclass:: parq.Result
   :members:
