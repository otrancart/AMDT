###########
# IMPORTS #
###########

import cftime 
from functools import partial

import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import dates
import matplotlib.cm as cm
import seaborn as sns


import pandas as pd
import os
import json

from scipy import stats 
from scipy.stats import t
from statsmodels.tsa.seasonal import STL

import general_function as gf



#########################
# FUNCTIONS - INTERFACE #
#########################


def moving_window(BDIR:str,FILEPATH:str,WIN:int):
    """ 
        Computing moving window -7 days- of a NetCDF file
        MW : average and standard deviation of a variabe over the whole area at 1 day 
        
        Save data into (depth or no):
            - <BDIR>/Results/<service>/<var>__<year>__<WIN>-MW.txt
            - <BDIR>/Results/<service>/[<depth>]<var>__<year>__<WIN>-MW.txt
            - <BDIR>/Results/<service>/<prefix>pfx<var>__<year>__<WIN>-MW.txt
            - <BDIR>/Results/<service>/<prefix>pfx[<depth>]<var>__<year>__<WIN>-MW.txt

        With data (sep=,):
            index(no name),day(time),average(avg),standard deviation(std)

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        FILEPATH : str
            path to a NetCDF file
        WIN : int
            number of days in the window

        Returns
        -------
        matplotlib figure
            None if the NetCDF file is hourly
    """
    with xr.open_dataset(FILEPATH) as ds:
        df = ds.to_dataframe()
    df = df.reset_index()

    # Check if this is a hourly file
    all_dates = df['time'].unique()
    if len(all_dates)>367:
        return None

    ### EXTRACT FROM FILENAME
    SERVICE = os.path.split(os.path.split(FILEPATH)[0])[1]
    YEAR = FILEPATH.split('__')[-1]
    VAR_FULL = (os.path.split(FILEPATH)[1]).split('__')[0]
    VAR = VAR_FULL.split("pfx")[-1]
    D = ""
    if "]" in VAR:
        D = VAR.split("]")[0]
        D = D.replace("[","")
        VAR = VAR.split("]")[-1]


    # Get unique dates in NetCDF
    all_dates = df['time'].unique()
    # Get window center -1
    if WIN%2 == 0:
        WINDOW_CENTER = int((WIN/2) -1)
    else : 
        WINDOW_CENTER = int(((WIN+1)/2) -1)

    # Create data
    all_data = {'time':[],'avg':[],'std':[]} 
    for idx in range(len(all_dates)-WIN+1):
        window=all_dates[idx:idx+WIN] # days concerning window
        all_data['time'].append(all_dates[idx+WINDOW_CENTER]) # date = window center
        # get statistics
        avg = df.loc[df["time"].isin(window),VAR].mean()
        all_data['avg'].append(avg)
        std = df.loc[df["time"].isin(window),VAR].std()
        all_data['std'].append(std)
        idx+=1
    df = pd.DataFrame(all_data)
    
    # save in file
    path = os.path.join(str(BDIR),"Results",SERVICE)
    if not os.path.exists(path):
        os.mkdir(path)
    output_file = os.path.join(path,VAR_FULL+"__"+str(YEAR)+"__"+str(WIN)+"-MW.txt")
    df.to_csv(output_file,sep=',')

    ################ TO ADAPT ################
    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID = VAR.split("pfx")[-1]
    VARID = VARID.split("]")[-1]
    if VARID in json_dict.keys():
        VARNAME = json_dict[VARID][0]
        VARUNIT = json_dict[VARID][1]

    # plot data  
    cols = list(df.columns)
    fig1, ax1 = plt.subplots()
    ax1.errorbar(x=df[cols[0]],y=df[cols[1]],yerr=df[cols[2]])
    if D!="":
        ax1.set_title("Moving Window "+VARNAME+" d=["+D+"] "+YEAR)
    else:
        ax1.set_title("Moving Window "+VARNAME+" "+YEAR)
    ax1.set_xlabel("window : 7 days")
    ax1.xaxis.set_major_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.grid(True)
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%b 04'))
    for tick in ax1.get_xticklabels():
        tick.set_rotation(90)
    ax1.set_ylabel(VARID+" in "+VARUNIT)

    return fig1



