# -*- coding: utf-8 -*-
# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license
# setup.py for cubedpandas

from setuptools import setup
from setuptools import find_packages
from datespan import VERSION as DATESPANLIB_VERSION


# ...to run the build and deploy process to pypi.org manually:
# 1. delete folder 'build'
# 1. empty folder 'dist'
# 2. python3 setup.py sdist bdist_wheel   # note: Wheel need to be installed: pip install wheel
# 3. twine upload -r  pypi dist/*         # note: Twine need to be installed: pip install twine

# ... via Github actions
# https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/

VERSION = DATESPANLIB_VERSION
DESCRIPTION = "DateSpan - A date and time span parsing and utilization library for data analysis and processing"
LONG_DESCRIPTION = """
A Python library for handling and using data and time spans. 

```python
from datespan import DateSpan

ds = DateSpan("January to March 2024")
print("2024-04-15" in ds + "1 month")  # returns True  
```

The DateSpanLib library is designed to be used for data analysis and data processing, 
where date and time spans are often used to filter, aggregate or join data. But it 
should also be valuable in any other context where date and time spans are used.

It provides dependency free integrations with Pandas, Numpy, Spark and others, can 
generate Python code artefacts, either as source text or as precompiled (lambda) 
functions and can also generate SQL fragments for filtering in SQL WHERE clauses.
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
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",

        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
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
    python_requires='>= 3.10',
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