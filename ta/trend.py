# -*- coding: utf-8 -*-
"""
.. module:: trend
   :synopsis: Trend Indicators.

.. moduleauthor:: Dario Lopez Padial (Bukosabino)

"""
import numpy as np
import pandas as pd

from .overlap import ema, midprice, rma
from .utils import get_drift, get_offset, verify_series, zero
from .momentum import roc
from .volatility import atr, true_range



def adx(high, low, close, length=None, drift=None, offset=None, **kwargs):
    """Indicator: ADX"""
    # Validate Arguments
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    length = length if length and length > 0 else 14
    drift = get_drift(drift)
    offset = get_offset(offset)

    # Calculate Result
    _atr = atr(high=high, low=low, close=close, length=length)

    up = high - high.shift(drift)
    dn = low.shift(drift) - low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    pos = pos.apply(zero)
    neg = neg.apply(zero)

    dmp = (100 / _atr) * rma(close=pos, length=length)
    dmn = (100 / _atr) * rma(close=neg, length=length)

    dx = 100 * (dmp - dmn).abs() / (dmp + dmn)
    adx = rma(close=dx, length=length)

    # Offset
    if offset != 0:
        dmp = dmp.shift(offset)
        dmn = dmn.shift(offset)
        adx = adx.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        adx.fillna(kwargs['fillna'], inplace=True)
        dmp.fillna(kwargs['fillna'], inplace=True)
        dmn.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        adx.fillna(method=kwargs['fill_method'], inplace=True)
        dmp.fillna(method=kwargs['fill_method'], inplace=True)
        dmn.fillna(method=kwargs['fill_method'], inplace=True)

    # Name and Categorize it
    adx.name = f"ADX_{length}"
    dmp.name = f"DMP_{length}"
    dmn.name = f"DMN_{length}"

    adx.category = dmp.category = dmn.category = 'trend'

    # Prepare DataFrame to return
    data = {adx.name: adx, dmp.name: dmp, dmn.name: dmn}
    adxdf = pd.DataFrame(data)
    adxdf.name = f"ADX_{length}"
    adxdf.category = 'trend'

    return adxdf


def aroon(close, length=None, offset=None, **kwargs):
    """Indicator: Aroon Oscillator"""
    # Validate Arguments
    close = verify_series(close)
    length = length if length and length > 0 else 14
    min_periods = int(kwargs['min_periods']) if 'min_periods' in kwargs and kwargs['min_periods'] is not None else length
    offset = get_offset(offset)

    # Calculate Result
    def maxidx(x):
        return 100 * (int(np.argmax(x)) + 1) / length

    def minidx(x):
        return 100 * (int(np.argmin(x)) + 1) / length

    _close = close.rolling(length, min_periods=min_periods)
    aroon_up = _close.apply(maxidx, raw=True)
    aroon_down = _close.apply(minidx, raw=True)

    # Handle fills
    if 'fillna' in kwargs:
        aroon_up.fillna(kwargs['fillna'], inplace=True)
        aroon_down.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        aroon_up.fillna(method=kwargs['fill_method'], inplace=True)
        aroon_down.fillna(method=kwargs['fill_method'], inplace=True)

    # Offset
    if offset != 0:
        aroon_up = aroon_up.shift(offset)
        aroon_down = aroon_down.shift(offset)

    # Name and Categorize it
    aroon_up.name = f"AROONU_{length}"
    aroon_down.name = f"AROOND_{length}"

    aroon_down.category = aroon_up.category = 'trend'

    # Prepare DataFrame to return
    data = {aroon_up.name: aroon_up, aroon_down.name: aroon_down}
    aroondf = pd.DataFrame(data)
    aroondf.name = f"AROON_{length}"
    aroondf.category = 'trend'

    return aroondf


def decreasing(close, length=None, asint=True, offset=None, **kwargs):
    """Indicator: Decreasing"""
    # Validate Arguments
    close = verify_series(close)
    length = int(length) if length and length > 0 else 1
    offset = get_offset(offset)

    # Calculate Result
    decreasing = close.diff(length) < 0
    if asint:
        decreasing = decreasing.astype(int)

    # Offset
    if offset != 0:
        decreasing = decreasing.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        decreasing.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        decreasing.fillna(method=kwargs['fill_method'], inplace=True)

    # Name and Categorize it
    decreasing.name = f"DEC_{length}"
    decreasing.category = 'trend'

    return decreasing


