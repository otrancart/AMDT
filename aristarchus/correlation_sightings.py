###########
# IMPORTS #
###########

import os

import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

import general_function as gf

#########################
# FUNCTIONS - INTERFACE #
#########################


def correlation(BDIR:str,CSVPATH:str,SERVICE:str,SAVE=True):
    """ 
        Correlation an environmental variable with sightings

        Save data into :
            - <BDIR>/Results/<SERVICE>/<PRODUCT>__<CSVFILE>-CORR.csv

        With data (sep=,):
            Latitude, Longitude, Date, Occurrences, <var>

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        CSVPATH : str
            path of the csv file containing sightings, columns names 'Latitude', 'Longitude', 'Date', 'Occurrences'
        SERVICE : str
            name of the service

        Returns
        -------
        list of DataFrame
    """
    result = []
    # Read points from csv
    all_pts = pd.read_csv(str(CSVPATH))
    # get time range occurrences
    pts_miny =  pd.to_datetime(all_pts[['Date']].min().Date, format='mixed').year
    pts_maxy =  pd.to_datetime(all_pts[['Date']].max().Date, format='mixed').year


    prods = gf.show_available_files_simple(BDIR+"/NetCDF_files",SERVICE)
    for product in prods:
        # verif if year present in occurrence file
        YEAR = product.split('__')[-1] ### EXTRACT FROM FILENAME
        if (int(YEAR) < pts_miny) or (int(YEAR) > pts_maxy):
            result.append(pd.DataFrame())
            pass
        else:
            # filter by year
            pts = all_pts[(all_pts['Date'].str.contains(YEAR))].reset_index()

            # Sample the raster at every point location and store values in DataFrame
            path_to_file = str(BDIR)+'/NetCDF_files/'+str(SERVICE)+"/"+product
            ds = xr.open_dataset(path_to_file)
            df = ds.to_dataframe().reset_index()

            # Check if this is a monthly file
            all_dates = df['time'].unique()
            if len(all_dates)<13:
                return pd.DataFrame()

            # Get lat and lon names
            latname = "lat"
            lonname = "lon"
            for c in df.columns:
                if 'lat' in c.lower():
                    latname = c
                if 'lon' in c.lower():
                    lonname = c
                    
            if'depth' in df.columns:
                colsearch = ['time',latname,lonname,'depth']
            else:
                colsearch = ['time',latname,lonname]
            
            # get resolution
            lat = ds[latname] 
            lon = ds[lonname] 
            lat_res = abs(lat[1] - lat[0]).values 
            lon_res = abs(lon[1] - lon[0]).values 
        

            ### EXTRACT FROM FILENAME
            VAR_FULL = product.split('__')[0]
            VAR = VAR_FULL.split("pfx")[-1]
            D = ""
            if "]" in VAR:
                D = VAR.split("]")[0]
                D = D.replace("[","")
                VAR = VAR.split("]")[-1]


            data = []
            for i in range(len(pts)):
                # get date of occ
                _date = pd.to_datetime(pts.at[i,'Date'], format='mixed')
                
                # get lat and lon of occ
                _lat = float(pts.at[i,'Latitude'])
                _long = float(pts.at[i,'Longitude'])

                # search at lat and lon in netcdf
                try :
                    closest_point = ds.sel(time=_date,lon=_long, lat=_lat, method='nearest')
                except :
                    closest_point = ds.sel(time=_date,longitude=_long, latitude=_lat, method='nearest')
                if len(closest_point.dims)==0:
                    closest_point = closest_point.expand_dims(VAR)
                df_CP = closest_point.to_dataframe().reset_index()
                
                # check if lat lon in range
                lat_found = df_CP[latname][0]
                lon_found = df_CP[lonname][0]
                if (abs(_lat-lat_found) > lat_res) or (abs(_long-lon_found) > lon_res):
                    data_mean = None
                    pass
                else :
                    df_CP = df_CP.drop(colsearch,axis=1)
                    if len(df_CP)>1:
                        data_mean = df_CP[VAR].dropna(how='any').mean()
                    else :
                        data_mean = df_CP.at[0,VAR]

                data.append(data_mean)
            pts[VAR] = data
            pts = pts.loc[:, ~pts.columns.str.contains('^Unnamed')].drop("index",axis=1)

            # Save in file
            if SAVE == True:
                path = str(BDIR)+"/Results/"+str(SERVICE)
                if not os.path.exists(path):
                    os.mkdir(path)
                output_file = path+"/"+product+"__"+(str(CSVPATH).split("/")[-1]).replace(".csv","")+"-CORR.csv"
                pts.to_csv(output_file, sep=',', encoding='utf-8')
            
            result.append(pts)
    return result



