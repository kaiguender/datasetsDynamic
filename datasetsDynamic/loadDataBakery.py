# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_bakery.ipynb.

# %% ../nbs/02_bakery.ipynb 3
from __future__ import annotations
from fastcore.docments import *
from fastcore.test import *
from fastcore.utils import *

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from os.path import join
from tsfresh.feature_extraction import MinimalFCParameters
from tsfresh.utilities.dataframe_functions import roll_time_series
from tsfresh import extract_features
import pathlib
import pkg_resources

from .utils import *

# %% auto 0
__all__ = ['loadDataBakery']

# %% ../nbs/02_bakery.ipynb 5
def loadDataBakery(testDays = 28, returnXY = True, daysToCut = 0, disable_progressbar = False):
    
    # LOAD RAW DATA
    dataPath = pkg_resources.resource_stream(__name__, 'datasets/dataBakery_unprocessed.csv')
    data = pd.read_csv(dataPath)
    
    #---
    
    # RENAME AND DROP COLUMNS
    data.drop(columns=["temp_min", "temp_max"], inplace=True)
    
    data.rename(columns={"date_short": "date", 
                         "shop_no": "store", 
                         "product_no": "item", 
                         "temp_avg_celsius": "temperature", 
                         "rain_mm": "rain"}, 
                inplace=True)
    
    #---
    
    # REMOVE INTERMITTENT DEMAND
    data_grouped = data.groupby(["store", "item"])
    groups = list(data_grouped.groups.keys())
    
    # get all store/item instances with more than 20 percent zero sales
    more_than_20_p_zero = []
    for group in groups:
        data_temp = data_grouped.get_group(group)
        zero = data_temp[data_temp["demand"]==0].shape[0]
        non_zero = data_temp[data_temp["demand"]!=0].shape[0]
        if zero/(non_zero+zero) >= 0.2:
            more_than_20_p_zero.append(group)
            
    # drop zero sales instances
    for group in more_than_20_p_zero:
        data = data.drop(data_grouped.get_group(group).index)
    
    #---
    
    # CALENDAR FEATURES
    data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
    data['year'] = data['date'].dt.year
    
    #---
    
    # ID Feature
    data['id'] = [str(data.store.iloc[i]) + '_' + str(data.item.iloc[i]) for i in range(data.shape[0])]
    
    #---
    
    # DAY INDEX
    data['dayIndex'] = data['date'].apply(lambda x: getDayIndex(x))
    
    #---
    
    # CUT DAYS DEPENDING ON DAYSTOCUT
    cutOffDate = data.dayIndex.max() - daysToCut
    data = data[data['dayIndex'] <= cutOffDate].reset_index(drop = True)
    
    #---
    
    # LABEL
    if isinstance(testDays, int):
        nDaysTest = testDays
    else:
        tsSizes = data.groupby(['id']).size()
        nDaysTest = int(tsSizes.iloc[0] * testDays)

    cutoffDateTest = data.dayIndex.max() - nDaysTest
    data['label'] = ['train' if data.dayIndex.iloc[i] <= cutoffDateTest else 'test' for i in range(data.shape[0])]    

    #---

    # data = data.sort_values(by = ['id', 'dayIndex'], axis = 0).reset_index(drop = True)

    #---

    # NORMALIZE DEMAND
    scalingData = data[data.label == 'train'].groupby('id')['demand'].agg('max').reset_index()
    scalingData.rename(columns = {'demand': 'scalingValue'}, inplace = True)
    data = pd.merge(data, scalingData, on = 'id')
    
    data['demand'] = data.demand / data.scalingValue

    #---

    # DEMAND LAG FEATURES
    
    y = pd.DataFrame(data['demand'])
    X = data.drop(columns = ['demand'])

    # set lag features
    fc_parameters = MinimalFCParameters()

    # delete length features
    del fc_parameters['length']

    # create lag features
    X, y = add_lag_features(X = X, 
                            y = y, 
                            column_id = ['id'],
                            column_sort = 'dayIndex', 
                            feature_dict = fc_parameters, 
                            time_windows = [(7, 7), (14, 14), (28, 28)],
                            n_jobs = 32, 
                            disable_progressbar = False)
    
    #---
    
    X['year'] = X['year'].apply(lambda x: str(int(x)))

    X = pd.concat([X, 
                  pd.get_dummies(X.weekday, prefix = 'weekday'), 
                  pd.get_dummies(X.month, prefix = 'month'), 
                  pd.get_dummies(X.year, prefix = 'year')], axis = 1).drop(['weekday', 'month', 'year'], axis = 1)

    X = pd.concat([X, pd.get_dummies(X.item, prefix = 'item')], axis = 1).drop(['item'], axis = 1)

    #---
    
    # STORE AND ITEM DUMMY VARIABLES
    data['item'] = data['item'].apply(lambda x: str(int(x)))
    data['store'] = data['store'].apply(lambda x: str(int(x)))
    dataTrain = pd.concat([data, 
                           pd.get_dummies(data.item, prefix = 'item'), 
                           pd.get_dummies(data.store, prefix = 'store')], axis = 1).drop(['store', 'item'], axis = 1)
    
    #---
    
    # SPLIT INTO TRAIN AND TEST DATA
    data = pd.concat([y, X], axis = 1)
    XArray = np.array(X.drop(['label', 'id'], axis = 1))   
    yArray = np.ravel(y)    
    
    XTrain = XArray[data['label'] == 'train']
    yTrain = yArray[data['label'] == 'train']

    XTest = XArray[data['label'] == 'test']
    yTest = yArray[data['label'] == 'test']

    #---

    if returnXY:
        return data, XTrain, yTrain, XTest, yTest
    else:
        return data    