def dpo(close, length=None, centered=True, offset=None, **kwargs):
    """Indicator: Detrend Price Oscillator (DPO)"""
    # Validate Arguments
    close = verify_series(close)
    length = int(length) if length and length > 0 else 1
    min_periods = int(kwargs['min_periods']) if 'min_periods' in kwargs and kwargs['min_periods'] is not None else length
    offset = get_offset(offset)

    # Calculate Result
    drift = int(0.5 * length) + 1  # int((0.5 * length) + 1)
    dpo = close.shift(drift) - close.rolling(length, min_periods=min_periods).mean()
    # dpo = close.shift(drift) - close.rolling(length).mean()
    if centered:
        dpo = dpo.shift(-drift)

    # Offset
    if offset != 0:
        dpo = dpo.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        dpo.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        dpo.fillna(method=kwargs['fill_method'], inplace=True)

    # Name and Categorize it
    dpo.name = f"DPO_{length}"
    dpo.category = 'trend'

    return dpo


def increasing(close, length=None, asint=True, offset=None, **kwargs):
    """Indicator: Increasing"""
    # Validate Arguments
    close = verify_series(close)
    length = int(length) if length and length > 0 else 1
    offset = get_offset(offset)

    # Calculate Result
    increasing = close.diff(length) > 0
    if asint:
        increasing = increasing.astype(int)

    # Offset
    if offset != 0:
        increasing = increasing.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        increasing.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        increasing.fillna(method=kwargs['fill_method'], inplace=True)

    # Name and Categorize it
    increasing.name = f"INC_{length}"
    increasing.category = 'trend'

    return increasing


def vortex(high, low, close, length=None, drift=None, offset=None, **kwargs):
    """Indicator: Vortex"""
    # Validate arguments
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    length = length if length and length > 0 else 14
    min_periods = int(kwargs['min_periods']) if 'min_periods' in kwargs and kwargs['min_periods'] is not None else length
    drift = get_drift(drift)
    offset = get_offset(offset)

    # Calculate Result
    tr = true_range(high=high, low=low, close=close)
    tr_sum = tr.rolling(length, min_periods=min_periods).sum()

    vmp = (high - low.shift(drift)).abs()
    vmm = (low - high.shift(drift)).abs()

    vip = vmp.rolling(length, min_periods=min_periods).sum() / tr_sum
    vim = vmm.rolling(length, min_periods=min_periods).sum() / tr_sum

    # Offset
    if offset != 0:
        vip = vip.shift(offset)
        vim = vim.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        vip.fillna(kwargs['fillna'], inplace=True)
        vim.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        vip.fillna(method=kwargs['fill_method'], inplace=True)
        vim.fillna(method=kwargs['fill_method'], inplace=True)

    # Name and Categorize it
    vip.name = f"VTXP_{length}"
    vim.name = f"VTXM_{length}"
    vip.category = vim.category = 'trend'

    # Prepare DataFrame to return
    data = {vip.name: vip, vim.name: vim}
    vtxdf = pd.DataFrame(data)
    vtxdf.name = f"VTX_{length}"
    vtxdf.category = 'trend'

    return vtxdf



