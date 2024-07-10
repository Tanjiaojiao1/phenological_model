# -*- coding: utf-8 -*-
import pandas as pd
from pylab import *
import os
import seaborn as sns
from photo_period_effect import photoeffect_yin, photoeffect_oryza2000, CERES_Rice
from T_dev_effect import Wang_engle, T_base_op_ceiling, T_base_opt
import datetime
from sklearn.cluster import KMeans
from all_models import simulate_and_calibrate
from multiprocessing import Pool

os.chdir(os.path.dirname(os.path.realpath(__file__)))

pd.options.display.max_columns = 99999
pd.options.display.max_rows = 99999

def getweatherstat_TemAver_ATM(SID,trd):
    '''
    SID:station id
    trd:transplanting date
    '''
    print(SID,trd)
    csy=trd.year
    df = pd.read_table("../data/Meteo/" + str(SID) + ".txt", encoding='gbk', sep=' * ', engine='python',
                       skiprows=[1])
    df['Date'] = df.apply(lambda row: pd.to_datetime('%d-%d-%d' % (row.YY, row.mm, row.dd)), axis=1)
    df = df.loc[(df.Date >= datetime.datetime(csy,1,1)) & (df.Date <= datetime.datetime(csy,12,31)), ['Date', 'TemAver']]
    df['Thermal']=df.TemAver.apply(lambda x:np.interp(x,[8,30],[0,22]))
    ATM=df.TemAver.mean()
    ATS=df.Thermal.sum()
    dfs= df.loc[(df.Date >= trd) & (df.Date <= trd+datetime.timedelta(days=120)), ['Date', 'TemAver','Thermal']]
    STM=dfs.TemAver.mean()
    STS=dfs.Thermal.sum()
    return ATM,ATS,STM,STS, df.loc[(df.Date >= trd) & (df.Date <= trd+datetime.timedelta(days=60)), 'Thermal'].sum(),\
           df.loc[(df.Date >= trd) & (df.Date <= trd+datetime.timedelta(days=70)), 'Thermal'].sum()

def get_weather(SID,trd):
    '''
    SID:station id
    trd:transplanting date
    '''
    print(SID,trd)

    df = pd.read_table("../data/Meteo/" + str(SID) + ".txt", encoding='gbk', sep=' * ', engine='python',
                       skiprows=[1])
    df['Date'] = df.apply(lambda row: pd.to_datetime('%d-%d-%d' % (row.YY, row.mm, row.dd)), axis=1)

    dfs= df.loc[(df.Date >= trd) & (df.Date <= trd+datetime.timedelta(days=160)), ['Date', 'TemAver']]

    return dfs

def put_weather_together():
    df = pd.read_excel('../data/obser_pheno_catalog.xlsx',
                     parse_dates=['transplanting date','reviving date', 'tillering date', 'jointing date',
                                  'booting date', 'heading date','maturity date'])
    df['season']= df.groupby(['station ID', 'year']).cumcount()+1
    dfm = df[['station ID', 'lat', 'lon', 'alt', 'year', 'season','transplanting date',
               'reviving date', 'tillering date', 'jointing date',
               'booting date', 'heading date','maturity date']]
    for ind,row in dfm.iterrows():
        wth=get_weather(row['station ID'],row['transplanting date'])
        wth['SID']=row['station ID']
        wth['year']=row.year
        wth['season']=row.season
        wth.to_csv('.../weather_all.csv',index=False,header=False if os.path.exists('.../weather_all.csv') else True,mode='a')

