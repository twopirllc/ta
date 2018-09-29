# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from .utils import verify_series


def kurtosis(close:pd.Series, length=None, offset=None, **kwargs):
    """Kurtosis over periods of a Pandas Series
    
    Use help(df.ta.kurtosis) for specific documentation where 'df' represents
    the DataFrame you are using.
    """
    # Validate Arguments
    close = verify_series(close)
    length = int(length) if length and length > 0 else 30
    min_periods = int(kwargs['min_periods']) if 'min_periods' in kwargs and kwargs['min_periods'] is not None else length
    offset = offset if isinstance(offset, int) else 0

    # Calculate Result
    kurtosis = close.rolling(length, min_periods=min_periods).kurt()

    # Offset
    kurtosis = kurtosis.shift(offset)

    # Name & Category
    kurtosis.name = f"KURT_{length}"
    kurtosis.category = 'statistics'

    # If 'append', then add it to the df
    if 'append' in kwargs and kwargs['append']:
        df[kurtosis.name] = kurtosis

    return kurtosis