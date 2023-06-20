import requests
import pandas as pd
import time
import numpy as np
from datetime import timedelta
import math

dates = [['2020', '2021'], ['2021', '2022'], ['2022', '2023']]
months = [['05', '11'], ['12', '04']]
currencies = ['EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCNY', 'USDCHF']
fx_df = df = pd.DataFrame(columns=[])


for drange in dates:
    for cur in currencies:
        time.sleep(0.25)
        url = "https://api.polygon.io/v2/aggs/ticker/C:{}/range/1/minute/{}-05-11/{}-11-11?adjusted=true&sort=asc&limit=99999&apiKey=beBybSi8daPgsTp5yx5cHtHpYcrjp5Jq".format(
            cur, drange[0], drange[0])
        print(url)
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        json_data = response.json()
        relevant_data = json_data['results']
        tmp_df = pd.DataFrame(relevant_data)
        tmp_df['datetime'] = pd.to_datetime(tmp_df['t'], unit='ms')
        tmp_df['Currency'] = cur
        fx_df = pd.concat([fx_df, tmp_df], ignore_index=True)

        time.sleep(0.25)
        url = "https://api.polygon.io/v2/aggs/ticker/C:{}/range/1/minute/{}-12-11/{}-04-11?adjusted=true&sort=asc&limit=99999&apiKey=beBybSi8daPgsTp5yx5cHtHpYcrjp5Jq".format(
            cur, drange[0], drange[1])
        print(url)
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        json_data = response.json()
        relevant_data = json_data['results']
        tmp_df = pd.DataFrame(relevant_data)
        tmp_df['datetime'] = pd.to_datetime(tmp_df['t'], unit='ms')
        tmp_df['Currency'] = cur
        fx_df = pd.concat([fx_df, tmp_df], ignore_index=True)

kelter_bands_delta = None
four_hour_df = pd.DataFrame({
    'Timestamp': [],
    'Currency_Pair': [],
    'VWAP': [],
    'Liquidity': [],
    'Volatility': [],
    'Max': [],
    'Min': [],
    'FD': [],
})

currency_df = fx_df[fx_df['Currency'] == currencies[0]]
current_date = fx_df['datetime'].min()
end_date = fx_df['datetime'].max()
while current_date <= end_date:
    filtered_df = currency_df[
        (currency_df['datetime'] >= current_date) & (currency_df['datetime'] <= current_date + timedelta(hours=24))]
    filtered_df = filtered_df.dropna()
    if len(filtered_df) > 0:
        min_vwap = filtered_df['vw'].min()
        max_vwap = filtered_df['vw'].max()
        mean_vwap = filtered_df['vw'].mean()
        volatility = (max_vwap - min_vwap) / mean_vwap if max_vwap > min_vwap else 0
        count = 0
        if kelter_bands_delta is not None:
            last_value = None
            for index, row in filtered_df.iterrows():
                if last_value is not None:
                    diff = abs(row['vw'] - last_value)
                    count += math.floor(diff / kelter_bands_delta) if kelter_bands_delta > 0 else 0
                last_value = row['vw']
            fd = count / (max_vwap - min_vwap) if max_vwap > min_vwap else 0
            four_hour_df = four_hour_df.append({
                'Timestamp': current_date,
                'Currency_Pair': currencies[0],
                'VWAP': mean_vwap,
                'Liquidity': filtered_df['v'].mean(),
                'Volatility': volatility,
                'Max': max_vwap,
                'Min': min_vwap,
                'FD': fd
            }, ignore_index=True)
        # calculate Kelter Bands delta
        kelter_bands_delta = 0.025 * volatility
current_date = current_date + timedelta(hours=24)