def create_cluster_variables():
    '''
    Trans60_TS: Thermal Accumulation within 60 days after transplanting
    Trans70_TS: Thermal Accumulation within 70 days after transplanting
    '''
    df = pd.read_excel('.../obser_pheno_catalog.xlsx',
                     parse_dates=['transplanting date','reviving date', 'tillering date', 'jointing date',
                                  'booting date', 'heading date','maturity date'])
    df['season']= df.groupby(['station ID', 'year']).cumcount()+1
    dfm = df[['station ID', 'lat', 'lon', 'alt', 'year', 'season','transplanting date',
               'reviving date', 'tillering date', 'jointing date',
               'booting date', 'heading date','maturity date']]

    dfm = dfm.rename(columns={'station ID':'SID'})
    dfm['TDOY']=dfm['transplanting date'].dt.dayofyear
    dfm['WS'] = dfm.apply(lambda row: getweatherstat_TemAver_ATM(row.SID, row['transplanting date']), axis=1)
    dfm['ATM']=dfm.WS.apply(lambda x:x[0])
    dfm['ATS']=dfm.WS.apply(lambda x:x[1])
    dfm['STM']=dfm.WS.apply(lambda x:x[2])
    dfm['STS']=dfm.WS.apply(lambda x:x[3])
    dfm['Trans60_TS']=dfm.WS.apply(lambda x:x[4])
    dfm['Trans70_TS']=dfm.WS.apply(lambda x:x[5])
    dfm.to_excel('.../dfm.xlsx', index=False)

def cluster_and_sim():
    df = pd.read_excel('.../dfm.xlsx')
    wths = pd.read_csv('.../weather_all.csv')
    if os.path.exists('.../cluster_and_sim.csv'):
        os.remove('.../cluster_and_sim.csv')
    for va in [['lat'], ['STM'], ['lat','STM'],['lat', 'STM','alt'],['lat', 'STM', 'TDOY'],['lat', 'STM', 'TDOY', 'alt']]:
        print(va)
        for n_cluster in [1, 3, 6, 9, 12, 18, 24]:
            kmeans = KMeans(n_clusters=n_cluster)
            y = kmeans.fit_predict(df[va])
            df['Cluster_%d_%s' % (n_cluster, '_'.join(va))] = y
            for ind, gp in df.groupby('Cluster_%d_%s' % (n_cluster, '_'.join(va))):
                print(ind)
                dfws = wths.merge(gp, on=['SID', 'year', 'season'])[['SID', 'year', 'season', 'Date', 'TemAver']]
                for thermalfun, thermalfun_para in zip([Wang_engle, T_base_op_ceiling, T_base_opt],
                                                       [{"Tbase": 8, "Topt": 30, "Tcei": 42}, {"Tbase": 8,"Topt_low": 25,"Topt_high": 35,"Tcei": 42, },
                                                        {"Tbase": 8, "Topt": 30}]):
                    for photofun, photofun_para in zip([photoeffect_yin, photoeffect_oryza2000, CERES_Rice, ""],
                                                       [{"mu": -15.46, "zeta": 2.06, "ep": 2.48},
                                                        {"Dc": 12.5, 'PPSE': 0.2}, {"psr": 100, "Do": 12.5}, ""]):
                        for quantile in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
                            dfcm = simulate_and_calibrate(thermal_fun=thermalfun, thermal_fun_para=thermalfun_para,
                                                        photofun=photofun, photo_fun_para=photofun_para, dfws=dfws, df=gp, quantile=quantile)
                            print(thermalfun, photofun)
                            dfcm['thermalfun'] = thermalfun.__name__
                            if photofun == '':
                                print('here')
                                dfcm['photofun'] = ''
                                dfcm['model'] = thermalfun.__name__
                            else:
                                dfcm['photofun'] = photofun.__name__
                                dfcm['model'] = thermalfun.__name__ + '_' + photofun.__name__
                            dfcm['n_cluster'] = n_cluster
                            dfcm['cluster_vas'] = '_'.join(va)
                            dfcm['claster_number'] = ind
                            dfcm['quantiles'] = quantile

                            dfcm.to_csv('../data/cluster_and_sim.csv', mode='a',
                                        header=False if os.path.exists('../data/cluster_and_sim.csv') else True,
                                        index=False)
    df.to_excel('../data/dfm_cluster.xlsx', index=False)


