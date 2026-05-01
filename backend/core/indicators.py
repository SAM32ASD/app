import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(closes: list[float], period: int = 9) -> float:
    if len(closes) < period + 1:
        return 50.0
    arr = np.array(closes[:period + 1], dtype=np.float64)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains) if len(gains) > 0 else 0.0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_atr(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> float:
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return 0.0
    tr_list = []
    for i in range(period):
        h = highs[i]
        l = lows[i]
        prev_c = closes[i + 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)
    return float(np.mean(tr_list)) if tr_list else 0.0


def calculate_adx(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> float:
    n = period + 1
    if len(highs) < n or len(lows) < n or len(closes) < n:
        return 0.0

    plus_dm_list = []
    minus_dm_list = []
    tr_list = []

    for i in range(period):
        h = highs[i]
        l = lows[i]
        prev_h = highs[i + 1]
        prev_l = lows[i + 1]
        prev_c = closes[i + 1]

        up_move = h - prev_h
        down_move = prev_l - l
        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))

        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)
        tr_list.append(tr)

    atr = np.mean(tr_list)
    if atr == 0:
        return 0.0

    plus_di = (np.mean(plus_dm_list) / atr) * 100
    minus_di = (np.mean(minus_dm_list) / atr) * 100

    di_sum = plus_di + minus_di
    if di_sum == 0:
        return 0.0
    dx = abs(plus_di - minus_di) / di_sum * 100
    return float(dx)


def find_significant_high(
    highs: list[float], ask: float, bars_n: int = 3,
    bars_lookback: int = 25, min_dist_points: int = 100, point: float = 0.01
) -> float:
    half = bars_n // 2
    for i in range(bars_n, min(bars_lookback, len(highs) - half)):
        center = highs[i]
        is_high = True
        for j in range(1, half + 1):
            if i + j < len(highs) and highs[i + j] >= center:
                is_high = False
                break
            if i - j >= 0 and highs[i - j] >= center:
                is_high = False
                break
        if is_high and (center - ask) / point >= min_dist_points:
            return center
    return -1.0


def find_significant_low(
    lows: list[float], bid: float, bars_n: int = 3,
    bars_lookback: int = 25, min_dist_points: int = 100, point: float = 0.01
) -> float:
    half = bars_n // 2
    for i in range(bars_n, min(bars_lookback, len(lows) - half)):
        center = lows[i]
        is_low = True
        for j in range(1, half + 1):
            if i + j < len(lows) and lows[i + j] <= center:
                is_low = False
                break
            if i - j >= 0 and lows[i - j] <= center:
                is_low = False
                break
        if is_low and (bid - center) / point >= min_dist_points:
            return center
    return -1.0