def read_MW(FILEPATH:str):
    """ 
        Show moving window of a txt file

        Parameters
        ----------
        FILEPATH : str
            path of a NetCDF file

        Returns
        -------
        matplotlib figure
    """
    ### EXTRACT FROM FILENAME
    YEAR = str(FILEPATH).split('__')[1]
    VAR_FULL = (os.path.split(str(FILEPATH))[1]).split('__')[0]
    VAR = VAR_FULL.split("pfx")[-1]
    D = ""
    if "]" in VAR:
        D = VAR.split("]")[0]
        D = D.replace("[","")
        VAR = VAR.split("]")[-1]

    df = pd.read_csv(str(FILEPATH),index_col=0,sep=",") 

    ################ TO ADAPT ################
    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID = VAR.split("pfx")[-1]
    VARID = VARID.split("]")[-1]
    if VARID in json_dict.keys():
        VARNAME = json_dict[VARID][0]
        VARUNIT = json_dict[VARID][1]

    # plot data
    cols = list(df.columns)
    fig1, ax1 = plt.subplots()
    ax1.errorbar(x=df[cols[0]],y=df[cols[1]],yerr=df[cols[2]])
    if D!="":
        ax1.set_title("Moving Window "+VARNAME+" d=["+D+"] "+YEAR)
    else:
        ax1.set_title("Moving Window "+VARNAME+" "+YEAR)
    ax1.set_xlabel("window : 7 days")
    ax1.xaxis.set_major_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.grid(True)
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%b 04'))
    for tick in ax1.get_xticklabels():
        tick.set_rotation(90)
    ax1.set_ylabel(VARID+" in "+VARUNIT)

    return fig1



# Thank you stackoverflow.com
def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)



def read_all_MW(BDIR:str,SERVICE:str,VAR:str):
    """ 
        Show moving window of all the txt files concerning a variable of a specific service

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        SERVICE : str
            name of a service
        VAR : str
            name of a variable with pfx, depth and window
        DATEMIN : Timestamp
            minimum date of sightings correlation

        Returns
        -------
        matplotlib figure, DataFrame MW, DataFrame MW 12 months
    """
    path_to_results = os.path.join(str(BDIR),'Results')
    WIN = str(VAR).split("-")[-1]
    end = "__"+WIN+"-MW.txt"

    # GET MW
    all_files = []
    filelist = gf.show_available_files_simple(path_to_results,SERVICE)
    for file in filelist:
        if file.endswith(end) and (str(VAR).replace("-"+WIN,"") in file):
            all_files.append(file)
    

    # TURN INTO DATAFRAME
    all_data = pd.DataFrame()
    for file in all_files:
        path_to_file = os.path.join(path_to_results,str(SERVICE),file)

        df = pd.read_csv(path_to_file,index_col=0,sep=",") 
        all_data = pd.concat([all_data,df])
    
    all_data = all_data.sort_values(by=['time'])
    # fill data
    min_d = all_data['time'].min()
    max_d = all_data['time'].max()
    dates = pd.DataFrame(pd.date_range(start=min_d, end =max_d, freq='D'))
    dates = dates.rename(columns={0:"time"})
    # sandardize dates
    to_datetime_fmt = partial(pd.to_datetime, format='mixed') #format='%Y-%m-%d')
    all_data['time'] = all_data['time'].apply(to_datetime_fmt)
    all_data = dates.merge(all_data, how='left', on='time') # dates added to all_data with NaN
    all_data = all_data.interpolate()

    cols = list(all_data.columns)


    # MW 12 months
    df_trend = pd.DataFrame()
    trend_dates = all_data['time'].unique()
    trend = {'time':[],'avg':[]} 
    for idx in range(len(trend_dates)-366):
        window=trend_dates[idx:idx+365] # 365 days
        trend['time'].append(trend_dates[idx+182]) # date = window center
        # Get average
        avg = all_data.loc[all_data["time"].isin(window),cols[1]].mean()
        trend['avg'].append(avg)
        idx+=1
    df_trend = pd.DataFrame(trend)

    ################ TO ADAPT ################
    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID = str(VAR).split("pfx")[-1]
    VARID = VARID.split("]")[-1]
    VARID = VARID.split("-")[0]
    if VARID in json_dict.keys():
        VARNAME = json_dict[VARID][0]
        VARUNIT = json_dict[VARID][1]


    # plot data    
    sns.set_style("ticks")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.errorbar(x=all_data[cols[0]],y=all_data[cols[1]],yerr=all_data[cols[2]],elinewidth=0.1,label=WIN+" days window")
    ax1.set_title("Moving Window "+VARNAME)
    #ax1.xaxis.set_major_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.grid(True)
    #ax1.xaxis.set_major_formatter(dates.DateFormatter('%b 04'))
    ax1.set_ylabel(VARID+" in "+VARUNIT)

    if not df_trend.empty :
        cols = list(df_trend.columns)
        ax1.errorbar(x=df_trend[cols[0]],y=df_trend[cols[1]],linewidth = 2,label="12 months window")
    ax1.legend(loc='upper left')

    return fig1,ax1,all_data,df_trend



