# -*- coding: utf-8 -*-
from pandas import DataFrame, Series
from pandas_ta.utils import get_drift, get_offset, non_zero_range, verify_series


def brar(
    open_: Series, high: Series, low: Series, close: Series,
    length: int = None, scalar: float = None, drift: int = None,
    offset: int = None, **kwargs
) -> DataFrame:
    """BRAR (BRAR)

    BR and AR

    Sources:
        No internet resources on definitive definition.
        Request by Github user homily, issue #46

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 26
        scalar (float): How much to magnify. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: ar, br columns.
    """
    # Validate
    length = int(length) if length and length > 0 else 26
    scalar = float(scalar) if scalar else 100
    high_open_range = non_zero_range(high, open_)
    open_low_range = non_zero_range(open_, low)
    open_ = verify_series(open_, length)
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)
    drift = get_drift(drift)
    offset = get_offset(offset)

    if open_ is None or high is None or low is None or close is None:
        return

    # Calculate
    hcy = non_zero_range(high, close.shift(drift))
    cyl = non_zero_range(close.shift(drift), low)

    hcy[hcy < 0] = 0  # Zero negative values
    cyl[cyl < 0] = 0  # ""

    ar = scalar * high_open_range.rolling(length).sum()
    ar /= open_low_range.rolling(length).sum()

    br = scalar * hcy.rolling(length).sum()
    br /= cyl.rolling(length).sum()

    # Offset
    if offset != 0:
        ar = ar.shift(offset)
        br = ar.shift(offset)

    # Fill
    if "fillna" in kwargs:
        ar.fillna(kwargs["fillna"], inplace=True)
        br.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        ar.fillna(method=kwargs["fill_method"], inplace=True)
        br.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Category
    _props = f"_{length}"
    ar.name = f"AR{_props}"
    br.name = f"BR{_props}"
    ar.category = br.category = "momentum"

    brardf = DataFrame({ar.name: ar, br.name: br})
    brardf.name = f"BRAR{_props}"
    brardf.category = "momentum"

    return brardf
