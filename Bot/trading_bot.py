# =========================================================
# BEHZAD ULTIMATE PRO V3.0 REAL-TIME FUTURES TRADING BOT - HEADLESS VERSION FOR RENDER
# نسخه بدون GUI برای اجرا در Render - منطق کاملاً مشابه نسخه اصلی
# =========================================================
import ccxt
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import warnings
import os
import math
from itertools import zip_longest
import traceback
import sys

warnings.filterwarnings('ignore')

print("🚀 BEHZAD ULTIMATE PRO - XT.COM FUTURES TRADING BOT (HEADLESS FOR RENDER)")
print("=" * 70)

# ==================== تنظیمات معاملاتی (دقیقاً مثل Futures.py) ====================
INITIAL_CAPITAL = 1000.0

# ================= حالت معاملاتی =================
TRADING_MODE = 'BOTH'

# ================= تنظیمات برای حالت BUY =================
BUY_RSI_UPPER_BOUND = 55
BUY_RSI_LOWER_BOUND = 35
BUY_RSI_NEUTRAL = 55
BUY_MACD_FAST = 12
BUY_MACD_SLOW = 26
BUY_MACD_SIGNAL = 9
BUY_MACD_BULLISH = True
BUY_STOP_LOSS_ENABLED = False
BUY_STOP_LOSS_PERCENT = 5.0
BUY_MIN_STOP_LOSS_PERCENT = 1.5
BUY_TP_METHOD = 1
BUY_TP_PERCENT = 3.0
BUY_TP_ATR_MULTIPLIER = 3.0
BUY_TP_SIGNAL_PERCENT = 2.0
BUY_TREND_FILTER_ENABLED = True
BUY_TREND_PRIMARY_TF = 'daily'
BUY_TREND_SECONDARY_TF = '4h'
BUY_TREND_EMA_FAST = 14
BUY_TREND_EMA_SLOW = 33
BUY_TREND_EMA_SIGNAL = 60
BUY_TREND_CONDITION = 'primary_only'
BUY_ADX_FILTER_ENABLED = True
BUY_ADX_PERIOD = 21
BUY_ADX_THRESHOLD = 33
BUY_ENTRY_TIMEFRAMES = ['4h', 'daily']
BUY_EXIT_TIMEFRAMES = ['4h']
BUY_EXIT_ATR_TIMEFRAMES = ['4h']
BUY_SCORING_SYSTEM_ENABLED = True
BUY_SCORING_WEIGHTS = {'rsi': 1.0, 'macd': 1.0, 'trend': 1.5, 'adx': 3.0}

# ================= تنظیمات برای حالت SELL =================
SELL_RSI_UPPER_BOUND = 70
SELL_RSI_LOWER_BOUND = 50
SELL_RSI_NEUTRAL = 45
SELL_MACD_FAST = 9
SELL_MACD_SLOW = 14
SELL_MACD_SIGNAL = 9
SELL_MACD_BEARISH = True
SELL_STOP_LOSS_ENABLED = True
SELL_STOP_LOSS_METHOD = 1
SELL_STOP_LOSS_PERCENT = 3.0
SELL_STOP_LOSS_ATR_MULTIPLIER = 1.8
SELL_MIN_STOP_LOSS_PERCENT = 1.5
SELL_TP_METHOD = 1
SELL_TP_PERCENT = 2.0
SELL_TP_ATR_MULTIPLIER = 3.0
SELL_TP_SIGNAL_PERCENT = 2.0
SELL_TREND_FILTER_ENABLED = True
SELL_TREND_PRIMARY_TF = 'daily'
SELL_TREND_SECONDARY_TF = '4h'
SELL_TREND_EMA_FAST = 14
SELL_TREND_EMA_SLOW = 33
SELL_TREND_EMA_SIGNAL = 60
SELL_TREND_CONDITION = 'primary_only'
SELL_ADX_FILTER_ENABLED = True
SELL_ADX_PERIOD = 21
SELL_ADX_THRESHOLD = 25
SELL_ENTRY_TIMEFRAMES = ['4h', 'daily']
SELL_EXIT_TIMEFRAMES = ['1h']
SELL_EXIT_ATR_TIMEFRAMES = ['4h']
SELL_SCORING_SYSTEM_ENABLED = True
SELL_SCORING_WEIGHTS = {'rsi': 1.0, 'macd': 1.0, 'trend': 1.5, 'adx': 3.0}

# ================= پارامترهای اصلی معامله =================
ENTRY_SCORE_THRESHOLD = 2.5
TRADE_DELAY_MINUTES = 0
POSITION_SIZE_PCT = 0.99
COMMISSION_RATE = 0.0
RSI_PERIOD = 7
ATR_PERIOD = 7
ATR_M = 1.2
MIN_TOTAL_SCORE = 2.5

# ==================== Exchange Configuration ====================
EXCHANGE_NAME = 'xt'
SYMBOL = 'ETH/USDT:USDT'
LEVERAGE = 1

# خواندن کلیدها از متغیرهای محیطی (ایمن‌تر)
API_KEY = os.environ.get('XT_API_KEY', '4bf461c4-2ede-417a-a107-bb5bfb2468e0')
API_SECRET = os.environ.get('XT_API_SECRET', '19423072f1b791274b908a721b9426cecbf145e9')
REAL_TRADING = True

# ==================== متغیرهای جهانی ====================
exchange = None
in_position = False
entry_price = 0.0
tp_price = 0.0
sl_price = 0.0
position_open_time = None
position_size = 0.0
balance = 0.0
trades = []
trade_counter = 0
position_type = 'long'
total_pnl = 0.0
initial_capital = 0.0
initial_capital_set = False
equity_history = []
signals = []

# اندیکاتورهای چند تایم‌فریمی
timeframe_indicators = {}

# ==================== متغیرهای جدید برای سیستم Fixed مانند V25 ====================
INDICATORS_FIXED = {}
OPEN_PRICES_FIXED = {}
CLOSE_PRICES_FIXED = {}
LAST_CANDLE_TIMES = {}
PREVIOUS_CANDLE_TIMES = {}

# برای ذخیره وضعیت
STATE_FILE = "futures_trading_state_HEADLESS.json"

# ==================== متغیرهای جدید برای مدیریت ====================
MAX_CACHE_SIZE = 1000

# ==================== توابع کمکی (دقیقاً از Futures.py) ====================

def calculate_ema_incremental(prices, period):
    """محاسبه EMA به صورت تدریجی بدون look-ahead"""
    n = len(prices)
    ema = np.full(n, np.nan)
    
    if n < period:
        return ema
    
    ema[period-1] = np.mean(prices[:period])
    alpha = 2 / (period + 1)
    
    for i in range(period, n):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
    
    return ema

def calculate_rsi_incremental(prices, period=RSI_PERIOD):
    """محاسبه RSI به صورت تدریجی"""
    n = len(prices)
    rsi = np.full(n, np.nan)
    
    if n <= period:
        return rsi
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    if avg_loss == 0:
        rsi[period] = 100
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100 - (100 / (1 + rs))
    
    for i in range(period + 1, n):
        gain = gains[i-1]
        loss = losses[i-1]
        
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd_incremental(prices, fast, slow, signal):
    """محاسبه MACD به صورت تدریجی با پارامترهای قابل تنظیم"""
    ema_fast = calculate_ema_incremental(prices, fast)
    ema_slow = calculate_ema_incremental(prices, slow)
    macd_line = ema_fast - ema_slow
    
    valid_macd = macd_line[~np.isnan(macd_line)]
    
    if len(valid_macd) < signal:
        macd_signal = np.full_like(macd_line, np.nan)
    else:
        macd_signal_valid = calculate_ema_incremental(valid_macd, signal)
        macd_signal = np.full_like(macd_line, np.nan)
        valid_indices = np.where(~np.isnan(macd_line))[0]
        
        if len(valid_indices) >= signal:
            first_signal_idx = valid_indices[signal-1]
            num_values = len(macd_signal_valid)
            
            for i in range(num_values):
                if first_signal_idx + i < len(macd_signal):
                    macd_signal[first_signal_idx + i] = macd_signal_valid[i]
    
    histogram = macd_line - macd_signal
    
    return macd_line, macd_signal, histogram

def calculate_atr_incremental(high, low, close, period=7):
    """محاسبه ATR به صورت تدریجی"""
    n = len(high)
    atr = np.full(n, np.nan)
    
    if n <= period:
        return atr
    
    tr = np.full(n, np.nan)
    
    if n > 0:
        tr[0] = high[0] - low[0]
    
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    atr[period-1] = np.mean(tr[:period])
    
    for i in range(period, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    
    return atr

def calculate_adx_incremental(high, low, close, period=14):
    """محاسبه ADX به صورت تدریجی"""
    n = len(high)
    
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    
    for i in range(1, n):
        up_move = high[i] - high[i-1]
        down_move = low[i-1] - low[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
    
    tr_smooth = np.zeros(n)
    plus_dm_smooth = np.zeros(n)
    minus_dm_smooth = np.zeros(n)
    
    tr_smooth[period-1] = np.sum(tr[:period])
    plus_dm_smooth[period-1] = np.sum(plus_dm[:period])
    minus_dm_smooth[period-1] = np.sum(minus_dm[:period])
    
    for i in range(period, n):
        tr_smooth[i] = tr_smooth[i-1] - (tr_smooth[i-1]/period) + tr[i]
        plus_dm_smooth[i] = plus_dm_smooth[i-1] - (plus_dm_smooth[i-1]/period) + plus_dm[i]
        minus_dm_smooth[i] = minus_dm_smooth[i-1] - (minus_dm_smooth[i-1]/period) + minus_dm[i]
    
    plus_di = np.zeros(n)
    minus_di = np.zeros(n)
    
    for i in range(period, n):
        if tr_smooth[i] != 0:
            plus_di[i] = 100 * (plus_dm_smooth[i] / tr_smooth[i])
            minus_di[i] = 100 * (minus_dm_smooth[i] / tr_smooth[i])
    
    dx = np.zeros(n)
    for i in range(period, n):
        if (plus_di[i] + minus_di[i]) != 0:
            dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])
    
    adx = np.zeros(n)
    if n >= 2*period:
        adx[2*period-1] = np.mean(dx[period:2*period])
        
        for i in range(2*period, n):
            adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
    
    return adx, plus_di, minus_di

