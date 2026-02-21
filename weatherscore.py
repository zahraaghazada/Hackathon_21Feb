#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 12:59:06 2026
@author: zehra
"""

import requests
import calendar
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim 
from datetime import datetime

def get_romantic_weather_prediction(city_name, target_month):
    print(f"--- PREDICTING TOP TWILIGHT DAYS FOR {city_name} on MONTH {target_month} ---")
    
    # Location Logic
    geolocator = Nominatim(user_agent="big_ring_theory") #nominatim turns cities into GPS coordinates
    location = geolocator.geocode(city_name)
    if not location: return "Location not found."
    
    lat, lon = location.latitude, location.longitude
    is_northern = lat > 0  #Define the Northern Hemisphere

    # Ideal Temp Logic
    if is_northern:
        if target_month in [6, 7, 8]: ideal_t = 20    # Summer
        elif target_month in [12, 1, 2]: ideal_t = 5  # Winter
        elif target_month in [3,4,5]: ideal_t = 15    # Spring
        else: ideal_t = 12                            # Autumn
    else:
        if target_month in [12, 1, 2]: ideal_t = 20   # Summer
        elif target_month in [6, 7, 8]: ideal_t = 5    # Winter
        elif target_month in [3,4,5]: ideal_t = 15    # Spring
        else: ideal_t = 12                            # Autumn

    # Data Collection Loop
    all_years = []
    current_year = 2026
    
    for year in range(current_year - 4, current_year):
        last_day = calendar.monthrange(year, target_month)[1]
        start_date = f"{year}-{target_month:02d}-01"
        end_date = f"{year}-{target_month:02d}-{last_day}"
        
        w_url = "https://archive-api.open-meteo.com/v1/archive"
        w_params = {
            "latitude": lat, "longitude": lon,
            "start_date": start_date, "end_date": end_date,
            "daily": ["temperature_2m_max", "precipitation_sum", "cloud_cover_mean", "wind_speed_10m_max"],
            "timezone": "auto"
        }
        
        try:
            w_res = requests.get(w_url, params=w_params)
            if w_res.status_code == 200:
                #Convert the 'daily' section into a DataFrame
                df_w = pd.DataFrame(w_res.json()['daily'])
                #Add this year's weather table to the list of dataframes
                all_years.append(df_w)
        #Catch any errors to prevent crashing
        except Exception as e:
            print(f"Error fetching data for {year}: {e}")
            
    #If the list is empty then notify 
    if not all_years:
        return "NO WEATHER DATA WAS COLLECTED!"
    
    # 4. Data Processing
    hist_weather_info = pd.concat(all_years)
    hist_weather_info['day'] = pd.to_datetime(hist_weather_info['time']).dt.day
    daily_avg = hist_weather_info.groupby('day').mean(numeric_only=True).reset_index() 

    # Scoring Formula
    def calc_score(row):
        # Cloudiness (70%)
        c_score = 100 - row['cloud_cover_mean']
        
        # Temperature (30%) - Gaussian Bell Curve
        t_score = np.exp(-((row['temperature_2m_max'] - ideal_t)**2) / (2 * 8**2)) * 100
        
        # Multipliers - Penalties (for rain and wind)
        r_mult = 1.0 if row['precipitation_sum'] < 0.1 else max(0, 1 - (row['precipitation_sum'] / 3))
        w_mult = 1.0 if row['wind_speed_10m_max'] < 12 else max(0.1, 1 - (row['wind_speed_10m_max'] / 18))
        #p_mult = 1.0 if row['pm2_5'] < 10 else max(0, 1 - (row['pm2_5'] - 10) / 40)
        
        #The Final Score for the Weather Scoring Formula
        final_score = ((c_score * 0.7) + (t_score * 0.3)) * r_mult * w_mult
        return round(final_score, 1)

    daily_avg['score'] = daily_avg.apply(calc_score, axis=1)
    return daily_avg.sort_values(by='score', ascending=False).head(3)

#Execute the formula
today = datetime.now()
next_month = today.month + 1 if today.month < 12 else 1

print("\nResults for Imishli, Azerbaijan:")
print(get_romantic_weather_prediction("Imishli, Azerbaijan", next_month))
                