def get_occ_infos(CSVPATH:str):
    """
        Get available years and occurrences name in the csv file.

        Parameters
        ----------
        CSVPATH : str
            path to a csv file

        Returns
        -------
        list(int)
        list(str)
    """
    df = pd.read_csv(str(CSVPATH))
    
    all_y = []
    for d in df['Date']:
        year = pd.to_datetime(str(d), format='mixed').year
        if year not in all_y:
            all_y.append(year)

    occ = df['Occurrences'].unique()
    return all_y,occ



def create_map_occ(CSVPATH:str,YEARS:list,OCC:list,W:int,H:int,Z:int):
    """ 
        Create a map of occurrences for all years

        Parameters
        ----------
        CSVPATH : str
            path to a csv file
        YEARS : list
            year of occurrences of CSVPATH to show (str,int)
        OCC : list
            type of occurrences of CSVPATH to show (str)
        W : int
            width of the map
        H : int
            height of the map
        Z : int
            zoom of the map

        Returns
        -------
        matplotlib figure
    """
    # Open and Read the file
    df = pd.read_csv(str(CSVPATH))

    data_map = pd.DataFrame()
    for year in YEARS:
        df_year = df[(df['Date'].str.contains(str(year)))]
        data_map = pd.concat([data_map,df_year])
    data_map = data_map.reset_index()

    i = 0
    for o in data_map['Occurrences']:
        if o not in OCC:
            data_map = data_map.drop(i)
        i+=1

    fig1, ax1 = plt.subplots()
    fig1 = px.scatter_mapbox(data_map,lat="Latitude",lon="Longitude",color="Occurrences",
                            mapbox_style="stamen-terrain",
                            width=W, height=H,zoom = Z)
    
    return fig1



def merge_all_CORR(BDIR:str,CSVFILE:str):
    """ 
        Merge correlations of all the csv files of all variables

        Save data into:
            - <BDIR>/<CSVFILE>-ALLCORR.csv

        With data (sep=,):
            Latitude, Longitude, Date, Occurrences, <fullvar>

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        CSVFILE : str
            name of the csv file containing sightings
        
        Returns
        -------
        DataFrame
    """
    filelist = gf.show_available_files(BDIR,'Results')
    end = "__"+str(CSVFILE).split(".")[0]+"-CORR.csv"

    # TURN INTO DATAFRAME
    all_data = pd.DataFrame()
    var_names = []
    path_to_results = os.path.join(str(BDIR),'Results')
    for service in list(filelist.keys()):
        all_data_1var = pd.DataFrame()
        for file in filelist[service]:
            if file.endswith(end): # GET CORR ONLY
                path_to_file = os.path.join(path_to_results,service)
                path_to_file = os.path.join(path_to_file,file)
                df = pd.read_csv(path_to_file,index_col=0,sep=",") 
                all_data_1var = pd.concat([all_data_1var,df])

                varname = file.split("__")[0]
                if varname not in var_names:
                    var_names.append(varname)

        if not all_data_1var.empty:
            all_data_1var.replace("", float('nan'), inplace=True)
            colonnes = list(all_data_1var.columns)
            colonnes.remove("Date")
            colonnes.remove("Latitude")
            colonnes.remove("Longitude")
            colonnes.remove("Occurrences")
            aggf = {}
            for c in colonnes:
                aggf[c]='sum'
            all_data_1var = all_data_1var.groupby(['Date', 'Latitude', 'Longitude', 'Occurrences']).agg(aggf).reset_index()
            #all_data_1var.replace(0.0, "", inplace=True)

            if all_data.empty:
                all_data = all_data_1var
            else:
                all_data = pd.merge(all_data, all_data_1var,on=["Date","Latitude","Longitude","Occurrences"],how="outer") # on=["Date","Latitude","Longitude","Occurrences"]

            colonnes = list(all_data.columns)
            colonnes.remove("Date")
            colonnes.remove("Latitude")
            colonnes.remove("Longitude")
            colonnes.remove("Occurrences")
            for i in range(len(colonnes)):
                c = i+1
                all_data = all_data.rename(columns={colonnes[-c]:var_names[-c]})

    all_data = all_data.sort_values(by=['Date'])

    # save in file
    output_file = str(BDIR)+"/"+str(CSVFILE).split(".")[0]+"-ALLCORR.csv"
    all_data.to_csv(output_file,sep=',')

    return all_data