# Trend Documentation
adx.__doc__ = \
"""Average Directional Movement (ADX)

Average Directional Movement is meant to quantify trend strength by measuring
the amount of movement in a single direction.

Sources:
    https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/average-directional-movement-adx/

Calculation:
    DMI ADX TREND 2.0 by @TraderR0BERT, NETWORTHIE.COM
        //Created by @TraderR0BERT, NETWORTHIE.COM, last updated 01/26/2016
        //DMI Indicator
        //Resolution input option for higher/lower time frames
        study(title="DMI ADX TREND 2.0", shorttitle="ADX TREND 2.0")

        adxlen = input(14, title="ADX Smoothing")
        dilen = input(14, title="DI Length")
        thold = input(20, title="Threshold")

        threshold = thold

        //Script for Indicator
        dirmov(len) =>
            up = change(high)
            down = -change(low)
            truerange = rma(tr, len)
            plus = fixnan(100 * rma(up > down and up > 0 ? up : 0, len) / truerange)
            minus = fixnan(100 * rma(down > up and down > 0 ? down : 0, len) / truerange)
            [plus, minus]

        adx(dilen, adxlen) =>
            [plus, minus] = dirmov(dilen)
            sum = plus + minus
            adx = 100 * rma(abs(plus - minus) / (sum == 0 ? 1 : sum), adxlen)
            [adx, plus, minus]

        [sig, up, down] = adx(dilen, adxlen)
        osob=input(40,title="Exhaustion Level for ADX, default = 40")
        col = sig >= sig[1] ? green : sig <= sig[1] ? red : gray

        //Plot Definitions Current Timeframe
        p1 = plot(sig, color=col, linewidth = 3, title="ADX")
        p2 = plot(sig, color=col, style=circles, linewidth=3, title="ADX")
        p3 = plot(up, color=blue, linewidth = 3, title="+DI")
        p4 = plot(up, color=blue, style=circles, linewidth=3, title="+DI")
        p5 = plot(down, color=fuchsia, linewidth = 3, title="-DI")
        p6 = plot(down, color=fuchsia, style=circles, linewidth=3, title="-DI")
        h1 = plot(threshold, color=black, linewidth =3, title="Threshold")

        trender = (sig >= up or sig >= down) ? 1 : 0
        bgcolor(trender>0?black:gray, transp=85)

        //Alert Function for ADX crossing Threshold
        Up_Cross = crossover(up, threshold)
        alertcondition(Up_Cross, title="DMI+ cross", message="DMI+ Crossing Threshold")
        Down_Cross = crossover(down, threshold)
        alertcondition(Down_Cross, title="DMI- cross", message="DMI- Crossing Threshold")

Args:
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    close (pd.Series): Series of 'close's
    length (int): It's period.  Default: 14
    drift (int): The difference period.   Default: 1
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: adx, dmp, dmn columns.
"""


aroon.__doc__ = \
"""Aroon (AROON)

Aroon attempts to identify if a security is trending and how strong.

Sources:
    https://www.tradingview.com/wiki/Aroon
    https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/aroon-ar/

Calculation:
    Default Inputs:
        length=1
    def maxidx(x):
        return 100 * (int(np.argmax(x)) + 1) / length

    def minidx(x):
        return 100 * (int(np.argmin(x)) + 1) / length

    _close = close.rolling(length, min_periods=min_periods)
    aroon_up = _close.apply(maxidx, raw=True)
    aroon_down = _close.apply(minidx, raw=True)

Args:
    close (pd.Series): Series of 'close's
    length (int): It's period.  Default: 1
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: aroon_up, aroon_down columns.
"""


decreasing.__doc__ = \
"""Decreasing

Returns True or False if the series is decreasing over a periods.  By default,
it returns True and False as 1 and 0 respectively with kwarg 'asint'.

Sources:

Calculation:
    decreasing = close.diff(length) < 0
    if asint:
        decreasing = decreasing.astype(int)

Args:
    close (pd.Series): Series of 'close's
    length (int): It's period.  Default: 1
    asint (bool): Returns as binary.  Default: True
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.Series: New feature generated.
"""


dpo.__doc__ = \
"""Detrend Price Oscillator (DPO)

Is an indicator designed to remove trend from price and make it easier to
identify cycles.

Sources:
    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:detrended_price_osci

Calculation:
    Default Inputs:
        length=1, centered=True
    SMA = Simple Moving Average
    drift = int(0.5 * length) + 1
    
    DPO = close.shift(drift) - SMA(close, length)
    if centered:
        DPO = DPO.shift(-drift)

Args:
    close (pd.Series): Series of 'close's
    length (int): It's period.  Default: 1
    centered (bool): Shift the dpo back by int(0.5 * length) + 1.  Default: True
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.Series: New feature generated.
"""


