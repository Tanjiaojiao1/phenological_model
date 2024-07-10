# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import math
from pylab import *
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import os
from photo_period_effect import photoeffect_yin, photoeffect_oryza2000, CERES_Rice
from T_dev_effect import Wang_engle, T_base_op_ceiling, T_base_opt
import datetime
import Sun
os.chdir(os.path.dirname(os.path.realpath(__file__)))

pd.options.display.max_columns = 999
pd.options.display.max_rows = 999


sun = Sun.Sun()

def photo_effect_correct(today, jd, hd, photo):
    if today < jd or today > hd:
        return 1
    else:
        return photo

def simulate_and_calibrate(thermal_fun,thermal_fun_para,photofun,photo_fun_para,dfws,df,quantile=0.50):
    dfmm = df[['SID', 'lat', 'lon', 'alt', 'year', 'season',
               'reviving date', 'tillering date', 'jointing date',
               'booting date', 'heading date', 'maturity date']].copy()
    dfm = pd.melt(dfmm, id_vars=['SID', 'lat', 'lon', 'alt', 'year', 'season'],
                  value_vars=['reviving date', 'tillering date', 'jointing date',
                              'booting date', 'heading date', 'maturity date'])
    dfm = dfm.rename(columns={'value': 'Date', 'variable': 'DStage'})
    dfm.Date=pd.to_datetime(dfm.Date)
    dfall = pd.DataFrame()
    for ind, row in df.iterrows():
        dfws.Date=pd.to_datetime(dfws.Date)
        dfw=dfws.loc[(dfws.SID==row.SID)&(dfws.year==row.year)&(dfws.season==row.season)&(dfws.Date>=row['reviving date']),].copy()
        
        dfw['Thermal_raw'] = dfw.TemAver.apply(lambda x: thermal_fun(T=x,**thermal_fun_para))
        dfw['Thermal_cum'] = dfw.Thermal_raw.cumsum()
        dfw['dayL'] = dfw.Date.apply(
            lambda x: sun.dayCivilTwilightLength(year=x.year, month=x.month, day=x.day, lon=row.lon, lat=row.lat))
        if photofun=='':
            dfw['photo_raw']=1
            dfw['photo']=1
        else:
            dfw['photo_raw'] = dfw.dayL.apply(lambda x: photofun(DL=x,**photo_fun_para))
            dfw['photo'] = dfw.apply(
                lambda rowt: photo_effect_correct(today=rowt.Date, jd=row['jointing date'],
                                                hd=row['heading date'], photo=rowt.photo_raw), axis=1)
        dfw['photothermal'] = dfw.photo * dfw.Thermal_raw
        dfw['photothermal_cum'] = dfw['photothermal'].cumsum()
        dfall = pd.concat([dfall, dfw])
    # print(dfall)
    thermaldf = dfall.merge(dfm, on=['SID', 'year', 'Date', 'season'], how='right')
    # thermaldf.to_excel('../data/thermaldf.csv', index=False)

    # 计算每个DStage的分位数
    dfp = thermaldf.groupby('DStage').median()['photothermal_cum'].reset_index()
    mature_percentile_thermal=thermaldf.loc[thermaldf.DStage=='maturity date','photothermal_cum'].quantile(quantile)
    dfp.loc[(dfp.DStage=='maturity date'),'photothermal_cum'] = mature_percentile_thermal
    if mature_percentile_thermal<dfp.loc[(dfp.DStage=='heading date'),'photothermal_cum'].values[0]:
        dfp.loc[(dfp.DStage=='heading date'),'photothermal_cum']=(mature_percentile_thermal+dfp.loc[(dfp.DStage=='booting date'),'photothermal_cum'].values[0])/2
        if dfp.loc[(dfp.DStage=='heading date'),'photothermal_cum'].values[0]<dfp.loc[(dfp.DStage=='booting date'),'photothermal_cum'].values[0]:
            dfp.loc[(dfp.DStage=='booting date'),'photothermal_cum']=(dfp.loc[(dfp.DStage=='heading date'),'photothermal_cum'].values[0]+dfp.loc[(dfp.DStage=='jointing date'),'photothermal_cum'].values[0])/2
            if dfp.loc[(dfp.DStage=='booting date'),'photothermal_cum'].values[0]<dfp.loc[(dfp.DStage=='jointing date'),'photothermal_cum'].values[0]:
                dfp.loc[(dfp.DStage=='jointing date'),'photothermal_cum']=(dfp.loc[(dfp.DStage=='booting date'),'photothermal_cum'].values[0]+dfp.loc[(dfp.DStage=='tillering date'),'photothermal_cum'].values[0])/2
                if dfp.loc[(dfp.DStage=='jointing date'),'photothermal_cum'].values[0]<dfp.loc[(dfp.DStage=='reviving date'),'photothermal_cum'].values[0]:
                    dfp.loc[(dfp.DStage=='reviving date'),'photothermal_cum']=1.0
                    
    dfp.loc[(dfp.DStage=='maturity date'),'photothermal_cum'] = mature_percentile_thermal
    dfp = dfp.sort_values(by=['photothermal_cum']).reset_index()

    mybins = dfp.photothermal_cum.tolist()
    mybins.append(9999999)
    mybins[0] = 0
    dfall['PhotoThermal_Dstage'] = dfall.groupby(['SID', 'year', 'season'])[['photothermal_cum']].transform(
        lambda x: pd.cut(x, bins=mybins, labels=dfp.DStage.tolist()).astype(str))
    dfpall = dfall.drop_duplicates(subset=['SID', 'year', 'season', 'PhotoThermal_Dstage'])

    dfpall = dfpall[['SID', 'year', 'season', 'Date', 'PhotoThermal_Dstage']].rename(
        columns={'PhotoThermal_Dstage': 'DStage', 'Date': 'sim_date'})
    
    dff = dfm.merge(dfpall, on=['SID', 'year', 'season', 'DStage'], how='left').rename(columns={'Date':'ob_date'})
    
    dff.loc[dff.DStage != 'reviving date', 'sim_date'] = dff.loc[dff.DStage != 'reviving date', 'sim_date'].apply(
        lambda x: x + datetime.timedelta(days=-1))
    
    dff['delta_days'] = (dff.sim_date-dff.ob_date).dt.days

   # Find rows where 'delta_days' is null & DStage == 'maturity date'
    null_rows = dff.loc[(dff.DStage == 'maturity date') & dff.delta_days.isnull()]
    # Iterate over null rows and calculate delta_days between 'reviving_ob_date' + 124 days and 'maturity_ob_date'
    for ind, row in null_rows.iterrows():
        # print(ind, row)
        sid = row['SID']
        year = row['year']
        season = row['season']
        # Find 'reviving date' and 'maturity date' ob_dates for the corresponding 'SID', 'year', 'season'
        reviving_ob_date = dff.loc[(dff.SID == sid) & (dff.year == year) & (dff.season == season)& (dff.DStage == 'reviving date')]['ob_date'].values[0]
        maturity_ob_date = dff.loc[(dff.SID == sid) & (dff.year == year) & (dff.season == season)& (dff.DStage == 'maturity date')]['ob_date'].values[0]
        # Calculate the difference in days between 'reviving_ob_date' + 124 days and 'maturity_ob_date'
        reviving_date_plus_124 = pd.to_datetime(reviving_ob_date) + datetime.timedelta(days=124)
        delta_days = (reviving_date_plus_124 - maturity_ob_date).days
        # Update 'abs_delta_days' in the 'dff' DataFrame
        dff.loc[ind, 'delta_days'] = delta_days

    dff['abs_delta_days']=dff['delta_days'].abs()

    return dff







