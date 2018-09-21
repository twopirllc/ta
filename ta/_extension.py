# -*- coding: utf-8 -*-
import math
import numpy as np
import pandas as pd

from pandas.core.base import PandasObject
from sys import float_info as sflt

TA_EPSILON = sflt.epsilon

def validate_positive(fn, x, minimum, default=None):
    return fn(x) if x and default and x > minimum else fn(default)

def signed_series(series:pd.Series, initial:int = None, length:int = None):
    """Returns a Signed Series with or without an initial value"""
    length = validate_positive(int, length, minimum=0, default=1)
    sign = series.diff(length)
    sign[sign > 0] = 1
    sign[sign < 0] = -1
    sign.iloc[0] = initial if initial else np.NaN
    return sign


class BasePandasObject(PandasObject):
    """Simple PandasObject Extension
    
    Ensures the DataFrame is not empty and has columns.

    Args:
        df (pd.DataFrame): Extends Pandas DataFrame 
    """
    def __init__(self, df, **kwargs):
        if df.empty:
            return None
        
        total_columns = len(df.columns)
        if total_columns > 0:
            self._df = df
        else:
            raise AttributeError(f"[X] No columns!")
    
    def __call__(self, kind, *args, **kwargs):
        raise NotImplementedError()


@pd.api.extensions.register_dataframe_accessor('ta')
class AnalysisIndicators(BasePandasObject):
    """AnalysisIndicators is class that extends a DataFrame.  The name extension is
    registered to all instances of the DataFrame wit the name of 'ta'.

    Args:
        kind(str): Name of the indicator.  Converts kind to lowercase.
        kwargs(dict): Method specific modifiers
    
    Returns:
        Either a Pandas Series or DataFrame of the results of the called indicator.

    Example A:  Loading Data and multiply ways of calling a function.
    # Load some data. If local, this would do.
    # Assum having a CSV with columns: date,open,high,low,close,volume
    df = pd.read_csv('AAPL.csv', index_col='date', parse_dates=True, dtype=float, infer_datetime_format=False, keep_date_col=True)

    # Calling HL2.  All equivalent.  Thy return a new Series/DataFrame with
    #  the Indicator result
    hl2 = df.ta.hl2()
    hl2 = df.ta.HL2()
    hl2 = df.ta(kind='hl2')

    #Given a TimeSeries DataFrame called df with lower case column names. ie. open, high, lose, close, volume

    Additional kwargs:
    * append: Default: False.  If True, appends the indicator result to the df.
    """

    def __call__(self, kind=None, **kwargs):
        try:
            indicator = getattr(self, kind.lower())
        except AttributeError:
            raise ValueError(f"kind='{kind.lower()}' is not valid for {self.__class__.__name__}")
        
        return indicator(**kwargs)


    ## Private Methods
    def _valid_df(self):
        """Validates and returns self._df   ** May be overkill."""
        try:
            df = self._df
        except AttributeError:
            print(f"[X] Not a valid DataFrame.")
            return
        else:
            return df

    # @property
    def defaults(self, value, min_range:int= 0, max_range:int = 100, every:int = 10):
        _levels = [x for x in range(min_range, max_range + 1) if x % every == 0]
        if value:
            for x in _levels:
                self._df[f'{x}'] = x
        else:
            for x in _levels:
                del self._df[f'{x}']



    ## Momentum Indicators
    def apo(self, close:str = None, fast:int = None, slow:int = None, **kwargs):
        """ apo """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return
        
        # Validate arguments
        fast = validate_positive(int, fast, minimum=0, default=12)
        slow = validate_positive(int, slow, minimum=0, default=26)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else fast

        # Calculate Result
        fastma = close.rolling(fast, min_periods=min_periods).mean()
        slowma = close.rolling(slow, min_periods=min_periods).mean()
        apo = fastma - slowma
        
        # Handle fills
        if 'fillna' in kwargs:
            apo.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            apo.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        # bop.name = f"BOP_{length}"
        apo.name = f"APO_{fast}_{slow}"
        apo.category = 'momentum'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[apo.name] = apo

        return apo


    def bop(self, open_:str = None, high:str = None, low:str = None, close:str = None, percentage:bool = False, **kwargs):
        """ bop """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(open_, pd.Series):
                open_ = open_
            else:
                open_ = df[open_] if open_ in df.columns else df.open

            if isinstance(high, pd.Series):
                high_ = high
            else:
                high_ = df[high] if high in df.columns else df.high

            if isinstance(low, pd.Series):
                low_ = low
            else:
                low_ = df[low] if low in df.columns else df.low

            if isinstance(close, pd.Series):
                close_ = close
            else:
                close_ = df[close] if close in df.columns else df.close
        else:
            return
        
        # Validate arguments
        # length = validate_positive(int, length, minimum=0, default=1)
        percent = 100 if percentage else 1

        # Calculate Result
        close_open_range = close_ - open_
        high_log_range = high_ - low_
        bop = percent * close_open_range / high_log_range
        
        # Handle fills
        if 'fillna' in kwargs:
            bop.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            bop.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        # bop.name = f"BOP_{length}"
        bop.name = f"BOP"
        bop.category = 'momentum'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[bop.name] = bop

        return bop


    def mom(self, close:str = None, length:int = None, **kwargs):
        """ mom """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.DataFrame) or isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return
        
        # Validate arguments
        length = validate_positive(int, length, minimum=0, default=1)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length

        # Calculate Result
        mom = close.diff(length)
        
        # Handle fills
        if 'fillna' in kwargs:
            mom.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            mom.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        mom.name = f"MOM_{length}"
        mom.category = 'momentum'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[mom.name] = mom

        return mom


    def ppo(self, close:str = None, fast:int = None, slow:int = None, **kwargs):
        """ ppo """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.DataFrame) or isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return
        
        # Validate arguments
        fast = validate_positive(int, fast, minimum=0, default=12)
        slow = validate_positive(int, slow, minimum=0, default=26)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else fast

        # Calculate Result
        fastma = close.rolling(fast, min_periods=min_periods).mean()
        slowma = close.rolling(slow, min_periods=min_periods).mean()
        ppo = 100 * (fastma - slowma) / slowma
        
        # Handle fills
        if 'fillna' in kwargs:
            ppo.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            ppo.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        ppo.name = f"PPO_{length}"
        ppo.category = 'momentum'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[ppo.name] = ppo

        return ppo


    def roc(self, close:str = None, length:int = None, **kwargs):
        """ roc """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.DataFrame) or isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return
        
        # Validate arguments
        length = validate_positive(int, length, minimum=0, default=1)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length

        # Calculate Result
        roc = 100 * self.mom(close=close, length=length) / close.shift(length)
        
        # Handle fills
        if 'fillna' in kwargs:
            roc.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            roc.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        roc.name = f"ROC_{length}"
        roc.category = 'momentum'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[roc.name] = roc

        return roc


    ## Overlap Indicators
    def hl2(self, high=None, low=None, offset=None, **kwargs):
        """Returns the average of two series.

        Args:
            high: None or a Series or DataFrame, optional
                If None, uses local df column: 'high'
            low: None or a Series or DataFrame, optional
                If None, uses local df column: 'low'
            append: bool, kwarg, optional
                If True, appends result to current df
        
            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high
            
            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low
        else:
            return

        # Validate Arguments
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        hl2 = 0.5 * (high + low)

        # Offset
        hl2.shift(offset)

        # Name & Category
        hl2.name = "HL2"
        hl2.category = 'overlap'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[hl2.name] = hl2
        
        return hl2


    def hlc3(self, high=None, low=None, close=None, offset=None, **kwargs):
        """Returns the average of three series.

        Args:
            high: None or a Series or DataFrame, optional
                If None, uses local df column: 'high'
            low: None or a Series or DataFrame, optional
                If None, uses local df column: 'low'
            close: None or a Series or DataFrame, optional
                If None, uses local df column: 'close'
            append: bool, kwarg, optional
                If True, appends result to current df
        
            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high
            
            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low

            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate Arguments
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        hlc3 = (high + low + close) / 3

        # Offset
        hlc3.shift(offset)

        # Name & Category
        hlc3.name = "HLC3"
        hlc3.category = 'overlap'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[hlc3.name] = hlc3
        
        return hlc3


    def ohlc4(self, open_=None, high=None, low=None, close=None, offset=None, **kwargs):
        """Calculates and returns the average of four series.

        Args:
            open_: None or a Series or DataFrame, optional
                If None, uses local df column: 'open'
            high: None or a Series or DataFrame, optional
                If None, uses local df column: 'high'
            low: None or a Series or DataFrame, optional
                If None, uses local df column: 'low'
            close: None or a Series or DataFrame, optional
                If None, uses local df column: 'close'
            append: bool, kwarg, optional
                If True, appends result to current df
        
            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(open_, pd.Series):
                open_ = open_
            else:
                open_ = df[open_] if open_ in df.columns else df.open

            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high
            
            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low

            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate Arguments
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        ohlc4 = 0.25 * (open_ + high + low + close)

        # Offset
        ohlc4.shift(offset)

        # Name & Category
        ohlc4.name = "OHLC4"
        ohlc4.category = 'overlap'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[ohlc4.name] = ohlc4
        
        return ohlc4


    def midpoint(self, close:str = None, length:int = None, offset=None, **kwargs):
        """Returns the Midpoint of a Series of a certain length.

        Args:
            close (None, str, pd.Series, optional):
                pd.Series: A seperate Series not in the current DataFrame.
                str: Looksup column in DataFrame under 'str' name.
                None: Default.  Uses current DataFrame column 'close'.
            length (int): Lookback length. Defaults to 1.

            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate arguments
        length = validate_positive(int, length, minimum=1, default=1)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        lowest = close.rolling(length, min_periods=min_periods).min()
        highest = close.rolling(length, min_periods=min_periods).max()
        midpoint = 0.5 * (lowest + highest)
        
        # Offset
        midpoint.shift(offset)

        # Handle fills
        if 'fillna' in kwargs:
            midpoint.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            midpoint.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        midpoint.name = f"MIDPOINT_{length}"
        midpoint.category = 'overlap'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[midpoint.name] = midpoint
            
        return midpoint


    def midprice(self, high:str = None, low:str = None, length:int = None, **kwargs):
        """ midprice """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low

            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high
        else:
            return

        # Validate arguments
        length = validate_positive(int, length, minimum=0, default=1)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length

        # Calculate Result
        lowest_low = low.rolling(length, min_periods=min_periods).min()
        highest_high = high.rolling(length, min_periods=min_periods).max()
        midprice = 0.5 * (lowest_low + highest_high)
        
        # Handle fills
        if 'fillna' in kwargs:
            midprice.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            midprice.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        midprice.name = f"MIDPRICE_{length}"
        midprice.category = 'overlap'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[midprice.name] = midprice
            
        return midprice


    def rpn(self, high=None, low=None, length=None, percentage=None, **kwargs):
        """Range Percentage
        
        Returns the Series of values that are a percentage of the absolute difference of two Series.

        Args:
            high: None or a Series or DataFrame, optional
                If None, uses local df column: 'high'
            low: None or a Series or DataFrame, optional
                If None, uses local df column: 'low'
            append: bool, kwarg, optional
                If True, appends result to current df
        
            **kwargs:
                addLow (bool, optional): If true, adds low value to result
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high
            
            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low
        else:
            return

        # Validate arguments
        length = validate_positive(int, length, minimum=0, default=1)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length
        percentage = validate_positive(float, percentage, minimum=0.0, default=0.1)

        # Calculate Result
        highest_high = high.rolling(length, min_periods=min_periods).max()
        lowest_low = low.rolling(length, min_periods=min_periods).min()
        abs_range = (highest_high - lowest_low).abs()

        rp = percentage * abs_range
        if 'addLow' in kwargs and kwargs['addLow']:
            rp += low

        # Name & Category
        rp.name = f"RP_{length}_{percentage}"
        rp.category = 'overlap'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[rp.name] = rp
        
        return rp


    ## Performance Indicators
    def log_return(self, close=None, length=None, cumulative:bool = False, percent:bool = False, offset:int = None, **kwargs):
        """Log Return with 
        
        Returns the Log Return of a Series.

        Args:
            close (None, pd.Series, optional):
                If None, uses local df column: 'high'
            length (None, int, optional):
                An integer of how periods to compute.  Default is None and one.
            cumulative (bool):
                Default: False.  If True, returns the cummulative returns
            offset (None, int, optional):
                An integer on how to shift the Series.  Default is None and zero.
        
            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate Arguments
        length = validate_positive(int, length, minimum=1, default=1)
        offset = offset if isinstance(offset, int) else 0
        percent = 100 if percent else 1

        # Calculate Result
        log_return = percent * np.log(close).diff(length)

        if cumulative:
            log_return = log_return.cumsum()

        # Offset
        log_return.shift(offset)

        # Name & Category
        log_return.name = f"LOGRET_{length}"
        log_return.category = 'performance'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[log_return.name] = log_return
        
        return log_return


    def percent_return(self, close=None, length=None, cumulative:bool = False, percent:bool = False, offset:int = None, **kwargs):
        """Percent Return with Length, Cumulation, Percentage and Offset Attributes
        
        Returns the Percent Change of a Series.

        Args:
            close (None, pd.Series, optional):
                If None, uses local df column: 'high'
            length (None, int, optional):
                An integer of how periods to compute.  Default is None and one.
            cumulative (bool):
                Default: False.  If True, returns the cummulative returns
            offset (None, int, optional):
                An integer on how to shift the Series.  Default is None and zero.
        
            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate Arguments
        length = validate_positive(int, length, minimum=1, default=1)
        offset = offset if isinstance(offset, int) else 0
        percent = 100 if percent else 1

        # Calculate Result
        pct_return = percent * close.pct_change(length)

        if cumulative:
            pct_return = percent * pct_return.cumsum()

        # Offset
        pct_return.shift(offset)

        # Name & Category
        pct_return.name = f"PCTRET_{length}"
        pct_return.category = 'performance'

        # If 'append', then add it to the df
        if 'append' in kwargs and kwargs['append']:
            df[pct_return.name] = pct_return
        
        return pct_return


    ## Statistics Indicators


    ## Trend Indicators
    def decreasing(self, close:str = None, length:int = None, asint:bool = True, offset=None, **kwargs):
        """Decreasing Trend
        
        Returns if a Series is Decreasing over a certain length.

        Args:
            close(None,pd.Series,pd.DataFrame): optional. If None, uses local df column: 'close'
            length(int): How many periods long.
            asint(bool): True.  Returns zeros and ones.

            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate Arguments
        length = validate_positive(int, length, minimum=1, default=1)
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        decreasing = close.diff(length) < 0
        if asint:
            decreasing = decreasing.astype(int)
        
        # Offset
        decreasing.shift(offset)

        # Handle fills
        if 'fillna' in kwargs:
            decreasing.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            decreasing.fillna(method=kwargs['fill_method'], inplace=True)
        
        # Name and Categorize it
        decreasing.name = f"DEC_{length}"
        decreasing.category = 'trend'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[decreasing.name] = decreasing

        return decreasing


    def increasing(self, close:str = None, length:int = None, asint:bool = True, offset=None, **kwargs):
        """Increasing Trend
        
        Returns if a Series is Increasing over a certain length.

        Args:
            close(None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'close'
            length(int): How many 
            asint(bool): True.  Returns zeros and ones.

            append(bool): kwarg, optional.  If True, appends result to current df

            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate arguments
        length = validate_positive(int, length, minimum=1, default=1)
        offset = offset if isinstance(offset, int) else 0

        # Calculate Result
        increasing = close.diff(length) > 0
        if asint:
            increasing = increasing.astype(int)
        
        # Offset
        increasing.shift(offset)

        # Handle fills
        if 'fillna' in kwargs:
            increasing.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            increasing.fillna(method=kwargs['fill_method'], inplace=True)
        
        # Name and Categorize it
        increasing.name = f"INC_{length}"
        increasing.category = 'trend'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[increasing.name] = increasing

        return increasing


    ## Volatility Indicators
    def donchian(self, close=None, length:int = None, **kwargs):
        """Donchian Channels


        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column.
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close
        else:
            return

        # Validate arguments
        length = validate_positive(int, length, minimum=0, default=20)
        min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else length

        # Calculate Result
        lower = close.rolling(length, min_periods=min_periods).min()
        upper = close.rolling(length, min_periods=min_periods).max()
        mid = 0.5 * (lower + upper)
    
        # Handle fills
        if 'fillna' in kwargs:
            lower.fillna(kwargs['fillna'], inplace=True)
            mid.fillna(kwargs['fillna'], inplace=True)
            upper.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            lower.fillna(method=kwargs['fill_method'], inplace=True)
            mid.fillna(method=kwargs['fill_method'], inplace=True)
            upper.fillna(method=kwargs['fill_method'], inplace=True)

        # Name and Categorize it
        lower.name = f"DCL_{length}"
        mid.name = f"DCM_{length}"
        upper.name = f"DCU_{length}"
        mid.category = upper.category = lower.category = 'volatility'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[lower.name] = lower
            df[mid.name] = mid
            df[upper.name] = upper

        # Prepare DataFrame to return
        data = {lower.name: lower, mid.name: mid, upper.name: upper}
        dcdf = pd.DataFrame(data)
        dcdf.name = f"DC{length}"
        dcdf.category = 'volatility'
            
        return dcdf


    ## Volume Indicators
    def ad(self, high=None, low=None, close=None, volume=None, open_=None, signed:bool = True, offset:int = None, **kwargs):
        """Accumulation/Distribution
        
        Returns a Series of the product of Price and Volume.

        Args:
            high (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'high'
            low (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'low'
            close (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'close'
            volume (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'volume'
            open_ (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'open_'
            signed (bool): True.  Returns zeros and ones.
            offset (int): How many 

            append(bool): kwarg, optional.  If True, appends result to current df

            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(high, pd.Series):
                high = high
            else:
                high = df[high] if high in df.columns else df.high

            if isinstance(low, pd.Series):
                low = low
            else:
                low = df[low] if low in df.columns else df.low

            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close

            if isinstance(volume, pd.Series):
                volume = volume
            else:
                volume = df[volume] if volume in df.columns else df.volume

            if open_ is not None:
                if isinstance(open_, pd.Series):
                    open_ = open_
                else:
                    open_ = df[open_] if open_ in df.columns else df.open
            
                # AD with Open
                ad - close - open_
            else:
                # AD with High, Low, Close
                ad = 2 * close - high - low
        else:
            return

        # Validate arguments
        offset = offset if isinstance(offset, int) else 0
        # min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else offset

        print(f"offset: {offset}")
        # Calculate Result
        hl_range = high - low
        ad *= volume / hl_range
        ad = ad.cumsum()

        # Offset
        ad.shift(offset)

        # Handle fills
        if 'fillna' in kwargs:
            ad.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            ad.fillna(method=kwargs['fill_method'], inplace=True)
        
        # Name and Categorize it
        ad.name = f"AD"
        ad.category = 'volume'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[ad.name] = ad

        return ad


    def pvol(self, close:str = None, volume:str = None, signed:bool = True, offset:int = None, **kwargs):
        """Price Volume
        
        Returns a Series of the product of Price and Volume.

        Args:
            close (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'close'
            volume (None,pd.Series,pd.DataFrame): optional.  If None, uses local df column: 'volume'
            signed (bool): True.  Returns zeros and ones.
            offset (int): How many 

            append(bool): kwarg, optional.  If True, appends result to current df

            **kwargs:
                fillna (value, optional): pd.DataFrame.fillna(value)
                fill_method (value, optional): Type of fill method
                append (bool, optional): If True, appends result to current df.
        
        Returns:
            pd.Series: New feature
        """
        df = self._valid_df()

        if df is not None:
            # Get the correct column(s).
            if isinstance(close, pd.Series):
                close = close
            else:
                close = df[close] if close in df.columns else df.close

            if isinstance(volume, pd.Series):
                volume = volume
            else:
                volume = df[volume] if volume in df.columns else df.volume
        else:
            return

        # Validate arguments
        offset = offset if isinstance(offset, int) else 0
        # min_periods = validate_positive(int, kwargs['minperiods']) if 'minperiods' in kwargs else offset

        print(f"offset: {offset}")
        # Calculate Result
        if signed:
            pvol = signed_series(close, 1) * close * volume
        else:
            pvol = close * volume

        # Offset
        pvol.shift(offset)

        # Handle fills
        if 'fillna' in kwargs:
            pvol.fillna(kwargs['fillna'], inplace=True)
        elif 'fill_method' in kwargs:
            pvol.fillna(method=kwargs['fill_method'], inplace=True)
        
        # Name and Categorize it
        pvol.name = f"PVOL"
        pvol.category = 'volume'
        
        # If append, then add it to the df 
        if 'append' in kwargs and kwargs['append']:
            df[pvol.name] = pvol

        return pvol


    ## Indicator Aliases & Categories
    # Momentum
    AbsolutePriceOscillator = apo
    BalanceOfPower = bop
    Momentum = mom
    PricePointOscillator = ppo ##
    RateOfChange = roc

    # Overlap
    HL2 = hl2
    HLC3 = hlc3
    OHLC4 = ohlc4
    Median = median
    Midpoint = midpoint
    Midprice = midprice
    RangePercentage = rpn

    # Performance
    PctReturn = percent_return
    LogReturn = log_return

    # Statistics

    # Trend
    Decreasing = decreasing
    Increasing = increasing

    # Volatility
    Donchian = donchian
    
    # Volume
    AccumDist = ad
    PriceVolume = pvol


ta_indicators = list((x for x in dir(pd.DataFrame().ta) if not x.startswith('_') and not x.endswith('_')))
if False:
    print(f"[i] Loaded {len(ta_indicators)} TA Indicators: {', '.join(ta_indicators)}")