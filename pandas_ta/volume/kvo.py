# -*- coding: utf-8 -*-
from numpy import isnan
from pandas import DataFrame
from pandas_ta.overlap import hlc3, ma
from pandas_ta.utils import get_drift, get_offset, signed_series, verify_series


def kvo(high, low, close, volume, fast=None, slow=None, signal=None, mamode=None, drift=None, offset=None, **kwargs):
    """Indicator: Klinger Volume Oscillator (KVO)"""
    # Validate arguments
    fast = int(fast) if fast and fast > 0 else 34
    slow = int(slow) if slow and slow > 0 else 55
    signal = int(signal) if signal and signal > 0 else 13
    mamode = mamode.lower() if mamode and isinstance(mamode, str) else "ema"
    _length = max(fast, slow, signal)
    high = verify_series(high, _length)
    low = verify_series(low, _length)
    close = verify_series(close, _length)
    volume = verify_series(volume, _length)
    drift = get_drift(drift)
    offset = get_offset(offset)

    if high is None or low is None or close is None or volume is None:
        return

    # Calculate Trend (T) and Trend groups (dtrend)
    trend = signed_series(hlc3(high, low, close), 1)
    dtrend = trend.diff().ne(0).cumsum()

    # Calculate the Daily Measurement (dm)
    dm = high - low

    # Calculate the Cumulative Measurement (cm)
    df = DataFrame({'dtrend': dtrend, 'dm': dm})
    df['dm_cumsum'] = df.groupby('dtrend')['dm'].cumsum()
    mask = df['dtrend'].ne(df['dtrend'].shift())
    df.loc[mask, 'previous_dm'] = df['dm'].shift()
    df['previous_dm'].ffill(inplace=True)
    cm = df['dm_cumsum'].add(df['previous_dm'], fill_value=0)

    # Avoid division by zero by adding a small number to 'cm' where it's zero
    cm += cm.where(cm == 0, 1e-10)

    # Calculate the Volume Force (VF)
    vf = volume * (-2 * ((dm / cm) - 1)) * trend * 100

    kvo = ma(mamode, vf, length=fast, **kwargs) - ma(mamode, vf, length=slow, **kwargs)
    kvo_signal = ma(mamode, kvo.loc[kvo.first_valid_index():,], length=signal, **kwargs)

    if kvo is None or all(isnan(kvo.values)):
        return  # Emergency Break

    if kvo_signal is None or all(isnan(kvo_signal.values)):
        return  # Emergency Break

    # Offset
    if offset != 0:
        kvo = kvo.shift(offset)
        kvo_signal = kvo_signal.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        kvo.fillna(kwargs["fillna"], inplace=True)
        kvo_signal.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        kvo.fillna(method=kwargs["fill_method"], inplace=True)
        kvo_signal.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Categorize it
    _props = f"_{fast}_{slow}_{signal}_{mamode}"
    kvo.name = f"KVO{_props}"
    kvo_signal.name = f"KVOs{_props}"
    kvo.category = kvo_signal.category = "volume"

    # Prepare DataFrame to return
    data = {kvo.name: kvo, kvo_signal.name: kvo_signal}
    df = DataFrame(data)
    df.name = f"KVO{_props}"
    df.category = kvo.category

    return df


kvo.__doc__ = \
"""Klinger Volume Oscillator (KVO)

This indicator was developed by Stephen J. Klinger. It is designed to predict
price reversals in a market by comparing volume to price.

Sources:
    https://www.investopedia.com/terms/k/klingeroscillator.asp
    https://www.daytrading.com/klinger-volume-oscillator

Calculation:
    Default Inputs:
        fast=34, slow=55, signal=13, drift=1
    EMA = Exponential Moving Average

    SV = volume * signed_series(HLC3, 1)
    KVO = EMA(SV, fast) - EMA(SV, slow)
    Signal = EMA(KVO, signal)

Args:
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    close (pd.Series): Series of 'close's
    volume (pd.Series): Series of 'volume's
    fast (int): The fast period. Default: 34
    long (int): The long period. Default: 55
    length_sig (int): The signal period. Default: 13
    mamode (str): See ```help(ta.ma)```. Default: 'ema'
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: KVO and Signal columns.
"""