def read_all_MW_CORR(DATA:pd.DataFrame,VAR:str,DATEMIN):
    """ 
        Plot moving window until a certain date

        Parameters
        ----------
        DATA : DataFrame
            moving window
        VAR : str
            name of a variable with pfx, depth and window
        DATEMIN : Timestamp
            minimum date of sightings correlation

        Returns
        -------
        matplotlib figure
    """
    cols = list(DATA.columns)

    # Get data only starting by datemin
    try :
        min_idx = DATA.set_index('time').index.get_loc(DATEMIN)
        all_data = DATA.iloc[min_idx:]
    except :
        DATEMIN= str(DATEMIN).replace(" 00:00:00"," 12:00:00")
        min_idx = DATA.set_index('time').index.get_loc(DATEMIN)
        all_data = DATA.iloc[min_idx:]
    

    WIN = str(VAR).split("-")[-1]
    ################ TO ADAPT ################
    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID = str(VAR).split("pfx")[-1]
    VARID = VARID.split("]")[-1]
    VARID = VARID.split("-")[0]
    if VARID in json_dict.keys():
        VARNAME = json_dict[VARID][0]
        VARUNIT = json_dict[VARID][1]


    # plot data    
    sns.set_style("ticks")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.errorbar(x=all_data[cols[0]],y=all_data[cols[1]],yerr=all_data[cols[2]],elinewidth=0.1,label=WIN+" days window")
    ax1.set_title("Moving Window "+VARNAME)
    #ax1.xaxis.set_major_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.grid(True)
    #ax1.xaxis.set_major_formatter(dates.DateFormatter('%b 04'))
    ax1.set_ylabel(VARID+" in "+VARUNIT)


    return fig1,ax1