increasing.__doc__ = \
"""Increasing

Returns True or False if the series is increasing over a periods.  By default,
it returns True and False as 1 and 0 respectively with kwarg 'asint'.

Sources:

Calculation:
    increasing = close.diff(length) > 0
    if asint:
        increasing = increasing.astype(int)

Args:
    close (pd.Series): Series of 'close's
    length (int): It's period.  Default: 1
    asint (bool): Returns as binary.  Default: True
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.Series: New feature generated.
"""


vortex.__doc__ = \
"""Vortex

Two oscillators that capture positive and negative trend movement.

Sources:
    https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vortex_indicator

Calculation:
    Default Inputs:
        length=14, drift=1
    TR = True Range
    SMA = Simple Moving Average
    tr = TR(high, low, close)
    tr_sum = tr.rolling(length).sum()

    vmp = (high - low.shift(drift)).abs()
    vmn = (low - high.shift(drift)).abs()

    VIP = vmp.rolling(length).sum() / tr_sum
    VIM = vmn.rolling(length).sum() / tr_sum

Args:
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    close (pd.Series): Series of 'close's
    length (int): ROC 1 period.  Default: 14
    drift (int): The difference period.   Default: 1
    offset (int): How many periods to offset the result.  Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: vip and vim columns
"""




# Legacy Code
def macd_depreciated(close, n_fast=12, n_slow=26, fillna=False):
    """
    Moving Average Convergence Divergence (MACD)

    Is a trend-following momentum indicator that shows the relationship between
    two moving averages of prices.

    https://en.wikipedia.org/wiki/MACD

    Args:
        close(pandas.Series): dataset 'Close' column.
        n_fast(int): n period short-term.
        n_slow(int): n period long-term.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    emafast = ema(close, n_fast)
    emaslow = ema(close, n_slow)
    macd = emafast - emaslow
    if fillna:
        macd = macd.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(macd, name='MACD_%d_%d' % (n_fast, n_slow))


def macd_signal_depreciated(close, n_fast=12, n_slow=26, n_sign=9, fillna=False):
    """Moving Average Convergence Divergence (MACD Signal)

    Shows EMA of MACD.

    https://en.wikipedia.org/wiki/MACD

    Args:
        close(pandas.Series): dataset 'Close' column.
        n_fast(int): n period short-term.
        n_slow(int): n period long-term.
        n_sign(int): n period to signal.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    emafast = ema(close, n_fast)
    emaslow = ema(close, n_slow)
    macd = emafast - emaslow
    macd_signal = ema(macd, n_sign)
    if fillna:
        macd_signal = macd_signal.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(macd_signal, name='MACD_sign')


def macd_diff_depreciated(close, n_fast=12, n_slow=26, n_sign=9, fillna=False):
    """Moving Average Convergence Divergence (MACD Diff)

    Shows the relationship between MACD and MACD Signal.

    https://en.wikipedia.org/wiki/MACD

    Args:
        close(pandas.Series): dataset 'Close' column.
        n_fast(int): n period short-term.
        n_slow(int): n period long-term.
        n_sign(int): n period to signal.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    emafast = ema(close, n_fast)
    emaslow = ema(close, n_slow)
    macd = emafast - emaslow
    macdsign = ema(macd, n_sign)
    macd_diff = macd - macdsign
    if fillna:
        macd_diff = macd_diff.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(macd_diff, name='MACD_diff')


def ema_indicator_depreciated(close, n=12, fillna=False):
    """EMA

    Exponential Moving Average via Pandas

    Args:
        close(pandas.Series): dataset 'Close' column.
        n_fast(int): n period short-term.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    ema_ = ema(close, n)
    if fillna:
        ema_ = ema_.replace([np.inf, -np.inf], np.nan).fillna(method='backfill')
    return pd.Series(ema_, name='ema')


