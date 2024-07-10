import pandas as pd
import os,sys
import matplotlib.pyplot as plt
import seaborn as sns
cur_dir=os.path.dirname(os.path.realpath(__file__))
os.chdir(cur_dir)
pd.options.display.max_columns = 999
def count_mature_days():
    df=pd.read_csv('../data/cluster_and_sim.csv', on_bad_lines='skip')
    dfna=df[(df.delta_days.isna())&(~df.ob_date.isna())&(df.DStage=='maturity date')]
    dfnaqc=dfna.groupby(['model','cluster_vas','n_cluster','quantiles']).count()['lat'].reset_index().rename(columns={'lat':'Not_maturation_count'})
    
    dfnotna=df[(~df.delta_days.isna())&(~df.ob_date.isna())&(df.DStage=='maturity date')]
    dfnotna=dfnotna[dfnotna.abs_delta_days!='abs_delta_days']
    dfnotna.abs_delta_days=dfnotna.abs_delta_days.astype(float)
    dferror_by_quan=dfnotna[['model','cluster_vas','n_cluster','quantiles','abs_delta_days']].groupby(['model','cluster_vas','n_cluster','quantiles']).mean().reset_index()
    dfme=dferror_by_quan.merge(dfnaqc,on=['model','cluster_vas','n_cluster','quantiles'])
    dfme.to_excel('../data/error_not_mature.xlsx',index=False)
    
def plot_quantile_error_non_mature_count():
    data=pd.read_excel('../data/error_not_mature.xlsx')
    data=data[data.cluster_vas=='lat_STM']
    fig, ax1 = plt.subplots()

    # Plot the first line with error bars
    sns.lineplot(x='quantiles', y='abs_delta_days', data=data, ax=ax1,  color='blue', err_style="bars", errorbar=("se", 2))

    ax1.set_xlabel('Quantiles for maturation threshold')
    ax1.set_ylabel('Mean absolute error (d)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create a second y-axis sharing the same x-axis
    ax2 = ax1.twinx()

    # Plot the second line with error bars
    sns.lineplot(x='quantiles', y='Not_maturation_count', data=data, ax=ax2, color='red', err_style="bars", errorbar=("se", 2))

    ax2.set_ylabel('Number of seasons with no maturation', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    # Save the figure
    fig.savefig('../fig/quantile_error_no.png',dpi=300)

def quantile_error_no_with_cluster():
    data=pd.read_excel('../data/error_not_mature.xlsx')
    data=data[data.cluster_vas=='lat_STM']
    fig, axes = plt.subplots(1,2,figsize=(8,4))
    ax1=axes[0]
    ax2=axes[1]
    data.n_cluster=data.n_cluster.astype(str)
    # Plot the first line with error bars
    sns.lineplot(x='quantiles', y='abs_delta_days', data=data, ax=ax1,  err_style="bars", errorbar=("se", 2), hue='n_cluster',hue_order=['1','3', '6',  '9', '12', '18', '24'])

    ax1.set_xlabel('Quantiles for maturation threshold')
    ax1.set_ylabel('Mean absolute error (d)', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    legend = ax1.legend(title='Cluster No.')


    # Plot the second line with error bars
    sns.lineplot(x='quantiles', y='Not_maturation_count', data=data, ax=ax2, legend=False,err_style="bars", errorbar=("se", 2), hue='n_cluster',hue_order=['1','3', '6',  '9', '12', '18', '24'])
    ax2.set_xlabel('Quantiles for maturation threshold')
    ax2.set_ylabel('Number of seasons with no maturation', color='black')
    ax2.tick_params(axis='y', labelcolor='black')
    # Save the figure
    fig.savefig('../fig/quantile_error_no_with_cluster.png',dpi=300)
    



if __name__=='__main__':
    plot_quantile_error_non_mature_count()
    quantile_error_no_with_cluster()
