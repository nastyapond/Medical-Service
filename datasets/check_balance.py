import pandas as pd
df = pd.read_csv("dataset.csv")
print(df["urgency"].value_counts(normalize=True))
print(df["request_type"].value_counts(normalize=True))