def adx_depreciated(high, low, close, n=14, fillna=False):
    """Average Directional Movement Index (ADX)

    The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI)
    are derived from smoothed averages of these differences, and measure trend
    direction over time. These two indicators are often referred to collectively
    as the Directional Movement Indicator (DMI).

    The Average Directional Index (ADX) is in turn derived from the smoothed
    averages of the difference between +DI and -DI, and measures the strength
    of the trend (regardless of direction) over time.

    Using these three indicators together, chartists can determine both the
    direction and strength of the trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    cs = close.shift(1)

    tr = high.combine(cs, max) - low.combine(cs, min)
    trs = tr.rolling(n).sum()

    up = high - high.shift(1)
    dn = low.shift(1) - low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    dip = 100 * pos.rolling(n).sum() / trs
    din = 100 * neg.rolling(n).sum() / trs

    dx = 100 * np.abs((dip - din) / (dip + din))
    adx = ema(dx, n)

    if fillna:
        adx = adx.replace([np.inf, -np.inf], np.nan).fillna(40)
    return pd.Series(adx, name='adx')


def adx_pos_depreciated(high, low, close, n=14, fillna=False):
    """Average Directional Movement Index Positive (ADX)

    The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI)
    are derived from smoothed averages of these differences, and measure trend
    direction over time. These two indicators are often referred to collectively
    as the Directional Movement Indicator (DMI).

    The Average Directional Index (ADX) is in turn derived from the smoothed
    averages of the difference between +DI and -DI, and measures the strength
    of the trend (regardless of direction) over time.

    Using these three indicators together, chartists can determine both the
    direction and strength of the trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    cs = close.shift(1)

    tr = high.combine(cs, max) - low.combine(cs, min)
    trs = tr.rolling(n).sum()

    up = high - high.shift(1)
    dn = low.shift(1) - low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    dip = 100 * pos.rolling(n).sum() / trs

    if fillna:
        dip = dip.replace([np.inf, -np.inf], np.nan).fillna(20)
    return pd.Series(dip, name='adx_pos')


def adx_neg_depreciated(high, low, close, n=14, fillna=False):
    """Average Directional Movement Index Negative (ADX)

    The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI)
    are derived from smoothed averages of these differences, and measure trend
    direction over time. These two indicators are often referred to collectively
    as the Directional Movement Indicator (DMI).

    The Average Directional Index (ADX) is in turn derived from the smoothed
    averages of the difference between +DI and -DI, and measures the strength
    of the trend (regardless of direction) over time.

    Using these three indicators together, chartists can determine both the
    direction and strength of the trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    cs = close.shift(1)

    tr = high.combine(cs, max) - low.combine(cs, min)
    trs = tr.rolling(n).sum()

    up = high - high.shift(1)
    dn = low.shift(1) - low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    din = 100 * neg.rolling(n).sum() / trs

    if fillna:
        din = din.replace([np.inf, -np.inf], np.nan).fillna(20)
    return pd.Series(din, name='adx_neg')


def adx_indicator_depreciated(high, low, close, n=14, fillna=False):
    """Average Directional Movement Index Indicator (ADX)

    Returns 1, if Plus Directional Indicator (+DI) is higher than Minus
    Directional Indicator (-DI). Else, return 0.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    cs = close.shift(1)

    tr = high.combine(cs, max) - low.combine(cs, min)
    trs = tr.rolling(n).sum()

    up = high - high.shift(1)
    dn = low.shift(1) - low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    dip = 100 * pos.rolling(n).sum() / trs
    din = 100 * neg.rolling(n).sum() / trs

    adx_diff = dip - din

    # prepare indicator
    df = pd.DataFrame([adx_diff]).T
    df.columns = ['adx_diff']
    df['adx_ind'] = 0
    df.loc[df['adx_diff'] > 0, 'adx_ind'] = 1
    adx_ind = df['adx_ind']

    if fillna:
        adx_ind = adx_ind.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(adx_ind, name='adx_ind')


