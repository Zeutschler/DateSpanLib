# DateSpanLib
![GitHub license](https://img.shields.io/github/license/Zeutschler/datespanlib?color=A1C547)
![PyPI version](https://img.shields.io/pypi/v/datespanlib?logo=pypi&logoColor=979DA4&color=A1C547)
![Python versions](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FZeutschler%2Fdatespanlib%2Fmaster%2Fpyproject.toml&query=%24%5B'project'%5D%5B'requires-python'%5D&color=A1C547)
![PyPI Downloads](https://img.shields.io/pypi/dm/datespanlib.svg?logo=pypi&logoColor=979DA4&label=PyPI%20downloads&color=A1C547)
![GitHub last commit](https://img.shields.io/github/last-commit/Zeutschler/datespanlib?logo=github&logoColor=979DA4&color=A1C547)
![unit tests](https://img.shields.io/github/actions/workflow/status/zeutschler/datespanlib/python-package.yml?logo=GitHub&logoColor=979DA4&label=unit%20tests&color=A1C547)
![build](https://img.shields.io/github/actions/workflow/status/zeutschler/datespanlib/python-package.yml?logo=GitHub&logoColor=979DA4&color=A1C547)
![documentation](https://img.shields.io/github/actions/workflow/status/zeutschler/datespanlib/static-site-upload.yml?logo=GitHub&logoColor=979DA4&label=docs&color=A1C547&link=https%3A%2F%2Fzeutschler.github.io%2Fcubedpandas%2F)
![codecov](https://codecov.io/github/Zeutschler/datespanlib/graph/badge.svg?token=B12O0B6F10)

**UNDER CONSTRUCTION** - The DateSpanLib library is under active development and in a pre-alpha state, not 
suitable for production use and even testing. The library is expected to be released in a first alpha version
in the next weeks.

-----------------
A Python library for handling and using data and time spans. 

```python
from datespanlib import DateSpan

ds = DateSpan("January to March 2024")
print("2024-04-15" in ds + "1 month")  # returns True  
```

The DateSpanLib library is designed to be used for data analysis and data processing, 
where date and time spans are often used to filter, aggregate or join data. But it 
should also be valuable in any other context where date and time spans are used.

It provides dependency free integrations with Pandas, Numpy, Spark and others, can 
generate Python code artefacts, either as source text or as precompiled (lambda) 
functions and can also generate SQL fragments for filtering in SQL WHERE clauses.

#### Background
The DataSpanLib library has been carved out from the 
[CubedPandas](https://github.com/Zeutschler/cubedpandas) project - a library for 
intuitive data analysis with Pandas dataframes - as it serves a broader purpose and 
can be used independently of CubedPandas. 

For internal DateTime parsing and manipulation, 
the great [dateutil](https://github.com/dateutil/dateutil) library is used. The
DataSpanLib library has no other dependencies (like Pandas, Numpy Spark etc.), 
so it is lightweight and easy to install.

## Installation
The library can be installed via pip or is available as a download on [PyPi.org](https://pypi.org/datespanlib/).
```bash
pip install datespanlib
```

## Usage

The library provides the following methods and classes:

### Method parse() 
The `parse` method converts an arbitrary string into a `DateSpanSet` object. The string can be a simple date
like '2021-01-01' or a complex date span expression like 'Mondays to Wednesday last month'.

### Class DateSpan
`DateSpan` objects represent a single span of time, typically represented by a `start` and `end` datetime.
The `DateSpan` object provides methods to compare, merge, split, shift, expand, intersect etc. with other
`DateSpan` or Python datetime objects.

`DateSpan` objects are 'expansive' in the sense that they resolve the widest possible time span
for the 
, e.g. if a `DateSpan` object is created with a start date of '2021-01-01' and an end date of '2021-01-31',  




###  DateSpanSet - represents an ordered set of DateSpan objects
`DateSpanSet` is an ordered and redundancy free collection of `DateSpan` objects. If e.g. two `DateSpan` 
objects in the set would overlap or are contiguous, they are merged into one `DateSpan` object. Aside 
set related operations the `DateSpanSet` comes with two special capabilities worth mentioning:

* A build in **interpreter for arbitrary date, time and date span strings**, ranging from simple dates
  like '2021-01-01' up to complex date span expressions like 'Mondays to Wednesday last month'.

* Provides methods and can create **artefacts and callables for data processing** with Python, SQL, Pandas
  Numpy, Spark and other compatible libraries.




## Basic Usage
```python
from datespanlib import parse, DateSpanSet, DateSpan

# Create a DateSpan object
jan = DateSpan(start='2024-01-01', end='2024-01-31')
feb = DateSpan("February 2024")

jan_feb = DateSpanSet([jan, feb]) # Create a DateSpanSet object
assert(len(jan_feb) == 1)  # returns 1, as the consecutive or overlapping DateSpan objects get merged.

assert (jan_feb == parse("January, February 2024")) # Compare DateSpan objects

# Set operations
jan_feb_mar = jan_feb + "1 month"
assert(jan_feb_mar == parse("first 3 month of 2024"))
jan_mar = jan_feb_mar - "Januray 2024"   
assert(len(jan_mar))  # returns 2, as the one DateSpans gets split into two DataSpans.
assert(jan_mar.contains("2024-01-15"))  

# Use DateSpanSet to filter Pandas DataFrame
import pandas as pd
df = pd.DataFrame({"date": pd.date_range("2024-01-01", "2024-12-31")})
result = df[df["date"].apply(jan_mar.contains)]  # don't use this, slow
result = jan_mar.filter(df, "date")  # fast vectorized operation

# Use DateSpanSet to filter Spark DataFrame
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.createDataFrame(pd.DataFrame({"date": pd.date_range("2024-01-01", "2024-12-31")}))
result = jan_mar.filter(df, "date")  # fast vectorized/distributed operation

# Use DateSpanSet to filter Numpy array
import numpy as np
arr = np.arange(np.datetime64("2024-01-01"), np.datetime64("2024-12-31"))
result = jan_mar.filter(arr)  # fast vectorized operation

# Use DateSpanSet to create an SQL WHERE statement
sql = f"SELECT * FROM table WHERE {jan_mar.to_sql('date')}"
```









