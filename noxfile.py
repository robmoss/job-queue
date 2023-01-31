import nox
from pathlib import Path
import shutil


# Ensure that nox supports session tags.
nox.needs_version = ">=2022.8.7"


@nox.session()
def build(session):
    """Build source and binary (wheel) packages."""
    build_dir = Path('build')
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.install('build')
    session.run('python', '-m', 'build', '-C--global-option=-q')


@nox.session()
def tests(session):
    """Run test cases and record the test coverage."""
    session.install('.[tests]')
    # Run the test cases and report the test coverage.
    package = 'parq'
    session.run(
        'python3', '-bb', Path(session.bin) / 'pytest',
        f'--cov={package}',
        '--pyargs', package, './tests', './doc',
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


@nox.session(tags=['check'])
def ruff(session):
    """Run code linters."""
    session.install('ruff')
    session.run('ruff', 'src', 'tests')


@nox.session(tags=['check'])
def blue(session):
    """Check code formatting."""
    session.install('blue')
    session.run('blue', '--check', '--diff', '--color', 'src', 'tests')
