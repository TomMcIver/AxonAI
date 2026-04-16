"""Feature engineering from RDS tables."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Dataset:
    features: pd.DataFrame
    labels: pd.Series