def calculate_indicators_for_timeframe(df, position_type='long'):
    """محاسبه اندیکاتورها برای یک تایم‌فرم خاص بر اساس position_type"""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # محاسبه RSI
    rsi = calculate_rsi_incremental(close, RSI_PERIOD)
    
    # محاسبه ATR
    atr = calculate_atr_incremental(high, low, close, ATR_PERIOD)
    
    # تعیین پارامترهای MACD بر اساس position_type
    if position_type == 'long':
        macd_fast = BUY_MACD_FAST
        macd_slow = BUY_MACD_SLOW
        macd_signal = BUY_MACD_SIGNAL
    else:  # short position
        macd_fast = SELL_MACD_FAST
        macd_slow = SELL_MACD_SLOW
        macd_signal = SELL_MACD_SIGNAL
    
    # محاسبه MACD
    macd_line, macd_signal_line, _ = calculate_macd_incremental(close, macd_fast, macd_slow, macd_signal)
    
    df_indicators = df.copy()
    df_indicators['rsi'] = rsi
    df_indicators['macd'] = macd_line
    df_indicators['macd_signal'] = macd_signal_line
    df_indicators['atr'] = atr
    
    # تعیین پارامترهای ADX بر اساس position_type
    if position_type == 'long':
        adx_enabled = BUY_ADX_FILTER_ENABLED
        adx_period = BUY_ADX_PERIOD
    else:  # short position
        adx_enabled = SELL_ADX_FILTER_ENABLED
        adx_period = SELL_ADX_PERIOD
    
    if adx_enabled:
        adx, plus_di, minus_di = calculate_adx_incremental(high, low, close, adx_period)
        df_indicators['adx'] = adx
        df_indicators['plus_di'] = plus_di
        df_indicators['minus_di'] = minus_di
    
    # تعیین پارامترهای فیلتر روند بر اساس position_type
    if position_type == 'long':
        trend_enabled = BUY_TREND_FILTER_ENABLED
        ema_fast = BUY_TREND_EMA_FAST
        ema_slow = BUY_TREND_EMA_SLOW
        ema_signal = BUY_TREND_EMA_SIGNAL
    else:  # short position
        trend_enabled = SELL_TREND_FILTER_ENABLED
        ema_fast = SELL_TREND_EMA_FAST
        ema_slow = SELL_TREND_EMA_SLOW
        ema_signal = SELL_TREND_EMA_SIGNAL
    
    if trend_enabled:
        df_indicators['ema_fast'] = calculate_ema_incremental(close, ema_fast)
        df_indicators['ema_slow'] = calculate_ema_incremental(close, ema_slow)
        df_indicators['ema_signal'] = calculate_ema_incremental(close, ema_signal)
    
    # محاسبه حداقل داده مورد نیاز
    if position_type == 'long':
        min_required = max(50, macd_slow + macd_signal, 
                          adx_period * 2 if adx_enabled else 0,
                          max(ema_fast, ema_slow, ema_signal) if trend_enabled else 0)
    else:
        min_required = max(50, macd_slow + macd_signal, 
                          adx_period * 2 if adx_enabled else 0,
                          max(ema_fast, ema_slow, ema_signal) if trend_enabled else 0)
    
    if len(df_indicators) > min_required:
        df_indicators = df_indicators.iloc[min_required:].copy()
    
    return df_indicators

# ==================== توابع کمک‌کننده تایم‌فرم ====================

def get_candle_start_time(close_time, timeframe):
    """دریافت زمان شروع کندل بر اساس زمان بسته شدن و تایم‌فرم"""
    if timeframe == '1h':
        return close_time - timedelta(hours=1)
    elif timeframe == '2h':
        return close_time - timedelta(hours=2)
    elif timeframe == '4h':
        return close_time - timedelta(hours=4)
    elif timeframe == 'daily':
        return close_time - timedelta(days=1)
    else:
        return close_time

def get_candle_close_time(start_time, timeframe):
    """دریافت زمان بسته شدن کندل بر اساس زمان شروع و تایم‌فرم"""
    if timeframe == '1h':
        return start_time + timedelta(hours=1)
    elif timeframe == '2h':
        return start_time + timedelta(hours=2)
    elif timeframe == '4h':
        return start_time + timedelta(hours=4)
    elif timeframe == 'daily':
        return start_time + timedelta(days=1)
    else:
        return start_time

def is_timeframe_close_time(current_time, timeframe):
    """بررسی اینکه آیا زمان فعلی زمان بسته شدن برای تایم‌فرم داده‌شده است"""
    if timeframe == '1h':
        return current_time.minute == 0 and current_time.second == 0
    elif timeframe == '2h':
        return current_time.hour % 2 == 0 and current_time.minute == 0 and current_time.second == 0
    elif timeframe == '4h':
        return current_time.hour in [0, 4, 8, 12, 16, 20] and current_time.minute == 0 and current_time.second == 0
    elif timeframe == 'daily':
        return current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0
    else:
        return False

def is_within_trading_hours(current_time):
    """بررسی اینکه آیا زمان فعلی در ساعات معاملاتی است"""
    return True

# ==================== توابع مدیریت ریسک ====================

def calculate_stop_loss(entry_price, atr_value, entry_time, timeframe_data, position_type='long'):
    """محاسبه سطح استاپ‌لاس بر اساس position_type"""
    if position_type == 'long':
        if not BUY_STOP_LOSS_ENABLED:
            return 0
        
        stop_loss = entry_price * (1 - BUY_STOP_LOSS_PERCENT / 100)
        min_stop = entry_price * (1 - BUY_MIN_STOP_LOSS_PERCENT / 100)
        stop_loss = min(stop_loss, min_stop)
    else:  # short position
        if not SELL_STOP_LOSS_ENABLED:
            return 0
        
        method = SELL_STOP_LOSS_METHOD
        if method == 1:  # درصد ثابت
            stop_loss = entry_price * (1 + SELL_STOP_LOSS_PERCENT / 100)
        elif method == 2:  # ضریب ATR
            stop_loss = entry_price + (atr_value * SELL_STOP_LOSS_ATR_MULTIPLIER)
        else:  # روش سطح مقاومت
            if entry_time in timeframe_data.index:
                idx = timeframe_data.index.get_loc(entry_time)
                start_idx = max(0, idx - 5)
                recent_high = max(timeframe_data.iloc[start_idx:idx]['high'].max(), entry_price * 1.03)
                stop_loss = recent_high
            else:
                stop_loss = entry_price * (1 + SELL_MIN_STOP_LOSS_PERCENT / 100)
        
        max_stop = entry_price * (1 + SELL_MIN_STOP_LOSS_PERCENT / 100)
        stop_loss = max(stop_loss, max_stop)
    
    return stop_loss

def calculate_take_profit(entry_price, atr_value, position_type='long'):
    """محاسبه سطح تیک پروفیت بر اساس position_type"""
    if entry_price is None or entry_price <= 0:
        print("⚠ Warning: Invalid entry price in calculate_take_profit")
        return 0
    
    try:
        if position_type == 'long':
            if BUY_TP_METHOD == 1:  # درصد ثابت
                return entry_price * (1 + BUY_TP_PERCENT / 100)
            elif BUY_TP_METHOD == 2:  # ضریب ATR
                return entry_price + (atr_value * BUY_TP_ATR_MULTIPLIER)
            elif BUY_TP_METHOD == 3:  # درصد سیگنال
                return entry_price * (1 + BUY_TP_SIGNAL_PERCENT / 100)
            else:
                return entry_price + (atr_value * 3)
        else:  # short position
            if SELL_TP_METHOD == 1:  # درصد ثابت
                return entry_price * (1 - SELL_TP_PERCENT / 100)
            elif SELL_TP_METHOD == 2:  # ضریب ATR
                return entry_price - (atr_value * SELL_TP_ATR_MULTIPLIER)
            elif SELL_TP_METHOD == 3:  # درصد سیگنال
                return entry_price * (1 - SELL_TP_SIGNAL_PERCENT / 100)
            else:
                return entry_price - (atr_value * 3)
    except Exception as e:
        print(f"⚠ Error calculating take profit: {e}")
        return 0

def check_risk_limits(current_balance, initial_balance, daily_pnl, weekly_pnl, trade_risk):
    """بررسی اینکه آیا در محدوده ریسک مجاز هستیم"""
    return True, ""

# ==================== توابع فیلتر روند ====================

