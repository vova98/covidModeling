import io
from setuptools import setup, find_packages

from covidlib import __version__

def read(file_path):
    with io.open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


readme = read('README.rst')
requirements = read('requirements.txt')


setup(
    # metadata
    name='covidlib',
    version=__version__,
    license='MIT',
    author="",
    author_email="",
    description="",
    long_description=readme,

    # options
    packages=find_packages(),
    python_requires='==3.*',
    install_requires=requirements,
)