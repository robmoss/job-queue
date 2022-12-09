Release process
===============

Feature development takes places on the "master" branch.
Periodically, a release is created by increasing the version number and
tagging the relevant commit with the new version number.

* Check that the release passes all of the tests:

  .. code-block:: shell

     tox

* Update the version number according to the
  `versioning scheme <https://www.python.org/dev/peps/pep-0440/>`__.

   * Update the version number in ``doc/conf.py``.
     The full version must **always** be updated, the short (X.Y) version
     **does not** need to be updated if the version number is being increased
     from X.Y.Z to X.Y.Z+1.

   * Update the version number in ``pyproject.toml``.

* Check whether the copyright year(s) need to be updated in:

   * ``LICENSE``

   * ``doc/conf.py``

* Describe the changes at the top of ``NEWS.rst`` under a heading of the form
  ``X.Y.Z (YYYY-MM-DD)``, which identifies the new version number and the
  date on which this version was released.

* Commit these changes; set the commit message to ``Release parq X.Y.Z``.

  .. code-block:: shell

     git add NEWS.rst doc/conf.py pyproject.toml
     git commit -m "Release parq X.Y.Z"

* Tag this commit ``X.Y.Z``.

  .. code-block:: shell

     git tag -a X.Y.Z -m "parq X.Y.Z"

* Push this commit **and** the new tag upstream.

  .. code-block:: shell

     git push --follow-tags

Publishing to PyPI
------------------

These instructions are based on the
`Packaging Python Projects tutorial <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`__.

Ensure that ``build`` and ``twine`` are installed:

.. code-block:: shell

   pip install build twine

Ensure that all uncommitted changes are stashed, **or they will be packaged!**

.. code-block:: shell

   git stash

Build the wheel ``./dist/parq-X.Y.Z-py3-none-any.whl``:

.. code-block:: shell

   python3 -m build

Upload this wheel to the PyPI **test** server, so that any problems can be
`identified <https://testpypi.python.org/pypi/parq/>`__ and fixed:

.. code-block:: shell

   python3 -m twine upload -r testpypi dist/parq-X.Y.Z-py3-none-any.whl

Then upload this wheel to PyPI:

.. code-block:: shell

   python3 -m twine upload dist/parq-X.Y.Z-py3-none-any.whl