def vortex_indicator_pos_depreciated(high, low, close, n=14, fillna=False):
    """Vortex Indicator (VI)

    It consists of two oscillators that capture positive and negative trend
    movement. A bullish signal triggers when the positive trend indicator
    crosses above the negative trend indicator or a key level.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vortex_indicator

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    tr = high.combine(close.shift(1), max) - low.combine(close.shift(1), min)
    trn = tr.rolling(n).sum()

    vmp = np.abs(high - low.shift(1))
    vmm = np.abs(low - high.shift(1))

    vip = vmp.rolling(n).sum() / trn
    if fillna:
        vip = vip.replace([np.inf, -np.inf], np.nan).fillna(1)
    return pd.Series(vip, name='vip')


def vortex_indicator_neg_depreciated(high, low, close, n=14, fillna=False):
    """Vortex Indicator (VI)

    It consists of two oscillators that capture positive and negative trend
    movement. A bearish signal triggers when the negative trend indicator
    crosses above the positive trend indicator or a key level.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vortex_indicator

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    tr = high.combine(close.shift(1), max) - low.combine(close.shift(1), min)
    trn = tr.rolling(n).sum()

    vmp = np.abs(high - low.shift(1))
    vmm = np.abs(low - high.shift(1))

    vin = vmm.rolling(n).sum() / trn
    if fillna:
        vin = vin.replace([np.inf, -np.inf], np.nan).fillna(1)
    return pd.Series(vin, name='vin')


def trix_depreciated(close, n=15, fillna=False):
    """Trix (TRIX)

    Shows the percent rate of change of a triple exponentially smoothed moving
    average.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:trix

    Args:
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    ema1 = ema(close, n)
    ema2 = ema(ema1, n)
    ema3 = ema(ema2, n)
    trix = (ema3 - ema3.shift(1)) / ema3.shift(1)
    trix *= 100
    if fillna:
        trix = trix.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(trix, name='trix_'+str(n))


def mass_index_depreciated(high, low, n=9, n2=25, fillna=False):
    """Mass Index (MI)

    It uses the high-low range to identify trend reversals based on range
    expansions. It identifies range bulges that can foreshadow a reversal of the
    current trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:mass_index

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        n(int): n low period.
        n2(int): n high period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.

    """
    amplitude = high - low
    ema1 = ema(amplitude, n)
    ema2 = ema(ema1, n)
    mass = ema1 / ema2
    mass = mass.rolling(n2).sum()
    if fillna:
        mass = mass.replace([np.inf, -np.inf], np.nan).fillna(n2)
    return pd.Series(mass, name='mass_index_'+str(n))


def cci_depreciated(high, low, close, n=20, c=0.015, fillna=False):
    """Commodity Channel Index (CCI)

    CCI measures the difference between a security's price change and its
    average price change. High positive readings indicate that prices are well
    above their average, which is a show of strength. Low negative readings
    indicate that prices are well below their average, which is a show of
    weakness.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:commodity_channel_index_cci

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        c(int): constant.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.

    """
    pp = (high + low + close) / 3.0
    cci = (pp - pp.rolling(n).mean()) / (c * pp.rolling(n).std())
    if fillna:
        cci = cci.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(cci, name='cci')


def dpo_depreciated(close, n=20, fillna=False):
    """Detrended Price Oscillator (DPO)

    Is an indicator designed to remove trend from price and make it easier to
    identify cycles.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:detrended_price_osci

    Args:
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    dpo = close.shift(int((0.5 * n) + 1)) - close.rolling(n).mean()
    if fillna:
        dpo = dpo.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(dpo, name='dpo_'+str(n))