def get_corr(BDIR:str,SERVICE:str,VAR:str):
    """ 
        Get correlations availables between variable and sightings

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        SERVICE : str
            name of a service
        VAR : str
            name of a variable

        Returns
        -------
        DataFrame 
            columns='Date','<var>','Occurrences'
        list (str)
            occurrences
    """
    path_to_results = os.path.join(str(BDIR),'Results')
    WIN = str(VAR).split("-")[-1]
    FULLVAR = str(VAR).replace("-"+WIN,"")

    # GET CORRELATIONS
    all_files = []
    filelist = gf.show_available_files_simple(path_to_results,SERVICE)
    for file in filelist:
        if file.endswith("CORR.csv") and (FULLVAR in file):
            all_files.append(file)
    if all_files == []:
        return pd.DataFrame,[]

    # TURN INTO DATAFRAME
    VARID = FULLVAR.split("pfx")[-1]
    VARID = VARID.split("__")[0]
    VARID = VARID.split("]")[-1]

    all_data = pd.DataFrame()
    for file in all_files:
        path_to_file = os.path.join(path_to_results,str(SERVICE),file)

        df = pd.read_csv(path_to_file,index_col=0,sep=",") 
        all_data = pd.concat([all_data,df])

    all_data = all_data.sort_values(by=['Date'])
    all_data = all_data.reset_index()

    occ = list(all_data['Occurrences'].unique())

    x = all_data['Date']
    y = all_data[VARID]
    lab = all_data['Occurrences']

    to_datetime_fmt = partial(pd.to_datetime, format='mixed') #format='%Y-%m-%d')
    x = x.apply(to_datetime_fmt)
    df = pd.DataFrame({'Date':x,VARID:y,'Occurrences':lab})

    return df,occ



def plot_corr(FIG,AX,VAR:str,DF:pd.DataFrame,OCC:list):
    """ 
        Add points of occurrences data on read_all_MW

        Parameters
        ----------
        FIG,AX : matplolib figure 
            figure from read_all_MW
        VAR : str
            name of a variable
        DF : DataFrame
            sightings with 'Date','<VAR>','Occurrences'
        OCC : list (str)
            all occurrences to show

        Returns
        -------
        matplotlib figure
    """
    WIN = str(VAR).split("-")[-1]
    FULLVAR = str(VAR).replace("-"+WIN,"")
    VARID = FULLVAR.split("pfx")[-1]
    VARID = VARID.split("]")[-1]

    dfcorr = DF[DF['Occurrences'].isin(OCC)]

    sns.set_style("ticks")

    cmap = get_cmap(len(dfcorr['Occurrences'].unique())+1)
    i=0
    for label, df in dfcorr.groupby('Occurrences'):
        df.plot(x='Date',y=VARID,s=5,kind="scatter",ax=AX, label=label,c=cmap(i))
        i+=1
    AX.legend(loc='upper left')
    return FIG
    


