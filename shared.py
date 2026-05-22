from pathlib import Path
from collections import defaultdict
import polars as pl

app_dir = Path(__file__).parent
expenses = pl.read_csv(app_dir / 'data//data_download.csv')

years = expenses.select("Year").to_series().unique().to_list()

# unique combinations
pairs = expenses.select(["Object_cat", "Object"]).unique()

# build nested dict: {Object_cat: {Object: Object}}
grouped = defaultdict(dict)
for cat, obj in zip(pairs["Object_cat"].to_list(), pairs["Object"].to_list()):
    grouped[cat][obj] = obj
