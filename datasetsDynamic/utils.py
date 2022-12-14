# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_utils.ipynb.

# %% ../nbs/00_utils.ipynb 3
from __future__ import annotations
from fastcore.docments import *
from fastcore.test import *
from fastcore.utils import *

import pandas as pd
import numpy as np

from os.path import join
from tsfresh.feature_extraction import MinimalFCParameters
from tsfresh.utilities.dataframe_functions import roll_time_series
from tsfresh import extract_features
import pathlib
import pkg_resources

# %% auto 0
__all__ = ['add_lag_features', 'getWeekdayFeature', 'getMonthFeature', 'getDayIndex']

# %% ../nbs/00_utils.ipynb 6
def add_lag_features(X, y, column_id, column_sort, feature_dict, time_windows, n_jobs = 32, disable_progressbar = False):
    """
    Create lag features for y and add them to X
    Parameters:
    -----------
    X: pandas.DataFrame 
    feature matrix to which TS features are added.
    y: pandas.DataFrame, 
    time series to compute the features for.
    column_id: list, 
    list of column names to group by, e.g. ["shop","product"]. If set to None, 
    either there should be nothing to groupby or each group should be 
    represented by a separate target column in y. 
    column_sort: str,
    column name used to sort the DataFrame. If None, will be filled by an 
    increasing number, meaning that the order of the passed dataframes are used 
    as “time” for the time series.
    feature_dict: dict,
    dictionary containing feature calculator names with the corresponding 
    parameters
    time_windows : list of tuples, 
    each tuple (min_timeshift, max_timeshift), represents the time shifts for 
    ech time windows to comupute e.g. [(7,7),(1,14)] for two time windos 
    a) time window with a fix size of 7 and b) time window that starts with size
    1 and increases up to 14. Then shifts by 1 for each step. 
    """

    if column_id == None:
        X['id'] = 1

    else:
        X['id'] = X[column_id].astype(str).agg('_'.join, axis = 1)

    if column_sort == None:
        X['time'] = range(X.shape[0])  

    else:
        X["time"] = X[column_sort].copy()
    
    y = pd.concat([y, X[['id', 'time']]], axis = 1)
    X = X.set_index(['id', 'time'])
  
    for window in time_windows:
        
        # create time series for given time window 
        df_rolled = roll_time_series(y, 
                                     column_id = "id", 
                                     column_sort = "time", 
                                     min_timeshift = window[0]-1, 
                                     max_timeshift = window[1]-1,
                                     n_jobs = n_jobs,
                                     disable_progressbar = disable_progressbar)
        
        df_rolled['id'] = df_rolled['id'].apply(lambda x: (x[0], x[1] + 1))

        # create lag features for given time window 
        df_features = extract_features(df_rolled, 
                                       column_id = "id", 
                                       column_sort = "time",
                                       default_fc_parameters = feature_dict,
                                       n_jobs = n_jobs,
                                       disable_progressbar = disable_progressbar)

        # Add time window to feature name for clarification 
        feature_names = df_features.columns.to_list()
        feature_names = [name + "_" + str(window[1]) for name in feature_names]
        df_features.columns = feature_names
        
        # add features for given time window to feature matrix temp
        X = pd.concat([X, df_features], axis = 1)
    
    y = y.set_index(['id', 'time'])
    y_column_names = y.columns.to_list()

    df = pd.concat([X, y],axis = 1)
    df = df.dropna()
    df.index.names = ['id', 'time']
    df = df.reset_index(drop = False, inplace = False).drop(['time'], axis = 1, inplace = False)
    
    y = df[y_column_names]
    X = df.drop(y_column_names, axis = 1)

    return X, y

# %% ../nbs/00_utils.ipynb 8
def getWeekdayFeature(weekday):
    if weekday == 'MON':
        weekdayInt = 1
    elif weekday == 'TUE':
        weekdayInt = 2
    elif weekday == 'WED':
        weekdayInt = 3
    elif weekday == 'THU':
        weekdayInt = 4
    elif weekday == 'FRI':
        weekdayInt = 5
    elif weekday == 'SAT':
        weekdayInt = 6
    elif weekday == 'SUN':
        weekdayInt = 7
        
    return weekdayInt        

# %% ../nbs/00_utils.ipynb 9
def getMonthFeature(month):
    if month == 'JAN':
        monthInt = 1
    elif month == 'FEB':
        monthInt = 2
    elif month == 'MAR':
        monthInt = 3
    elif month == 'APR':
        monthInt = 4
    elif month == 'MAY':
        monthInt = 5
    elif month == 'JUN':
        monthInt = 6
    elif month == 'JUL':
        monthInt = 7
    elif month == 'AUG':
        monthInt = 8
    elif month == 'SEP':
        monthInt = 9
    elif month == 'OCT':
        monthInt = 10
    elif month == 'NOV':
        monthInt = 11
    elif month == 'DEC':
        monthInt = 12
    
    return monthInt

# %% ../nbs/00_utils.ipynb 10
def getDayIndex(date):
    year = date.timetuple().tm_year
    
    if year == 2016:
        yearCoefficient = 0
    elif year == 2017:
        yearCoefficient = 366
    elif year == 2018:
        yearCoefficient = 366 + 365
    elif year == 2019:
        yearCoefficient = 366 + 365 + 365
    elif year == 2020:
        yearCoefficient = 366 + 365 + 365 + 365
        
    dayIndex = date.timetuple().tm_yday + yearCoefficient
    
    return dayIndex