def compare_MW(BDIR:str,SERVICE1:str,VAR1:str,SERVICE2:str,VAR2:str):
    """ 
        Compare moving window of 2 datasets

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        SERVICE1 : str
            name of a service
        VAR1 : str
            name of a variable
        SERVICE2 : str
            name of a service
        VAR2 : str
            name of a variable

        Returns
        -------
        matplotlib figure
    """
    path_to_results = os.path.join(str(BDIR),'Results')

    # GET MW
    all_files1 = []
    filelist1 = gf.show_available_files_simple(path_to_results,SERVICE1)
    for file in filelist1:
        if file.endswith("MW.txt") and (str(VAR1) in file):
            all_files1.append(file)
    
    all_files2 = []
    filelist2 = gf.show_available_files_simple(path_to_results,SERVICE2)
    for file in filelist2:
        if file.endswith("MW.txt") and (str(VAR2) in file):
            all_files2.append(file)
    

    # TURN INTO DATAFRAME
    all_data = pd.DataFrame()
    path_to_results = os.path.join(str(BDIR),'Results')
    for file in all_files1:
        path_to_file = os.path.join(path_to_results,str(SERVICE1),file)

        df = pd.read_csv(path_to_file,index_col=0,sep=",") 
        df = df.rename(columns={"avg":str(SERVICE1)+"_"+str(VAR1)+"_avg","std":str(SERVICE1)+"_"+str(VAR1)+"_std"})
        all_data = pd.concat([all_data,df])

    for file in all_files2:
        path_to_file = os.path.join(path_to_results,str(SERVICE2),file)

        df = pd.read_csv(path_to_file,index_col=0,sep=",") 
        df = df.rename(columns={"avg":str(SERVICE2)+"_"+str(VAR2)+"_avg","std":str(SERVICE2)+"_"+str(VAR2)+"_std"})
        all_data = pd.concat([all_data,df])
    
    all_data = all_data.sort_values(by=['time'])
    # fill data
    min_d = all_data['time'].min()
    max_d = all_data['time'].max()
    dates = pd.DataFrame(pd.date_range(start=min_d, end =max_d, freq='D'))
    dates = dates.rename(columns={0:"time"})
    # sandardize dates
    to_datetime_fmt = partial(pd.to_datetime, format='mixed') #format='%Y-%m-%d')
    all_data['time'] = all_data['time'].apply(to_datetime_fmt)
    all_data = dates.merge(all_data, how='left', on='time') # dates added to all_data with NaN

    ################ TO ADAPT ################
    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID1 = str(VAR1).split("pfx")[-1]
    VARID1 = VARID1.split("]")[-1]
    if VARID1 in json_dict.keys():
        VARNAME1 = json_dict[VARID1][0]
        VARUNIT1 = json_dict[VARID1][1]
    VARID2 = str(VAR2).split("pfx")[-1]
    VARID2 = VARID2.split("]")[-1]
    if VARID2 in json_dict.keys():
        VARNAME2 = json_dict[VARID2][0]
        VARUNIT2 = json_dict[VARID2][1]

    # plot data
    cols = list(all_data.columns)
   
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.errorbar(x=all_data[cols[0]],y=all_data[cols[1]],yerr=all_data[cols[2]],fmt="-",elinewidth=0.1,color='r')    
    ax1.set_ylabel("Service 1: "+VARNAME1+" in "+VARUNIT1)
    for t in ax1.get_yticklabels():
        t.set_color('r')

    ax2 = ax1.twinx()
    ax2.errorbar(x=all_data[cols[0]],y=all_data[cols[3]],yerr=all_data[cols[4]],fmt="-",elinewidth=0.1,color='b')
    ax2.set_ylabel("Service 2: "+VARNAME2+" in "+VARUNIT2)
    for t in ax2.get_yticklabels():
        t.set_color('b')

    ax1.set_title("Moving Window comparison, window : 7 days")
    ax1.xaxis.grid(True)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(45)

    return fig1, ax1, ax2



def regression(DF:pd.DataFrame):
    """ 
        Get Linear Regression results

        Parameters
        ----------
        DF : DataFrame or Series
            moving window data

        Returns
        -------
        results object
    """
    if isinstance(DF, pd.DataFrame):
        col = DF['avg']
        idx = DF.index
    else : 
        col = DF
        DF1 = DF.reset_index()
        idx = DF1.index
    # get linear regression on 12 months data
    res = stats.linregress(idx, col)

    # 95% confidence interval on slope and intercept
    tinv = lambda p, df: abs(t.ppf(p/2, df))
    ts = tinv(0.05, len(col)-2)
    
    sns.set_style("whitegrid")
    return res,ts



def stl_test(DF:pd.DataFrame):
    """ 
        Get Seasonal-Trend decomposition using LOESS results

        Parameters
        ----------
        DF : DataFrame
            moving window data, daily frequency

        Returns
        -------
        matplotlib figure
    """
    DF = DF.drop('std',axis=1) # DF.index.freq = D
    DF.time = pd.to_datetime(DF.time)
    df1 = DF.resample('M', on='time').mean()

    sns.set_style("whitegrid")
    plt.rc("figure", figsize=(16, 12))
    plt.rc("font", size=13)

    # seasonal tells STL how many full seasons to use in the seasonal LOWESS but doesn't tell STL how many observations are needed for a full period.
    stl = STL(df1)
    res = stl.fit()
    fig = res.plot()
    return fig,res