def check_trend_filter(current_time, position_type='long'):
    """بررسی اینکه آیا شرایط روند برقرار است"""
    if position_type == 'long':
        if not BUY_TREND_FILTER_ENABLED:
            return True, 1.0, "Trend filter disabled"
        
        primary_tf = BUY_TREND_PRIMARY_TF
        secondary_tf = BUY_TREND_SECONDARY_TF
        trend_condition = BUY_TREND_CONDITION
        adx_enabled = BUY_ADX_FILTER_ENABLED
        adx_threshold = BUY_ADX_THRESHOLD
    else:  # short position
        if not SELL_TREND_FILTER_ENABLED:
            return True, 1.0, "Trend filter disabled"
        
        primary_tf = SELL_TREND_PRIMARY_TF
        secondary_tf = SELL_TREND_SECONDARY_TF
        trend_condition = SELL_TREND_CONDITION
        adx_enabled = SELL_ADX_FILTER_ENABLED
        adx_threshold = SELL_ADX_THRESHOLD
    
    trend_score = 0
    reasons = []
    
    if primary_tf in timeframe_indicators:
        primary_data = timeframe_indicators[primary_tf]
        available_times = primary_data.index[primary_data.index <= current_time]
        
        if len(available_times) > 0:
            last_candle_time = available_times[-1]
            candle = primary_data.loc[last_candle_time]
            
            if 'ema_fast' in candle and 'ema_slow' in candle:
                if position_type == 'long':
                    if candle['close'] > candle['ema_slow']:
                        trend_score += 0.5
                        reasons.append(f"Price > EMA{SELL_TREND_EMA_SLOW if position_type == 'short' else BUY_TREND_EMA_SLOW} on {primary_tf}")
                    
                    if candle['ema_fast'] > candle['ema_slow']:
                        trend_score += 0.5
                        reasons.append(f"EMA{SELL_TREND_EMA_FAST if position_type == 'short' else BUY_TREND_EMA_FAST} > EMA{SELL_TREND_EMA_SLOW if position_type == 'short' else BUY_TREND_EMA_SLOW} on {primary_tf}")
                else:  # short position
                    if candle['close'] < candle['ema_slow']:
                        trend_score += 0.5
                        reasons.append(f"Price < EMA{SELL_TREND_EMA_SLOW} on {primary_tf}")
                    
                    if candle['ema_fast'] < candle['ema_slow']:
                        trend_score += 0.5
                        reasons.append(f"EMA{SELL_TREND_EMA_FAST} < EMA{SELL_TREND_EMA_SLOW} on {primary_tf}")
                
                if adx_enabled and 'adx' in candle and candle['adx'] > adx_threshold:
                    trend_score += 0.3
                    reasons.append(f"ADX > {adx_threshold} on {primary_tf}")
    
    if trend_condition in ['both_bullish', 'secondary_only'] and secondary_tf in timeframe_indicators:
        secondary_data = timeframe_indicators[secondary_tf]
        available_times = secondary_data.index[secondary_data.index <= current_time]
        
        if len(available_times) > 0:
            last_candle_time = available_times[-1]
            candle = secondary_data.loc[last_candle_time]
            
            if 'ema_fast' in candle and 'ema_slow' in candle:
                if position_type == 'long':
                    if candle['close'] > candle['ema_slow']:
                        trend_score += 0.3
                        reasons.append(f"Price > EMA{SELL_TREND_EMA_SLOW if position_type == 'short' else BUY_TREND_EMA_SLOW} on {secondary_tf}")
                    
                    if candle['ema_fast'] > candle['ema_slow']:
                        trend_score += 0.3
                        reasons.append(f"EMA{SELL_TREND_EMA_FAST if position_type == 'short' else BUY_TREND_EMA_FAST} > EMA{SELL_TREND_EMA_SLOW if position_type == 'short' else BUY_TREND_EMA_SLOW} on {secondary_tf}")
                else:  # short position
                    if candle['close'] < candle['ema_slow']:
                        trend_score += 0.3
                        reasons.append(f"Price < EMA{SELL_TREND_EMA_SLOW} on {secondary_tf}")
                    
                    if candle['ema_fast'] < candle['ema_slow']:
                        trend_score += 0.3
                        reasons.append(f"EMA{SELL_TREND_EMA_FAST} < EMA{SELL_TREND_EMA_SLOW} on {secondary_tf}")
    
    if trend_condition == 'both_bullish':
        meets_condition = trend_score >= 1.6
    elif trend_condition == 'primary_only':
        meets_condition = trend_score >= 0.8
    else:
        meets_condition = trend_score >= 0.5
    
    reason_text = " | ".join(reasons) if reasons else "No trend data"
    return meets_condition, trend_score, reason_text

# ==================== توابع امتیازدهی پیشرفته ====================

def calculate_advanced_score(rsi_value, macd_diff, trend_score, adx_value=None, position_type='long'):
    """محاسبه امتیاز ورود پیشرفته با اجزای وزندار"""
    if position_type == 'long':
        if not BUY_SCORING_SYSTEM_ENABLED:
            score = 0
            if BUY_RSI_LOWER_BOUND < rsi_value < BUY_RSI_UPPER_BOUND:
                score += 2.5
            elif rsi_value > BUY_RSI_NEUTRAL:
                score += 1
            
            if macd_diff > 0 and BUY_MACD_BULLISH:
                score += 1.5
            
            return score, {"basic_score": score}
        
        score_details = {}
        total_score = 0
        
        # امتیاز RSI
        if BUY_RSI_LOWER_BOUND < rsi_value < BUY_RSI_UPPER_BOUND:
            rsi_score = 2.5 * BUY_SCORING_WEIGHTS['rsi']
            total_score += rsi_score
            score_details['rsi_score'] = rsi_score
            score_details['rsi_condition'] = f"RSI in ({BUY_RSI_LOWER_BOUND},{BUY_RSI_UPPER_BOUND})"
        elif rsi_value > BUY_RSI_NEUTRAL:
            rsi_score = 1.0 * BUY_SCORING_WEIGHTS['rsi']
            total_score += rsi_score
            score_details['rsi_score'] = rsi_score
            score_details['rsi_condition'] = f"RSI > {BUY_RSI_NEUTRAL}"
        else:
            score_details['rsi_score'] = 0
            score_details['rsi_condition'] = "RSI not favorable"
        
        # امتیاز MACD
        macd_score = 0
        if macd_diff > 0 and BUY_MACD_BULLISH:
            macd_score = 1.5 * BUY_SCORING_WEIGHTS['macd']
            score_details['macd_condition'] = "MACD bullish"
        elif macd_diff > -0.5:
            macd_score = 0.5 * BUY_SCORING_WEIGHTS['macd']
            score_details['macd_condition'] = "MACD neutral"
        else:
            score_details['macd_condition'] = "MACD bearish"
        
        total_score += macd_score
        score_details['macd_score'] = macd_score
        
        # امتیاز روند
        if BUY_TREND_FILTER_ENABLED:
            trend_component = trend_score * BUY_SCORING_WEIGHTS['trend']
            total_score += trend_component
            score_details['trend_score'] = trend_component
        
        # امتیاز ADX
        if BUY_ADX_FILTER_ENABLED and BUY_SCORING_WEIGHTS.get('adx', 0) > 0 and adx_value is not None:
            if adx_value > BUY_ADX_THRESHOLD:
                adx_score = 0.5 * BUY_SCORING_WEIGHTS['adx']
                total_score += adx_score
                score_details['adx_score'] = adx_score
                score_details['adx_condition'] = f"ADX > {BUY_ADX_THRESHOLD}"
            else:
                score_details['adx_score'] = 0
                score_details['adx_condition'] = f"ADX <= {BUY_ADX_THRESHOLD}"
        elif BUY_ADX_FILTER_ENABLED and BUY_SCORING_WEIGHTS.get('adx', 0) > 0:
            score_details['adx_score'] = 0
            score_details['adx_condition'] = "ADX data not available"
        
        score_details['total_score'] = total_score
        
        return total_score, score_details
    else:  # short position
        if not SELL_SCORING_SYSTEM_ENABLED:
            score = 0
            if SELL_RSI_LOWER_BOUND < rsi_value < SELL_RSI_UPPER_BOUND:
                score += 2.5
            elif rsi_value < SELL_RSI_NEUTRAL:
                score += 1
            
            if macd_diff < 0 and SELL_MACD_BEARISH:
                score += 1.5
            
            return score, {"basic_score": score}
        
        score_details = {}
        total_score = 0
        
        # امتیاز RSI
        if SELL_RSI_LOWER_BOUND < rsi_value < SELL_RSI_UPPER_BOUND:
            rsi_score = 2.5 * SELL_SCORING_WEIGHTS['rsi']
            total_score += rsi_score
            score_details['rsi_score'] = rsi_score
            score_details['rsi_condition'] = f"RSI in ({SELL_RSI_LOWER_BOUND},{SELL_RSI_UPPER_BOUND})"
        elif rsi_value < SELL_RSI_NEUTRAL:
            rsi_score = 1.0 * SELL_SCORING_WEIGHTS['rsi']
            total_score += rsi_score
            score_details['rsi_score'] = rsi_score
            score_details['rsi_condition'] = f"RSI < {SELL_RSI_NEUTRAL}"
        else:
            score_details['rsi_score'] = 0
            score_details['rsi_condition'] = "RSI not favorable"
        
        # امتیاز MACD
        macd_score = 0
        if macd_diff < 0 and SELL_MACD_BEARISH:
            macd_score = 1.5 * SELL_SCORING_WEIGHTS['macd']
            score_details['macd_condition'] = "MACD bearish"
        elif macd_diff < 0.5:
            macd_score = 0.5 * SELL_SCORING_WEIGHTS['macd']
            score_details['macd_condition'] = "MACD neutral"
        else:
            score_details['macd_condition'] = "MACD bullish"
        
        total_score += macd_score
        score_details['macd_score'] = macd_score
        
        # امتیاز روند
        if SELL_TREND_FILTER_ENABLED:
            trend_component = trend_score * SELL_SCORING_WEIGHTS['trend']
            total_score += trend_component
            score_details['trend_score'] = trend_component
        
        # امتیاز ADX
        if SELL_ADX_FILTER_ENABLED and SELL_SCORING_WEIGHTS.get('adx', 0) > 0 and adx_value is not None:
            if adx_value > SELL_ADX_THRESHOLD:
                adx_score = 0.5 * SELL_SCORING_WEIGHTS['adx']
                total_score += adx_score
                score_details['adx_score'] = adx_score
                score_details['adx_condition'] = f"ADX > {SELL_ADX_THRESHOLD}"
            else:
                score_details['adx_score'] = 0
                score_details['adx_condition'] = f"ADX <= {SELL_ADX_THRESHOLD}"
        elif SELL_ADX_FILTER_ENABLED and SELL_SCORING_WEIGHTS.get('adx', 0) > 0:
            score_details['adx_score'] = 0
            score_details['adx_condition'] = "ADX data not available"
        
        score_details['total_score'] = total_score
        
        return total_score, score_details

# ==================== توابع جدید برای سیستم Fixed مانند V25 ====================

def get_exchange_time():
    try:
        if exchange:
            timestamp = exchange.milliseconds()
            return datetime.utcfromtimestamp(timestamp / 1000)
    except Exception as e:
        print(f"  [EXCHANGE TIME] Error: {e}")
    return datetime.utcnow()