def kst_depreciated(close, r1=10, r2=15, r3=20, r4=30, n1=10, n2=10, n3=10, n4=15, fillna=False):
    """KST Oscillator (KST)

    It is useful to identify major stock market cycle junctures because its
    formula is weighed to be more greatly influenced by the longer and more
    dominant time spans, in order to better reflect the primary swings of stock
    market cycle.

    https://en.wikipedia.org/wiki/KST_oscillator

    Args:
        close(pandas.Series): dataset 'Close' column.
        r1(int): r1 period.
        r2(int): r2 period.
        r3(int): r3 period.
        r4(int): r4 period.
        n1(int): n1 smoothed period.
        n2(int): n2 smoothed period.
        n3(int): n3 smoothed period.
        n4(int): n4 smoothed period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    rocma1 = ((close - close.shift(r1)) / close.shift(r1)).rolling(n1).mean()
    rocma2 = ((close - close.shift(r2)) / close.shift(r2)).rolling(n2).mean()
    rocma3 = ((close - close.shift(r3)) / close.shift(r3)).rolling(n3).mean()
    rocma4 = ((close - close.shift(r4)) / close.shift(r4)).rolling(n4).mean()
    kst = 100 * (rocma1 + 2 * rocma2 + 3 * rocma3 + 4 * rocma4)
    if fillna:
        kst = kst.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(kst, name='kst')


def kst_sig_depreciated(close, r1=10, r2=15, r3=20, r4=30, n1=10, n2=10, n3=10, n4=15, nsig=9, fillna=False):
    """KST Oscillator (KST Signal)

    It is useful to identify major stock market cycle junctures because its
    formula is weighed to be more greatly influenced by the longer and more
    dominant time spans, in order to better reflect the primary swings of stock
    market cycle.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:know_sure_thing_kst

    Args:
        close(pandas.Series): dataset 'Close' column.
        r1(int): r1 period.
        r2(int): r2 period.
        r3(int): r3 period.
        r4(int): r4 period.
        n1(int): n1 smoothed period.
        n2(int): n2 smoothed period.
        n3(int): n3 smoothed period.
        n4(int): n4 smoothed period.
        nsig(int): n period to signal.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    rocma1 = ((close - close.shift(r1)) / close.shift(r1)).rolling(n1).mean()
    rocma2 = ((close - close.shift(r2)) / close.shift(r2)).rolling(n2).mean()
    rocma3 = ((close - close.shift(r3)) / close.shift(r3)).rolling(n3).mean()
    rocma4 = ((close - close.shift(r4)) / close.shift(r4)).rolling(n4).mean()
    kst = 100 * (rocma1 + 2 * rocma2 + 3 * rocma3 + 4 * rocma4)
    kst_sig = kst.rolling(nsig).mean()
    if fillna:
        kst_sig = kst_sig.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(kst_sig, name='kst_sig')


def ichimoku_a_depreciated(high, low, n1=9, n2=26, fillna=False):
    """Ichimoku Kinkō Hyō (Ichimoku)

    It identifies the trend and look for potential signals within that trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:ichimoku_cloud

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        n1(int): n1 low period.
        n2(int): n2 medium period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    conv = 0.5 * (high.rolling(n1).max() + low.rolling(n1).min())
    base = 0.5 * (high.rolling(n2).max() + low.rolling(n2).min())

    spana = 0.5 * (conv + base)
    spana = spana.shift(n2)

    if fillna:
        spana = spana.replace([np.inf, -np.inf], np.nan).fillna(method='backfill')
    return pd.Series(spana, name='ichimoku_a_'+str(n2))


def ichimoku_b_depreciated(high, low, n2=26, n3=52, fillna=False):
    """Ichimoku Kinkō Hyō (Ichimoku)

    It identifies the trend and look for potential signals within that trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:ichimoku_cloud

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        n2(int): n2 medium period.
        n3(int): n3 high period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    spanb = 0.5 * (high.rolling(n3).max() + low.rolling(n3).min())
    spanb = spanb.shift(n2)
    if fillna:
        spanb = spanb.replace([np.inf, -np.inf], np.nan).fillna(method='backfill')
    return pd.Series(spanb, name='ichimoku_b_'+str(n2))


def aroon_up_depreciated(close, n=25, fillna=False):
    """Aroon Indicator (AI)

    Identify when trends are likely to change direction (uptrend).

    Aroon Up - ((N - Days Since N-day High) / N) x 100

    https://www.investopedia.com/terms/a/aroon.asp
    Args:
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.

    """
    aroon_up = close.rolling(n).apply(lambda x: float(np.argmax(x) + 1) / n * 100)
    if fillna:
        aroon_up = aroon_up.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(aroon_up, name='aroon_up'+str(n))


def aroon_down_depreciated(close, n=25, fillna=False):
    """Aroon Indicator (AI)

    Identify when trends are likely to change direction (downtrend).

    Aroon Down - ((N - Days Since N-day Low) / N) x 100

    https://www.investopedia.com/terms/a/aroon.asp
    Args:
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.

    Returns:
        pandas.Series: New feature generated.
    """
    aroon_down = close.rolling(n).apply(lambda x: float(np.argmin(x) + 1) / n * 100)
    if fillna:
        aroon_down = aroon_down.replace([np.inf, -np.inf], np.nan).fillna(0)
    return pd.Series(aroon_down, name='aroon_down'+str(n))