def cluster_and_sim_parallel():
    df=pd.read_excel('../data/dfm.xlsx')
    wths=pd.read_csv('../data/weather_all.csv')
    if os.path.exists('../data/cluster_and_sim.csv'):
        os.remove('../data/cluster_and_sim.csv')
    pool=Pool(50)
    res=[]
    for va in [['lat'], ['STM'], ['lat','STM'],['lat', 'STM','alt'],['lat', 'STM', 'TDOY'],['lat', 'STM', 'TDOY', 'alt']]:
        print(va)
        for n_cluster in [1, 3, 6, 9, 12, 18, 24]:
            kmeans=KMeans(n_clusters=n_cluster)
            y = kmeans.fit_predict(df[va])
            df['Cluster_%d_%s'%(n_cluster,'_'.join(va))]=y
            re=pool.apply_async(sim_cluster,(df,wths,n_cluster,va))
            res.append(re)
    for re in res:
        dfcm=re.get()
        dfcm.to_csv('../data/cluster_and_sim.csv',mode='a',header=False if os.path.exists('../data/cluster_and_sim.csv') else True,index=False)

    df.to_excel('../data/dfm_cluster.xlsx', index=False)


def cluster_and_sim_sequence():
    df=pd.read_excel('../data/dfm.xlsx')
    wths=pd.read_csv('../data/weather_all.csv')
    if os.path.exists('../data/cluster_and_sim.csv'):
        os.remove('../data/cluster_and_sim.csv')

    for va in [['lat'], ['STM'], ['lat','STM'],['lat', 'STM','alt'],['lat', 'STM', 'TDOY'],['lat', 'STM', 'TDOY', 'alt']]:
        print(va)
        for n_cluster in [1, 3, 6, 9, 12, 18, 24]:
            kmeans=KMeans(n_clusters=n_cluster)
            y = kmeans.fit_predict(df[va])
            df['Cluster_%d_%s'%(n_cluster,'_'.join(va))]=y
            dfcm=sim_cluster(df,wths,n_cluster,va)
            dfcm.to_csv('../data/cluster_and_sim.csv',mode='a',header=False if os.path.exists('../data/cluster_and_sim.csv') else True,index=False)
            break
    df.to_excel('../data/dfm_cluster.xlsx', index=False)


def sim_cluster(df,wths,n_cluster,va):
    dfall=pd.DataFrame()
    for ind,gp in df.groupby('Cluster_%d_%s'%(n_cluster,'_'.join(va))):
        print(ind)
        dfws=wths.merge(gp,on=['SID','year','season'])[['SID','year','season','Date','TemAver']]
        for thermalfun,thermalfun_para in zip([Wang_engle, T_base_op_ceiling, T_base_opt],[{"Tbase":8, "Topt":30, "Tcei":42},{"Tbase":8,
                                                                "Topt_low":25, "Topt_high":35, "Tcei":42,},{"Tbase":8, "Topt":30}]):
            for photofun,photofun_para in zip([photoeffect_yin, photoeffect_oryza2000, CERES_Rice,""],
                                                [{"mu":-15.46, "zeta":2.06, "ep":2.48},{"Dc":12.5,'PPSE':0.2},{"psr":100, "Do":12.5},""]):

                for quantile in np.arange(0.05,0.51,0.05):
                    dfcm = simulate_and_calibrate(thermal_fun=thermalfun, thermal_fun_para=thermalfun_para,
                                                photofun=photofun, photo_fun_para=photofun_para, dfws=dfws, df=gp, quantile=quantile)
                    print(thermalfun, photofun)
                    dfcm['thermalfun'] = thermalfun.__name__
                    if photofun == '':
                        print('here')
                        dfcm['photofun'] = ''
                        dfcm['model'] = thermalfun.__name__
                    else:
                        dfcm['photofun'] = photofun.__name__
                        dfcm['model'] = thermalfun.__name__ + '_' + photofun.__name__
                    dfcm['n_cluster'] = n_cluster
                    dfcm['cluster_vas'] = '_'.join(va)
                    dfcm['claster_number'] = ind
                    dfcm['quantiles'] = quantile
                    dfall=pd.concat([dfall,dfcm])
    return dfall

if __name__=="__main__":
    cluster_and_sim()