def get_previous_candle_time(current_time, timeframe):
    """محاسبه زمان کندل قبلی بر اساس تایم‌فریم (مانند V25)"""
    try:
        if timeframe == "1h":
            previous_time = current_time - timedelta(hours=1)
            previous_start = datetime(previous_time.year, previous_time.month, previous_time.day, previous_time.hour, 0, 0)
            return previous_start
        elif timeframe == "4h":
            current_hour = current_time.hour
            current_block = current_hour // 4
            previous_block = (current_block - 1) % 6
            previous_start_hour = previous_block * 4
            previous_start = datetime(current_time.year, current_time.month, current_time.day, previous_start_hour, 0, 0)
            if previous_start_hour > current_hour:
                previous_start = previous_start - timedelta(days=1)
            return previous_start
        elif timeframe == "daily":
            previous_day = current_time - timedelta(days=1)
            previous_start = datetime(previous_day.year, previous_day.month, previous_day.day, 0, 0, 0)
            return previous_start
        elif timeframe == "2h":
            current_hour = current_time.hour
            current_block = current_hour // 2
            previous_block = (current_block - 1) % 12
            previous_start_hour = previous_block * 2
            previous_start = datetime(current_time.year, current_time.month, current_time.day, previous_start_hour, 0, 0)
            if previous_start_hour > current_hour:
                previous_start = previous_start - timedelta(days=1)
            return previous_start
    except Exception as e:
        print(f"  [PREVIOUS CANDLE TIME] Error: {e}")
    return None

def get_indicators_from_closed_candle_only(timeframe):
    """اندیکاتورها فقط از کندل بسته شده قبلی (منطق V25)"""
    try:
        current_time = get_exchange_time()
        previous_candle_time = get_previous_candle_time(current_time, timeframe)
        
        if previous_candle_time is None:
            return {'rsi': 50, 'macd': 0, 'macd_signal': 0, 'atr': 0, 'adx': 0, 'ema_fast': 0, 'ema_slow': 0, 'ema_signal': 0, 'close': 0}
        
        if timeframe in PREVIOUS_CANDLE_TIMES:
            if PREVIOUS_CANDLE_TIMES[timeframe] == previous_candle_time:
                if timeframe in INDICATORS_FIXED and INDICATORS_FIXED[timeframe] is not None:
                    return INDICATORS_FIXED[timeframe]
        
        PREVIOUS_CANDLE_TIMES[timeframe] = previous_candle_time
        
        print(f"  [CLOSED INDICATORS] Calculating indicators for {timeframe} previous candle at {previous_candle_time.strftime('%Y-%m-%d %H:%M')}")
        
        df = fetch_ohlcv_data(timeframe, limit=150)
        
        if len(df) < 20:
            print(f"  [CLOSED INDICATORS] Not enough data for {timeframe}: {len(df)} candles")
            return {'rsi': 50, 'macd': 0, 'macd_signal': 0, 'atr': 0, 'adx': 0, 'ema_fast': 0, 'ema_slow': 0, 'ema_signal': 0, 'close': 0}
        
        df_indicators = calculate_indicators_for_timeframe(df, 'long')
        
        if len(df_indicators) > 0:
            time_mask = df_indicators.index <= previous_candle_time
            if time_mask.any():
                last_closed_row = df_indicators[time_mask].iloc[-1]
            else:
                last_closed_row = df_indicators.iloc[-1]
            
            rsi_val = last_closed_row.get('rsi', 50)
            macd_val = last_closed_row.get('macd', 0)
            macd_signal_val = last_closed_row.get('macd_signal', 0)
            atr_val = last_closed_row.get('atr', 0)
            adx_val = last_closed_row.get('adx', 0)
            ema_fast_val = last_closed_row.get('ema_fast', 0)
            ema_slow_val = last_closed_row.get('ema_slow', 0)
            ema_signal_val = last_closed_row.get('ema_signal', 0)
            close_val = last_closed_row.get('close', 0)
            
            if pd.isna(rsi_val): rsi_val = 50
            if pd.isna(macd_val): macd_val = 0
            if pd.isna(macd_signal_val): macd_signal_val = 0
            if pd.isna(atr_val): atr_val = 0
            if pd.isna(adx_val): adx_val = 0
            if pd.isna(ema_fast_val): ema_fast_val = 0
            if pd.isna(ema_slow_val): ema_slow_val = 0
            if pd.isna(ema_signal_val): ema_signal_val = 0
            if pd.isna(close_val): close_val = 0
            
            indicators = {
                'rsi': float(rsi_val),
                'macd': float(macd_val),
                'macd_signal': float(macd_signal_val),
                'atr': float(atr_val),
                'adx': float(adx_val),
                'ema_fast': float(ema_fast_val),
                'ema_slow': float(ema_slow_val),
                'ema_signal': float(ema_signal_val),
                'close': float(close_val)
            }
            
            INDICATORS_FIXED[timeframe] = indicators
            
            if len(INDICATORS_FIXED) > MAX_CACHE_SIZE:
                oldest_key = next(iter(INDICATORS_FIXED))
                del INDICATORS_FIXED[oldest_key]
            
            CLOSE_PRICES_FIXED[f"{timeframe}_prev"] = indicators['close']
            
            if len(CLOSE_PRICES_FIXED) > MAX_CACHE_SIZE:
                oldest_key = next(iter(CLOSE_PRICES_FIXED))
                del CLOSE_PRICES_FIXED[oldest_key]
            
            print(f"  [CLOSED INDICATORS] {timeframe} - RSI: {indicators['rsi']:.1f}, "
                  f"ATR: {indicators['atr']:.2f}, MACD: {indicators['macd']:.4f}, "
                  f"Signal: {indicators['macd_signal']:.4f}, ADX: {indicators['adx']:.1f}")
            
            return indicators
        
        return {'rsi': 50, 'macd': 0, 'macd_signal': 0, 'atr': 0, 'adx': 0, 'ema_fast': 0, 'ema_slow': 0, 'ema_signal': 0, 'close': 0}
    
    except Exception as e:
        print(f"  [CLOSED INDICATORS] Error for {timeframe}: {e}")
        return {'rsi': 50, 'macd': 0, 'macd_signal': 0, 'atr': 0, 'adx': 0, 'ema_fast': 0, 'ema_slow': 0, 'ema_signal': 0, 'close': 0}

