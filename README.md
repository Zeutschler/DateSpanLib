# datespan

![GitHub license](https://img.shields.io/github/license/Zeutschler/datespan?color=A1C547)
![PyPI version](https://img.shields.io/pypi/v/datespan?logo=pypi&logoColor=979DA4&color=A1C547)
![PyPI Downloads](https://img.shields.io/pypi/dm/datespan.svg?logo=pypi&logoColor=979DA4&label=PyPI%20downloads&color=A1C547)
![GitHub last commit](https://img.shields.io/github/last-commit/Zeutschler/datespan?logo=github&logoColor=979DA4&color=A1C547)
![unit tests](https://img.shields.io/github/actions/workflow/status/zeutschler/datespan/python-package.yml?logo=GitHub&logoColor=979DA4&label=unit%20tests&color=A1C547)
![build](https://img.shields.io/github/actions/workflow/status/zeutschler/datespan/python-package.yml?logo=GitHub&logoColor=979DA4&color=A1C547)


-----------------
A Python package for effortless date span parsing and management. 
Aimed for data analysis and processing, useful in any context requiring date & time spans.   

```bash
pip install datespan
```

```python
import pandas as pd
from datespan import parse, DateSpan
df = pd.DataFrame({"date": pd.date_range("2024-01-01", "2024-12-31")})

dss = parse("April 2024 ytd") # Create a DateSpanSet, same as 'DateSpanSet("April 2024 ytd")'
dss.add("May")                # Add full month May of the current year
dss.add("today")              # Add the current day from 00:00 to 23:59:59
dss += "previous week"        # Add a full week from Monday 00:00 to Sunday 23:59:59
dss -= "January"              # Remove full month January of the current year

print(len(dss))               # returns the number of contained nonconsecutive DateSpans
print(dss.to_tuples())        # returns a list of (start, end) tuples representing the DateSpanSet
print(dss.to_sql("date"))     # returns an SQL WHERE clause fragment
print(dss.filter(df, "date")) # returns a DataFrame filtered by the DateSpanSet on column 'date'
```

### Classes
`DateSpan` represents a single date or time span, defined by a start and an end datetime. 
Provides methods to create, compare, merge, parse, split, shift, expand & intersect 
`DateSpan` objects and /or `datetime`, `date`or `time` objects.

`DateSpanSet` represents an ordered and redundancy free collection of `DateSpan` objects, 
where consecutive or overlapping `DateSpan` objects get automatically merged into a single `DateSpan` 
object. Required for fragmented date span expressions like `every 2nd Friday of next month`. 

`DateSpanParser` provides parsing  for arbitrary date, time and date span strings in english language,
ranging from simple dates like '2021-01-01' up to complex date span expressions like 
'Mondays to Wednesday last month'. For internal DateTime parsing and manipulation, the 
[DateUtil]() library is used. 

### Part of the CubedPandas Project
The 'dataspan' package has been carved out from the 
[CubedPandas](https://github.com/Zeutschler/cubedpandas) project, a library for 
easy, fast & fun data analysis with Pandas dataframes, as DataSpan serves a broader 
scope and purpose and can be used independently of CubedPandas. 

### Bugs, Issues, Feature Requests
Please report any bugs, issues, feature requests, questions or feedback on the
[GitHub Issues](https://github.com/Zeutschler/datespan/issues) page. It will
be highly appreciated and will help to improve the package.

### Documentation
Documentation will be available from 0.3.0 release on. 