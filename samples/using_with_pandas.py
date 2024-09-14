from datetime import datetime
import pandas as pd
from datespanlib import DateSpanSet, DateSpan, parse

df = pd.DataFrame.from_dict({
    "product": ["A", "B", "C", "A", "B", "C"],
    "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
             datetime(2024, 7, 1), datetime(2024, 7, 2),
             datetime(2024, 12, 1), datetime(2023, 12, 2)],
    "sales": [100, 150, 300, 200, 250, 350]
})

# create a DateSpanSet
spans = DateSpanSet("June")
print(spans)

# filer the DataFrame using the DateSpanSet
filtered_df = spans.filter(df["date"], return_mask=False)
print(filtered_df)