def is_new_candle_started(timeframe):
    """Check if a new candle has started for the given timeframe"""
    try:
        now = get_exchange_time()
        
        if timeframe == "1h":
            hour = now.hour
            candle_start = datetime(now.year, now.month, now.day, hour, 0, 0)
            minutes_since_start = (now - candle_start).total_seconds() / 60
            
            if minutes_since_start < 2:
                last_start_key = f'last_{timeframe}_start'
                last_grace_key = f'last_{timeframe}_grace_active'
                
                last_start = LAST_CANDLE_TIMES.get(last_start_key)
                last_grace_active = LAST_CANDLE_TIMES.get(last_grace_key, False)
                
                if last_start != candle_start or not last_grace_active:
                    current_price = fetch_current_price()
                    if current_price > 0:
                        OPEN_PRICES_FIXED[timeframe] = current_price
                        print(f"  [{timeframe.upper()}] Set OPEN price: ${current_price:.2f} at {now.strftime('%H:%M:%S')}")
                    
                    LAST_CANDLE_TIMES[last_start_key] = candle_start
                    LAST_CANDLE_TIMES[last_grace_key] = True
                    print(f"  [{timeframe.upper()}] NEW CANDLE! Start: {candle_start.strftime('%H:%M')}, Grace active")
                    return True
                return True
            else:
                LAST_CANDLE_TIMES[f'last_{timeframe}_grace_active'] = False
                return False
                
        elif timeframe == "4h":
            hour = now.hour
            start_hour = (hour // 4) * 4
            candle_start = datetime(now.year, now.month, now.day, start_hour, 0, 0)
            minutes_since_start = (now - candle_start).total_seconds() / 60
            
            if minutes_since_start < 2:
                last_start_key = f'last_{timeframe}_start'
                last_grace_key = f'last_{timeframe}_grace_active'
                
                last_start = LAST_CANDLE_TIMES.get(last_start_key)
                last_grace_active = LAST_CANDLE_TIMES.get(last_grace_key, False)
                
                if last_start != candle_start or not last_grace_active:
                    current_price = fetch_current_price()
                    if current_price > 0:
                        OPEN_PRICES_FIXED[timeframe] = current_price
                        print(f"  [{timeframe.upper()}] Set OPEN price: ${current_price:.2f}")
                    
                    LAST_CANDLE_TIMES[last_start_key] = candle_start
                    LAST_CANDLE_TIMES[last_grace_key] = True
                    print(f"  [{timeframe.upper()}] NEW CANDLE! Start: {candle_start.strftime('%H:%M')}")
                    return True
                return True
            else:
                LAST_CANDLE_TIMES[f'last_{timeframe}_grace_active'] = False
                return False
        
        elif timeframe == "daily":
            candle_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            hours_since_start = (now - candle_start).total_seconds() / 3600
            
            if hours_since_start < 2:
                last_start_key = f'last_{timeframe}_start'
                last_grace_key = f'last_{timeframe}_grace_active'
                
                last_start = LAST_CANDLE_TIMES.get(last_start_key)
                last_grace_active = LAST_CANDLE_TIMES.get(last_grace_key, False)
                
                if last_start != candle_start or not last_grace_active:
                    current_price = fetch_current_price()
                    if current_price > 0:
                        OPEN_PRICES_FIXED[timeframe] = current_price
                        print(f"  [{timeframe.upper()}] Set OPEN price: ${current_price:.2f}")
                    
                    LAST_CANDLE_TIMES[last_start_key] = candle_start
                    LAST_CANDLE_TIMES[last_grace_key] = True
                    print(f"  [{timeframe.upper()}] NEW CANDLE! Date: {candle_start.strftime('%Y-%m-%d')}")
                    return True
                return True
            else:
                LAST_CANDLE_TIMES[f'last_{timeframe}_grace_active'] = False
                return False
                
        return False
    except Exception as e:
        print(f"  [is_new_candle_started ERROR] {e}")
        return False

# ==================== توابع سیگنال ورود ====================

def check_entry_signal_v2(current_time, entry_timeframes_list, position_type='long'):
    """منطق سیگنال ورود V2.1 با استفاده از اندیکاتورهای Fixed"""
    best_score = 0
    best_rsi_value = 50
    best_macd_value = 0
    best_macd_signal_value = 0
    best_atr_value = 0
    best_entry_price = 0
    best_timeframe = None
    all_scores = []
    
    for entry_tf in entry_timeframes_list:
        if is_new_candle_started(entry_tf):
            print(f"  [ENTRY CHECK] New {entry_tf} candle started, checking entry conditions")
            
            indicators = get_indicators_from_closed_candle_only(entry_tf)
            
            rsi_value = indicators.get('rsi', 50)
            macd_value = indicators.get('macd', 0)
            macd_signal_value = indicators.get('macd_signal', 0)
            atr_value = indicators.get('atr', 0)
            entry_price = indicators.get('close', 0)
            
            score = 0.0
            
            if position_type == 'long':
                if BUY_RSI_LOWER_BOUND < rsi_value < BUY_RSI_UPPER_BOUND:
                    score += 2.5
                elif rsi_value > BUY_RSI_NEUTRAL:
                    score += 1
                
                if macd_value > macd_signal_value and BUY_MACD_BULLISH:
                    score += 1.5
            else:  # short position
                if SELL_RSI_LOWER_BOUND < rsi_value < SELL_RSI_UPPER_BOUND:
                    score += 2.5
                elif rsi_value < SELL_RSI_NEUTRAL:
                    score += 1
                
                if macd_value < macd_signal_value and SELL_MACD_BEARISH:
                    score += 1.5
            
            all_scores.append((score, entry_tf, rsi_value, macd_value, macd_signal_value))
            
            if score > best_score:
                best_score = score
                best_rsi_value = rsi_value
                best_macd_value = macd_value
                best_macd_signal_value = macd_signal_value
                best_atr_value = atr_value
                best_entry_price = entry_price
                best_timeframe = entry_tf
    
    if all_scores:
        avg_score = sum([s[0] for s in all_scores]) / len(all_scores)
        return avg_score, best_rsi_value, best_macd_value, best_macd_signal_value, best_atr_value, best_entry_price, best_timeframe, all_scores, f"Score: {avg_score:.1f} (Fixed from closed candle)", position_type
    else:
        return 0, 50, 0, 0, 0, 0, None, [], "No valid signals (No new candle)", position_type

def check_entry_signal_v3(current_time, entry_timeframes_list, position_type='long'):
    """منطق سیگنال ورود V3.0 با استفاده از اندیکاتورهای Fixed"""
    if not is_within_trading_hours(current_time):
        return 0, 50, 0, 0, 0, 0, None, [], "Outside trading hours", position_type
    
    best_score = 0
    best_rsi_value = 50
    best_macd_value = 0
    best_macd_signal_value = 0
    best_atr_value = 0
    best_entry_price = 0
    best_timeframe = None
    all_scores = []
    best_score_details = {}
    
    trend_ok, trend_score, trend_reason = check_trend_filter(current_time, position_type=position_type)
    if position_type == 'long' and not trend_ok and BUY_TREND_FILTER_ENABLED:
        return 0, 50, 0, 0, 0, 0, None, [], f"Trend filter failed: {trend_reason}", position_type
    elif position_type == 'short' and not trend_ok and SELL_TREND_FILTER_ENABLED:
        return 0, 50, 0, 0, 0, 0, None, [], f"Trend filter failed: {trend_reason}", position_type
    
    for entry_tf in entry_timeframes_list:
        if is_new_candle_started(entry_tf):
            print(f"  [ENTRY CHECK] New {entry_tf} candle started, checking entry conditions")
            
            indicators = get_indicators_from_closed_candle_only(entry_tf)
            
            rsi_value = indicators.get('rsi', 50)
            macd_value = indicators.get('macd', 0)
            macd_signal_value = indicators.get('macd_signal', 0)
            atr_value = indicators.get('atr', 0)
            entry_price = indicators.get('close', 0)
            macd_diff = macd_value - macd_signal_value
            
            adx_value = None
            if position_type == 'long' and BUY_ADX_FILTER_ENABLED:
                adx_value = indicators.get('adx', 0)
            elif position_type == 'short' and SELL_ADX_FILTER_ENABLED:
                adx_value = indicators.get('adx', 0)
            
            score, score_details = calculate_advanced_score(
                rsi_value, macd_diff, trend_score, 
                adx_value=adx_value, position_type=position_type
            )
            
            all_scores.append((score, entry_tf, rsi_value, macd_value, macd_signal_value, score_details))
            
            if score > best_score:
                best_score = score
                best_rsi_value = rsi_value
                best_macd_value = macd_value
                best_macd_signal_value = macd_signal_value
                best_atr_value = atr_value
                best_entry_price = entry_price
                best_timeframe = entry_tf
                best_score_details = score_details
    
    if all_scores:
        avg_score = sum([s[0] for s in all_scores]) / len(all_scores)
        
        if avg_score < MIN_TOTAL_SCORE:
            return 0, best_rsi_value, best_macd_value, best_macd_signal_value, best_atr_value, best_entry_price, best_timeframe, all_scores, f"Score {avg_score:.1f} < minimum {MIN_TOTAL_SCORE}", position_type
        
        reason_parts = []
        if best_score_details:
            for key, value in best_score_details.items():
                if isinstance(value, (int, float)):
                    reason_parts.append(f"{key}: {value:.2f}")
                else:
                    reason_parts.append(f"{key}: {value}")
        
        reason = f"Score: {avg_score:.1f} (Fixed from closed candle)"
        if reason_parts:
            reason += " | " + " | ".join(reason_parts[:3])
        
        return avg_score, best_rsi_value, best_macd_value, best_macd_signal_value, best_atr_value, best_entry_price, best_timeframe, all_scores, reason, position_type
    else:
        return 0, 50, 0, 0, 0, 0, None, [], "No valid signals (No new candle)", position_type

def check_entry_signal(current_time, entry_timeframes_list, position_type='long'):
    """تابع اصلی سیگنال ورود"""
    if position_type == 'long':
        if BUY_TREND_FILTER_ENABLED or BUY_SCORING_SYSTEM_ENABLED:
            return check_entry_signal_v3(current_time, entry_timeframes_list, 'long')
        else:
            return check_entry_signal_v2(current_time, entry_timeframes_list, 'long')
    else:  # short position
        if SELL_TREND_FILTER_ENABLED or SELL_SCORING_SYSTEM_ENABLED:
            return check_entry_signal_v3(current_time, entry_timeframes_list, 'short')
        else:
            return check_entry_signal_v2(current_time, entry_timeframes_list, 'short')

# ==================== توابع صرافی ====================

def initialize_exchange():
    global exchange
    
    try:
        exchange_class = getattr(ccxt, EXCHANGE_NAME)
    except AttributeError:
        print(f"صرافی {EXCHANGE_NAME} در کتابخانه ccxt پشتیبانی نمی‌شود")
        return False
    
    config = {
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'timeout': 30000,
        'options': {
            'defaultType': 'future',
            'createMarketBuyOrderRequiresPrice': False,
            'defaultMarginMode': 'isolated',
            'defaultPositionSide': 'LONG',
        }
    }
    
    exchange = exchange_class(config)
    
    try:
        exchange.load_markets()
        print(f"✅ Connected to {EXCHANGE_NAME} exchange successfully")
        
        if LEVERAGE > 1:
            try:
                exchange.set_leverage(LEVERAGE, SYMBOL, params={'positionSide': 'LONG'})
                print(f"✅ Leverage set to {LEVERAGE}x for {SYMBOL}")
            except Exception as e:
                print(f"⚠ Could not set leverage: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize exchange: {e}")
        return False

def get_account_balance():
    """دریافت موجودی واقعی از صرافی"""
    global balance, initial_capital, initial_capital_set
    
    try:
        if exchange:
            balance_info = exchange.fetch_balance()
            
            if 'USDT' in balance_info['total']:
                balance = balance_info['total']['USDT']
            elif 'free' in balance_info and 'USDT' in balance_info['free']:
                balance = balance_info['free']['USDT']
            else:
                for key in ['total', 'free', 'used']:
                    if key in balance_info and 'USDT' in balance_info[key]:
                        balance = balance_info[key]['USDT']
                        break
            
            if not initial_capital_set and balance > 0:
                initial_capital = balance
                initial_capital_set = True
                print(f"💰 Initial capital set to: ${initial_capital:.2f}")
            
            return balance
    except Exception as e:
        print(f"⚠ Error fetching balance: {e}")
    
    return balance

def fetch_current_price():
    try:
        if exchange:
            ticker = exchange.fetch_ticker(SYMBOL)
            return ticker['last']
    except Exception as e:
        print(f"⚠ Error fetching price: {e}")
    return 0

def fetch_ohlcv_data(timeframe, limit=150):
    try:
        if timeframe == "daily":
            tf = "1d"
        elif timeframe == "4h":
            tf = "4h"
        elif timeframe == "2h":
            tf = "2h"
        else:
            tf = "1h"
        
        raw = exchange.fetch_ohlcv(SYMBOL, tf, limit=limit)
        df = pd.DataFrame(raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['datetime'] = df['datetime'].dt.tz_localize(None)
        df = df.set_index('datetime').sort_index()
        return df
    except Exception as e:
        print(f"  [DATA FETCH] Error fetching {timeframe} data: {e}")
        return pd.DataFrame()

# ==================== توابع مدیریت وضعیت ====================

def save_state():
    """ذخیره وضعیت"""
    state = {
        'in_position': in_position,
        'entry_price': entry_price,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'position_open_time': position_open_time.isoformat() if position_open_time else None,
        'position_size': position_size,
        'balance': balance,
        'initial_capital': initial_capital,
        'initial_capital_set': initial_capital_set,
        'trade_counter': trade_counter,
        'trades': trades[-50:],
        'position_type': position_type,
        'total_pnl': total_pnl,
        'equity_history': equity_history[-100:],
        'signals': signals[-100:],
        'last_update': datetime.utcnow().isoformat()
    }
    
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"  [STATE] Error saving: {e}")
        return False

def load_state():
    """بارگذاری وضعیت"""
    global in_position, entry_price, tp_price, sl_price, position_open_time
    global position_size, balance, initial_capital, initial_capital_set
    global trade_counter, trades, position_type, total_pnl
    global equity_history, signals
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            
            in_position = state.get('in_position', False)
            entry_price = state.get('entry_price', 0.0)
            tp_price = state.get('tp_price', 0.0)
            sl_price = state.get('sl_price', 0.0)
            position_size = state.get('position_size', 0.0)
            balance = state.get('balance', 0.0)
            initial_capital = state.get('initial_capital', 0.0)
            initial_capital_set = state.get('initial_capital_set', False)
            trade_counter = state.get('trade_counter', 0)
            trades = state.get('trades', [])
            position_type = state.get('position_type', 'long')
            total_pnl = state.get('total_pnl', 0.0)
            equity_history = state.get('equity_history', [])
            signals = state.get('signals', [])
            
            pos_time = state.get('position_open_time')
            if pos_time:
                position_open_time = datetime.fromisoformat(pos_time.replace('Z', '+00:00'))
            
            print(f"  [STATE] Loaded: Position={in_position}, Balance=${balance:.2f}")
            print(f"  [STATE] Trades loaded: {len(trades)}")
            return True
            
        except Exception as e:
            print(f"  [STATE] Error loading: {e}")
    
    print(f"  [STATE] No state file found, using defaults")
    return False

# ==================== تابع محاسبه Score برای نمایش ====================

def calculate_score_for_position_type(position_type='long'):
    """محاسبه امتیاز کلی برای یک position_type با استفاده از Fixed indicators"""
    current_time = get_exchange_time()
    
    if current_time.tzinfo is not None:
        current_time_naive = current_time.replace(tzinfo=None)
    else:
        current_time_naive = current_time
    
    if position_type == 'long':
        entry_timeframes_list = BUY_ENTRY_TIMEFRAMES
    else:  # short position
        entry_timeframes_list = SELL_ENTRY_TIMEFRAMES
    
    all_scores = []
    best_score = 0
    best_rsi = 50
    best_tf = None
    best_info = ""
    
    trend_ok, trend_score, trend_reason = check_trend_filter(current_time_naive, position_type=position_type)
    
    if position_type == 'long' and not trend_ok and BUY_TREND_FILTER_ENABLED:
        return 0, f"Trend filter failed: {trend_reason}", "No TF"
    elif position_type == 'short' and not trend_ok and SELL_TREND_FILTER_ENABLED:
        return 0, f"Trend filter failed: {trend_reason}", "No TF"
    
    for entry_tf in entry_timeframes_list:
        indicators = get_indicators_from_closed_candle_only(entry_tf)
        
        rsi_value = indicators.get('rsi', 50)
        macd_value = indicators.get('macd', 0)
        macd_signal_value = indicators.get('macd_signal', 0)
        macd_diff = macd_value - macd_signal_value
        atr_value = indicators.get('atr', 0)
        
        adx_value = None
        if position_type == 'long' and BUY_ADX_FILTER_ENABLED:
            adx_value = indicators.get('adx', 0)
        elif position_type == 'short' and SELL_ADX_FILTER_ENABLED:
            adx_value = indicators.get('adx', 0)
        
        score, score_details = calculate_advanced_score(
            rsi_value, macd_diff, trend_score, adx_value, position_type
        )
        
        all_scores.append(score)
        
        if score > best_score:
            best_score = score
            best_rsi = rsi_value
            best_tf = entry_tf
            best_info = f"RSI: {rsi_value:.1f}, MACD: {macd_diff:.4f}, ATR: {atr_value:.2f}"
    
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        info = f"Avg Score: {avg_score:.1f} (from {len(all_scores)} TFs, FIXED FROM CLOSED CANDLE) | {best_info}"
        return avg_score, info, best_tf
    else:
        return 0, "No valid data", "No TF"

# ==================== توابع معاملاتی ====================

def calculate_position_size(entry_price):
    """محاسبه اندازه موقعیت"""
    global balance
    
    if balance <= 0:
        get_account_balance()
    
    if balance <= 0:
        return 0, 0
    
    try:
        market = exchange.market(SYMBOL)
        contract_size = float(market['contractSize']) if 'contractSize' in market else 0.01
        min_amount = market['limits']['amount']['min']
        
        print(f"  [MARKET INFO] Contract size: {contract_size}, Min contracts: {min_amount}")
        
        investment = balance * POSITION_SIZE_PCT
        
        contracts_needed = (investment * LEVERAGE) / (entry_price * contract_size)
        
        contracts = max(min_amount, round(contracts_needed))
        contracts = int(contracts)
        
        position_size_eth = contracts * contract_size
        
        print(f"  [POSITION SIZE] Investment: ${investment:.2f}, Contracts: {contracts}, ETH Amount: {position_size_eth:.6f} ETH")
        return contracts, position_size_eth
        
    except Exception as e:
        print(f"⚠ Error calculating position size: {e}")
        
        investment = balance * POSITION_SIZE_PCT
        contracts_needed = (investment * LEVERAGE) / entry_price
        
        contracts = max(1, round(contracts_needed))
        contract_size = 0.01
        position_size_eth = contracts * contract_size
        
        return contracts, position_size_eth

def open_position(position_type_param, entry_price_candle, score, timeframe):
    """باز کردن پوزیشن"""
    global in_position, entry_price, tp_price, sl_price, position_open_time
    global position_size, balance, trade_counter, trades, position_type
    global total_pnl, initial_capital_set, initial_capital
    
    if in_position:
        print("⚠ Already in a position")
        return False
    
    get_account_balance()
    
    if balance <= 0:
        print("❌ No balance available")
        return False

    try:
        if entry_price_candle is None or entry_price_candle <= 0:
            current_price = fetch_current_price()
            if current_price <= 0:
                print("❌ Invalid entry price and current price")
                return False
            entry_price_candle = current_price
            print(f"⚠ Using current price as entry price: ${current_price:.2f}")
        
        contracts_calc, position_size_eth_calc = calculate_position_size(entry_price_candle)
        
        if contracts_calc <= 0 or position_size_eth_calc <= 0:
            print("❌ Invalid position size")
            return False
        
        current_price = fetch_current_price()
        if current_price <= 0:
            print("❌ Invalid current price")
            return False
        
        side = 'buy' if position_type_param == 'long' else 'sell'
        position_side = 'LONG' if position_type_param == 'long' else 'SHORT'
        
        amount_precise = exchange.amount_to_precision(SYMBOL, float(contracts_calc))
        amount_float = float(amount_precise)
        
        print(f"  [ORDER] Creating {side} order for {amount_float} contracts ({position_size_eth_calc:.6f} ETH) at ~${current_price:.2f}")
        
        order = None
        try:
            if side == 'buy':
                cost = position_size_eth_calc * current_price
                order = exchange.create_order(
                    symbol=SYMBOL,
                    type='market',
                    side=side,
                    amount=amount_float,
                    params={
                        'cost': cost,
                        'positionSide': position_side  
                    }
                )
            else:
                order = exchange.create_order(
                    symbol=SYMBOL,
                    type='market',
                    side=side,
                    amount=amount_float,
                    params={'positionSide': position_side}  
                )
                
            print(f"✅ Order placed: {order['id']}")
            
            entry_price_final = None
            
            if order and 'price' in order and order['price'] is not None:
                entry_price_final = order['price']
                print(f"  [ORDER] Using order price: ${entry_price_final:.2f}")
            elif order and 'average' in order and order['average'] is not None:
                entry_price_final = order['average']
                print(f"  [ORDER] Using order average: ${entry_price_final:.2f}")
            elif order and 'info' in order and 'price' in order['info'] and order['info']['price'] is not None:
                entry_price_final = float(order['info']['price'])
                print(f"  [ORDER] Using order info price: ${entry_price_final:.2f}")
            else:
                entry_price_final = current_price
                print(f"  [ORDER] Using current price as fallback: ${entry_price_final:.2f}")
            
            if entry_price_final is None or entry_price_final <= 0:
                print("⚠ Warning: Invalid entry price from order, using current price")
                entry_price_final = current_price
                
        except Exception as e:
            print(f"❌ Error placing market order: {e}")
            
            try:
                print("🔄 Trying limit order as fallback...")
                if side == 'buy':
                    limit_price = current_price * 1.002
                else:
                    limit_price = current_price * 0.998
                    
                order = exchange.create_order(
                    symbol=SYMBOL,
                    type='limit',
                    side=side,
                    amount=amount_float,
                    price=limit_price,
                    params={'positionSide': position_side}
                )
                print(f"✅ Limit order placed: {order['id']}")
                
                for _ in range(10):
                    time.sleep(1)
                    order_status = exchange.fetch_order(order['id'], SYMBOL)
                    if order_status['status'] == 'closed':
                        print("✅ Order filled")
                        if 'price' in order_status and order_status['price'] is not None:
                            entry_price_final = order_status['price']
                        elif 'average' in order_status and order_status['average'] is not None:
                            entry_price_final = order_status['average']
                        else:
                            entry_price_final = limit_price
                        break
                    elif order_status['status'] == 'canceled':
                        print("❌ Order canceled")
                        return False
                else:
                    print("⚠ Order not filled within timeout, canceling...")
                    try:
                        exchange.cancel_order(order['id'], SYMBOL)
                    except:
                        pass
                    return False
                    
            except Exception as e2:
                print(f"❌ Error placing limit order: {e2}")
                return False
        
        if entry_price_final is None or entry_price_final <= 0:
            print("⚠ Final entry price is invalid, using current price")
            entry_price_final = current_price
        
        atr_value = 0
        indicators = get_indicators_from_closed_candle_only(timeframe)
        if indicators:
            atr_value = indicators.get('atr', 0)
        
        in_position = True
        entry_price = float(entry_price_final)
        position_type = position_type_param
        position_size = position_size_eth_calc
        position_open_time = datetime.utcnow()
        
        tp_price = calculate_take_profit(entry_price, atr_value, position_type_param)
        sl_price = calculate_stop_loss(entry_price, atr_value, datetime.utcnow(), 
                                      timeframe_indicators.get(timeframe, pd.DataFrame()), 
                                      position_type_param)
        
        trade_counter += 1
        
        trade_data = {
            'trade_number': trade_counter,
            'type': 'BUY' if position_type_param == 'long' else 'SELL_SHORT',
            'time': datetime.utcnow(),
            'price': entry_price,
            'contracts': contracts_calc,
            'amount_eth': position_size_eth_calc,
            'position_type': position_type_param,
            'score': score,
            'timeframe': timeframe,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'balance_before': balance,
            'investment': balance * POSITION_SIZE_PCT,
            'formatted_log': f"***********{'BUY' if position_type_param == 'long' else 'SELL_SHORT'} NO {trade_counter}***********\n"
                            f"Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"Price: ${entry_price:.2f}\n"
                            f"Contracts: {contracts_calc}\n"
                            f"ETH Amount: {position_size_eth_calc:.6f} ETH\n"
                            f"Position Type: {position_type_param.upper()}\n"
                            f"Score: {score:.1f}\n"
                            f"Timeframe: {timeframe}\n"
                            f"TP: ${tp_price:.2f}\n"
                            f"SL: ${sl_price:.2f}\n"
                            f"Investment: ${balance * POSITION_SIZE_PCT:.2f}\n"
                            f"Balance: ${balance:.2f}\n"
                            f"*******************************"
        }
        
        trades.append(trade_data)
        
        print(f"\n{'='*60}")
        print(f"✅ OPENED {position_type_param.upper()} POSITION #{trade_counter}")
        print(f"{'='*60}")
        print(f"Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Price: ${entry_price:.2f}")
        print(f"Contracts: {contracts_calc}")
        print(f"ETH Amount: {position_size_eth_calc:.6f} ETH")
        print(f"Position Type: {position_type_param.upper()}")
        print(f"Score: {score:.1f}")
        print(f"Timeframe: {timeframe}")
        if tp_price and tp_price > 0:
            print(f"TP: ${tp_price:.2f} (+{((tp_price/entry_price)-1)*100:.1f}%)")
        if sl_price and sl_price > 0:
            print(f"SL: ${sl_price:.2f} ({((sl_price/entry_price)-1)*100:.1f}%)")
        print(f"ATR: {atr_value:.2f}")
        print(f"Investment: ${balance * POSITION_SIZE_PCT:.2f}")
        print(f"Leverage: {LEVERAGE}x")
        print(f"Balance: ${balance:.2f}")
        print(f"{'='*60}\n")
        
        balance = balance - (balance * POSITION_SIZE_PCT)
        
        save_state()
        return True
        
    except Exception as e:
        print(f"❌ Error in open_position: {e}")
        return False

def close_position(exit_price=None, reason=""):
    """بستن پوزیشن"""
    global in_position, entry_price, tp_price, sl_price, position_open_time
    global position_size, balance, trade_counter, trades, total_pnl
    
    if not in_position or position_size <= 0:
        return False
    
    if exit_price is None:
        exit_price = fetch_current_price()
    
    try:
        close_side = 'sell' if position_type == 'long' else 'buy'
        
        market = exchange.market(SYMBOL)
        contract_size = float(market['contractSize']) if 'contractSize' in market else 0.01
        contracts_to_close = int(position_size / contract_size)
        
        amount_precise = exchange.amount_to_precision(SYMBOL, float(contracts_to_close))
        amount_float = float(amount_precise)
        
        order = exchange.create_order(
            symbol=SYMBOL,
            type='market',
            side=close_side,
            amount=amount_float
        )
        print(f"✅ Close order placed: {order}")
        
        if 'price' in order:
            exit_price = order['price']
        elif 'average' in order:
            exit_price = order['average']
    except Exception as e:
        print(f"❌ Error placing close order: {e}")
        return False
    
    if position_type == 'long':
        sale_proceeds = position_size * exit_price
        investment_amount = position_size * entry_price
        pnl = sale_proceeds - investment_amount
    else:  # short position
        close_value = abs(position_size) * exit_price
        investment_amount = abs(position_size) * entry_price
        pnl = investment_amount - close_value
    
    pnl_percent = (pnl / investment_amount) * 100 if investment_amount > 0 else 0
    
    balance = balance + pnl + investment_amount
    total_pnl += pnl
    
    holding_hours = (datetime.utcnow() - position_open_time).total_seconds() / 3600 if position_open_time else 0
    
    trade_counter += 1
    
    market = exchange.market(SYMBOL)
    contract_size = float(market['contractSize']) if 'contractSize' in market else 0.01
    contracts_closed = int(position_size / contract_size)
    
    trade_data = {
        'trade_number': trade_counter,
        'type': 'SELL' if position_type == 'long' else 'BUY_COVER',
        'time': datetime.utcnow(),
        'price': exit_price,
        'contracts': contracts_closed,
        'amount_eth': position_size,
        'pnl': pnl,
        'pnl_percent': pnl_percent,
        'reason': reason,
        'holding_hours': holding_hours,
        'position_type': position_type,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'investment_amount': investment_amount,
        'balance_before': balance - pnl - investment_amount,
        'balance_after': balance,
        'formatted_log': f"***********{'SELL' if position_type == 'long' else 'BUY_COVER'} NO {trade_counter}***********\n"
                        f"Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Exit Price: ${exit_price:.2f}\n"
                        f"Entry Price: ${entry_price:.2f}\n"
                        f"Contracts: {contracts_closed}\n"
                        f"ETH Amount: {position_size:.6f} ETH\n"
                        f"P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)\n"
                        f"Reason: {reason}\n"
                        f"Holding Hours: {holding_hours:.1f}\n"
                        f"Position Type: {position_type.upper()}\n"
                        f"Investment: ${investment_amount:.2f}\n"
                        f"New Balance: ${balance:.2f}\n"
                        f"*******************************"
    }
    
    trades.append(trade_data)
    
    print(f"\n{'='*60}")
    print(f"✅ CLOSED {position_type.upper()} POSITION #{trade_counter}")
    print(f"{'='*60}")
    print(f"Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exit Price: ${exit_price:.2f}")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Contracts: {contracts_closed}")
    print(f"ETH Amount: {position_size:.6f} ETH")
    print(f"P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
    print(f"Reason: {reason}")
    print(f"Holding Hours: {holding_hours:.1f}")
    print(f"Position Type: {position_type.upper()}")
    print(f"Investment: ${investment_amount:.2f}")
    print(f"New Balance: ${balance:.2f}")
    print(f"{'='*60}\n")
    
    in_position = False
    entry_price = 0.0
    tp_price = 0.0
    sl_price = 0.0
    position_open_time = None
    position_size = 0.0
    position_type = 'long'
    
    save_state()
    return True

# ==================== تابع اصلی به‌روزرسانی اندیکاتورها ====================

def update_all_indicators():
    """به‌روزرسانی اندیکاتورها برای تمام تایم‌فریم‌های مورد نیاز"""
    global timeframe_indicators
    
    all_timeframes = set(
        BUY_ENTRY_TIMEFRAMES + BUY_EXIT_TIMEFRAMES + BUY_EXIT_ATR_TIMEFRAMES +
        SELL_ENTRY_TIMEFRAMES + SELL_EXIT_TIMEFRAMES + SELL_EXIT_ATR_TIMEFRAMES +
        [BUY_TREND_PRIMARY_TF, BUY_TREND_SECONDARY_TF, SELL_TREND_PRIMARY_TF, SELL_TREND_SECONDARY_TF, '1h']
    )
    
    for tf in all_timeframes:
        try:
            df = fetch_ohlcv_data(tf, limit=200)
            if len(df) > 0:
                timeframe_indicators[tf] = calculate_indicators_for_timeframe(df, 'long')
                print(f"  [INDICATORS] Updated {tf}: {len(timeframe_indicators[tf])} candles")
        except Exception as e:
            print(f"  [INDICATORS] Error updating {tf}: {e}")

# ==================== توابع جدید برای مدیریت بهتر ====================

def cleanup_cache():
    """پاک‌سازی cache برای جلوگیری از رشد بی‌رویه"""
    try:
        for cache_dict in [INDICATORS_FIXED, OPEN_PRICES_FIXED, CLOSE_PRICES_FIXED, 
                          LAST_CANDLE_TIMES, PREVIOUS_CANDLE_TIMES]:
            if len(cache_dict) > MAX_CACHE_SIZE:
                keys_to_remove = list(cache_dict.keys())[:len(cache_dict) - MAX_CACHE_SIZE]
                for key in keys_to_remove:
                    del cache_dict[key]
        
        global trades
        if len(trades) > 100:
            trades = trades[-100:]
        
        global signals
        if len(signals) > 100:
            signals = signals[-100:]
            
        print(f"  [CLEANUP] Cache cleaned. INDICATORS_FIXED: {len(INDICATORS_FIXED)} items")
    except Exception as e:
        print(f"  [CLEANUP] Error: {e}")

# ==================== تابع اصلی Trading Loop ====================

def trading_loop():
    """حلقه معاملاتی اصلی بدون GUI"""
    print("🔄 Starting HEADLESS trading loop...")
    
    last_indicator_update = datetime.utcnow()
    error_count = 0
    max_errors = 10
    
    while True:
        try:
            current_time = datetime.utcnow()
            print(f"\n⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # پاک‌سازی دوره‌ای cache
            if current_time.minute % 30 == 0:
                cleanup_cache()
            
            # به‌روزرسانی اندیکاتورها هر 5 دقیقه
            if (current_time - last_indicator_update).total_seconds() > 300:
                print("🔄 Updating indicators...")
                update_all_indicators()
                last_indicator_update = current_time
            
            # Update account information
            get_account_balance()
            current_price = fetch_current_price()
            print(f"💰 Balance: ${balance:.2f}, Price: ${current_price:.2f}")
            
            # انتخاب تایم‌فریم‌ها بر اساس حالت معاملاتی
            if in_position:
                if position_type == 'long':
                    entry_tfs = BUY_ENTRY_TIMEFRAMES
                    exit_tfs = BUY_EXIT_TIMEFRAMES
                    exit_atr_tfs = BUY_EXIT_ATR_TIMEFRAMES
                else:  # short position
                    entry_tfs = SELL_ENTRY_TIMEFRAMES
                    exit_tfs = SELL_EXIT_TIMEFRAMES
                    exit_atr_tfs = SELL_EXIT_ATR_TIMEFRAMES
            elif TRADING_MODE == 'BOTH':
                entry_tfs = list(set(BUY_ENTRY_TIMEFRAMES + SELL_ENTRY_TIMEFRAMES))
                exit_tfs = list(set(BUY_EXIT_TIMEFRAMES + SELL_EXIT_TIMEFRAMES))
                exit_atr_tfs = list(set(BUY_EXIT_ATR_TIMEFRAMES + SELL_EXIT_ATR_TIMEFRAMES))
            else:
                if TRADING_MODE == 'BUY':
                    entry_tfs = BUY_ENTRY_TIMEFRAMES
                    exit_tfs = BUY_EXIT_TIMEFRAMES
                    exit_atr_tfs = BUY_EXIT_ATR_TIMEFRAMES
                else:  # SELL
                    entry_tfs = SELL_ENTRY_TIMEFRAMES
                    exit_tfs = SELL_EXIT_TIMEFRAMES
                    exit_atr_tfs = SELL_EXIT_ATR_TIMEFRAMES
            
            # ==================== منطق خروج ====================
            if in_position:
                take_profit_hit = False
                if tp_price > 0:
                    if position_type == 'long' and current_price >= tp_price:
                        take_profit_hit = True
                        exit_reason = f"Take Profit hit at {tp_price:.2f}"
                    elif position_type == 'short' and current_price <= tp_price:
                        take_profit_hit = True
                        exit_reason = f"Take Profit hit at {tp_price:.2f}"
                
                if take_profit_hit:
                    print(f"🎯 Take profit signal detected!")
                    close_position(exit_price=tp_price, reason=exit_reason)
                elif sl_price > 0:
                    if position_type == 'long' and current_price <= sl_price:
                        print(f"🛑 Stop loss hit!")
                        close_position(exit_price=sl_price, reason=f"Stop loss at {sl_price:.2f}")
                    elif position_type == 'short' and current_price >= sl_price:
                        print(f"🛑 Stop loss hit!")
                        close_position(exit_price=sl_price, reason=f"Stop loss at {sl_price:.2f}")
                
                # نمایش وضعیت فعلی
                if position_type == 'long':
                    current_pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    current_pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                print(f"📊 Position: {position_type.upper()}, Entry: ${entry_price:.2f}, Current: ${current_price:.2f}, P&L: {current_pnl_pct:.2f}%")
            
            # ==================== منطق ورود ====================
            if not in_position:
                # در حالت BOTH، هم سیگنال long و هم short را بررسی می‌کنیم
                if TRADING_MODE == 'BOTH':
                    long_score, long_rsi_value, long_macd_value, long_macd_signal_value, long_atr_value, \
                    long_entry_price, long_best_tf, long_all_scores, long_entry_reason, _ = check_entry_signal(
                        current_time, BUY_ENTRY_TIMEFRAMES, 'long'
                    )
                    
                    short_score, short_rsi_value, short_macd_value, short_macd_signal_value, short_atr_value, \
                    short_entry_price, short_best_tf, short_all_scores, short_entry_reason, _ = check_entry_signal(
                        current_time, SELL_ENTRY_TIMEFRAMES, 'short'
                    )
                    
                    # انتخاب بهترین سیگنال
                    if long_score >= ENTRY_SCORE_THRESHOLD and short_score >= ENTRY_SCORE_THRESHOLD:
                        if long_score >= short_score:
                            score, rsi_value, macd_value, macd_signal_value, atr_value = long_score, long_rsi_value, long_macd_value, long_macd_signal_value, long_atr_value
                            entry_price_candle, best_tf, entry_reason = long_entry_price, long_best_tf, long_entry_reason
                            signal_position_type = 'long'
                        else:
                            score, rsi_value, macd_value, macd_signal_value, atr_value = short_score, short_rsi_value, short_macd_value, short_macd_signal_value, short_atr_value
                            entry_price_candle, best_tf, entry_reason = short_entry_price, short_best_tf, short_entry_reason
                            signal_position_type = 'short'
                    elif long_score >= ENTRY_SCORE_THRESHOLD:
                        score, rsi_value, macd_value, macd_signal_value, atr_value = long_score, long_rsi_value, long_macd_value, long_macd_signal_value, long_atr_value
                        entry_price_candle, best_tf, entry_reason = long_entry_price, long_best_tf, long_entry_reason
                        signal_position_type = 'long'
                    elif short_score >= ENTRY_SCORE_THRESHOLD:
                        score, rsi_value, macd_value, macd_signal_value, atr_value = short_score, short_rsi_value, short_macd_value, short_macd_signal_value, short_atr_value
                        entry_price_candle, best_tf, entry_reason = short_entry_price, short_best_tf, short_entry_reason
                        signal_position_type = 'short'
                    else:
                        score = 0
                else:
                    # حالت‌های BUY یا SELL
                    if TRADING_MODE == 'BUY':
                        signal_position_type = 'long'
                        entry_tfs_for_signal = BUY_ENTRY_TIMEFRAMES
                    else:  # SELL
                        signal_position_type = 'short'
                        entry_tfs_for_signal = SELL_ENTRY_TIMEFRAMES
                    
                    score, rsi_value, macd_value, macd_signal_value, atr_value, \
                    entry_price_candle, best_tf, all_scores, entry_reason, _ = check_entry_signal(
                        current_time, entry_tfs_for_signal, signal_position_type
                    )
                
                # بررسی شرایط ریسک
                risk_ok, risk_reason = check_risk_limits(balance, initial_capital, 0, 0, 0.20)
                
                if not risk_ok:
                    entry_reason = f"Risk limit: {risk_reason}"
                
                if score >= ENTRY_SCORE_THRESHOLD and balance > 0 and atr_value > 0 and best_tf and risk_ok:
                    print(f"🎯 Entry signal detected! Score: {score:.1f}, Type: {signal_position_type}")
                    print(f"📊 RSI: {rsi_value:.1f}, ATR: {atr_value:.2f}, Timeframe: {best_tf}")
                    print(f"📝 Reason: {entry_reason}")
                    
                    open_position(signal_position_type, entry_price_candle, score, best_tf)
                elif score > 0:
                    print(f"📈 Signal score: {score:.1f} (threshold: {ENTRY_SCORE_THRESHOLD})")
            
            error_count = 0
            
            time.sleep(10)
            
        except Exception as e:
            error_count += 1
            print(f"  [TRADING LOOP] Error #{error_count}: {e}")
            
            if error_count >= max_errors:
                print(f"  [TRADING LOOP] Too many errors ({error_count}), restarting loop...")
                error_count = 0
            
            time.sleep(10)

# ==================== MAIN HEADLESS APPLICATION ====================

def main_headless():
    """تابع اصلی برای اجرای Headless"""
    print("\n" + "="*70)
    print("🚀 BEHZAD ULTIMATE PRO FUTURES BOT - HEADLESS MODE")
    print("⚡ Optimized for Render Cloud - NO GUI")
    print("="*70)
    
    if not initialize_exchange():
        print("❌ Cannot start trading without exchange connection")
        return
    
    load_state()
    
    # بارگذاری اولیه اندیکاتورها
    print("📈 Loading initial indicators...")
    update_all_indicators()
    
    # نمایش وضعیت اولیه
    current_price = fetch_current_price()
    get_account_balance()
    
    print(f"\n📊 INITIAL STATUS:")
    print(f"   Balance: ${balance:.2f}")
    print(f"   Price: ${current_price:.2f}")
    print(f"   Position: {'ACTIVE' if in_position else 'INACTIVE'}")
    if in_position:
        print(f"   Position Type: {position_type.upper()}")
        print(f"   Entry Price: ${entry_price:.2f}")
    
    # نمایش امتیازهای فعلی
    print(f"\n📈 CURRENT SCORES (FIXED FROM CLOSED CANDLE):")
    
    buy_score, buy_info, buy_tf = calculate_score_for_position_type('long')
    if buy_score >= ENTRY_SCORE_THRESHOLD:
        print(f"   BUY SCORE: {buy_score:.1f} ✓ (Signal: BUY)")
    else:
        print(f"   BUY SCORE: {buy_score:.1f} ✗ (Threshold: {ENTRY_SCORE_THRESHOLD})")
    
    sell_score, sell_info, sell_tf = calculate_score_for_position_type('short')
    if sell_score >= ENTRY_SCORE_THRESHOLD:
        print(f"   SELL SCORE: {sell_score:.1f} ✓ (Signal: SELL)")
    else:
        print(f"   SELL SCORE: {sell_score:.1f} ✗ (Threshold: {ENTRY_SCORE_THRESHOLD})")
    
    print(f"\n🔄 Starting trading loop...")
    print("="*70)
    
    # شروع حلقه معاملاتی
    trading_loop()

# ==================== اجرای برنامه ====================

if __name__ == "__main__":
    print("\n📋 CONFIGURATION SUMMARY (HEADLESS VERSION)")
    print("="*60)
    print(f" Trading Mode: {TRADING_MODE}")
    print(f" Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f" Position Size: {POSITION_SIZE_PCT*100}%")
    print(f" Leverage: {LEVERAGE}x")
    print(f" Exchange: {EXCHANGE_NAME}")
    print(f" Symbol: {SYMBOL}")
    print(f" Real Trading: {REAL_TRADING}")
    print("="*60)
    print("🚀 Starting HEADLESS Futures Trading Bot")
    print("⚡ Real Trading Mode - Using REAL balances from exchange")
    print("💼 Logic: FULL ORIGINAL LOGIC (No GUI)")
    print("🛡️  Optimized for Render Cloud Server")
    
    main_headless()
    