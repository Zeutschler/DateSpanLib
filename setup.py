# -*- coding: utf-8 -*-
# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from setuptools import setup
from setuptools import find_packages
from datespan import VERSION


# ...to run the build and deploy process to pypi.org manually:
# 1. delete folder 'build'
# 1. empty folder 'dist'
# 2. python3 setup.py sdist bdist_wheel   # note: Wheel need to be installed: pip install wheel
# 3. twine upload -r  pypi dist/*         # note: Twine need to be installed: pip install twine
# ... via GitHub actions see
# https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/

DESCRIPTION = "datespan - effortless date span parsing and management"
LONG_DESCRIPTION = """
A Python package for effortless date span parsing and management. 
Aimed for data analysis and processing, useful in any context requiring date & time spans.
"""

setup(

    name="dataspan",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Topic :: Utilities",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",

        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
    ],
    author="Thomas Zeutschler",
    keywords=['python', 'datetime', 'timespan', 'pandas', 'numpy', 'spark', 'data analysis', 'sql', 'dataframe', 'data'],
    author_email="cubedpandas@gmail.com",
    url="https://github.com/Zeutschler/datespan",
    license='MIT',
    platforms=['any'],
    zip_safe=True,
    python_requires='>= 3.9',
    install_requires=[
        'python-dateutil',
    ],
    test_suite="datespan.tests",
    packages=['datespan', 'datespan.parser', 'tests'],
    project_urls={
        'Homepage': 'https://github.com/Zeutschler/datespan',
        'Documentation': 'https://github.com/Zeutschler/datespan',
        'GitHub': 'https://github.com/Zeutschler/datespan',
    },
)