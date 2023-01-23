import nox
from pathlib import Path
import shutil


@nox.session()
def build(session):
    """Build source and binary (wheel) packages."""
    build_dir = Path('build')
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.install('build')
    session.run('python', '-m', 'build', '-C--global-option=-q')


def _find_installed_pkg(session):
    """
    Return the directory where the package is installed.

    We need to use this directory to calculate test coverage, because test
    cases will spawn worker processes that import the installed package.
    """
    lib_dir = Path(f'{session.virtualenv.location}/lib')
    pkg_dirs = list(lib_dir.glob('python3.*/site-packages/parq'))
    if len(pkg_dirs) != 1:
        raise ValueError(f'Found {len(pkg_dirs)} package directories')
    return pkg_dirs[0]


@nox.session()
def tests(session):
    """Run test cases and record the test coverage."""
    session.install('pytest', 'pytest-cov')
    session.install('.')
    # Run the test cases and report the test coverage.
    src_dir = _find_installed_pkg(session)
    session.run(
        'python3', '-bb', Path(session.bin) / 'pytest',
        f'--cov={src_dir}',
        src_dir, './tests', './doc',
        *session.posargs,
        env={
            # NOTE: Do not import sphinx_rtd_theme in doc/conf.py.
            'READTHEDOCS': 'True',
        })


@nox.session()
def docs(session):
    """Build the HTML documentation."""
    session.install('-r', 'requirements-rtd.txt')
    session.run('sphinx-build', '-W', '-b', 'html',
                './doc', './doc/build/html')
