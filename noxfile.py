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


@nox.session()
def tests(session):
    """Run test cases and record the test coverage."""
    session.install('pytest', 'pytest-cov')
    session.install('.')
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
