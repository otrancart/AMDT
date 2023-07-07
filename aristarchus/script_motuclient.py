###########
# IMPORTS #
###########

import motuclient
import xarray as xr
import rioxarray
import matplotlib.pyplot as plt
import plotly.express as px
import os
import re
import json

import requests
from bs4 import BeautifulSoup

import general_function as gf



##################
# MOTU FUNCTIONS #
##################

# Functions from tutorial : 
# https://help.marine.copernicus.eu/en/articles/5211063-how-to-use-the-motuclient-within-python-environment

class MotuOptions:
    """used to parse the motuclient options from a dictionary"""
    def __init__(self, attrs: dict):
        super(MotuOptions, self).__setattr__("attrs", attrs)

    def __setattr__(self, k, v):
        self.attrs[k] = v

    def __getattr__(self, k):
        try:
            return self.attrs[k]
        except KeyError:
            return None
        

def motu_option_parser(script_template:str):
    """ 
        Parse options of motu request in a dictionnary

        Parameters
        ----------
        script_template : str
            motu API request-like with --options

        Returns
        -------
        dictionary : dict
            contains every motu options
    """
    dictionary = dict(
        [e.strip().partition(" ")[::2] for e in script_template.split('--')])
    dictionary['variable'] = [value for (var, value) in [e.strip().partition(" ")[::2] for e in script_template.split('--')] if var == 'variable']  # pylint: disable=line-too-long
    for k, v in list(dictionary.items()):
        if k in ['longitude-min', 'longitude-max', 'latitude-min', 
                 'latitude-max', 'depth-min', 'depth-max']:
            dictionary[k] = float(v)
        if k in ['date-min', 'date-max']:
            dictionary[k] = v[1:-1]
        dictionary[k.replace('-','_')] = dictionary.pop(k)
    dictionary.pop('python')
    dictionary['auth_mode'] = 'cas'
    return dictionary



#########################
# FUNCTIONS - INTERFACE #
#########################


def extract_json(URL:str):
    """ 
        Extract source code of link to json format 

        Parameters
        ----------
        URL : str
            link of a copernicus product (page)

        Returns
        -------
        PageElement
            source code of the webpage
    """
    page = requests.get(str(URL))
    soup = BeautifulSoup(page.content, "html.parser")
    json_script = soup.find(id="__NEXT_DATA__")
    return json_script



def get_products(JSON_SCRIPT):
    """ 
        Get all products ID (= datasets) 

        Parameters
        ----------
        JSON_SCRIPT : PageElement
            source code of a copernicus product (page)

        Returns
        -------
        list(str)
            ID of available products (datasets)
    """
    all_prod_id = []
    for prod in re.findall(r'product=[\w\_\-\.]+"',str(JSON_SCRIPT)):
        prod = prod.replace("product=","")
        prod = prod.replace('"',"")
        if (prod not in all_prod_id) and (prod!=""):
            all_prod_id.append(prod)
    return all_prod_id



def get_infos(JSON_SCRIPT,PRODUCT:str):
    """ 
        Get time range, depth range and all variables of a dataset

        Parameters
        ----------
        JSON_SCRIPT : PageElement
            source code of a copernicus product (page)
        PRODUCT : str
            ID of a dataset in this page

        Returns
        -------
        list:
            general infos of the dataset
            - [0] str : start date
            - [1] str : end date
            - [2] list(str) : depth = -dmax(int),-dmin(int),unit(str)
            - [3] list(str) : variables
    """
    json_object = json.loads(JSON_SCRIPT.contents[0])
    all_prod = json_object['props']['pageProps']['dataPackage']['dataset']['stacItems']
    
    # GET DATES
    for data in all_prod :
        if data.startswith(PRODUCT): 
            START_DATE = str(all_prod[data]['properties']['start_datetime'])
            START_DATE = START_DATE.replace('T00:00:00Z',"")
            END_DATE = str(all_prod[data]['properties']['end_datetime'])
            END_DATE = END_DATE.replace('T00:00:00Z',"")

            # GET DEPTH
            dims = all_prod[data]['properties']['cube:dimensions']
            for k in dims:
                if re.match("elevation",k):
                    D = dims['elevation']['extent']
                    D.append(str(dims['elevation']['unit']))
                    break
                else:
                    D = []

            # GET VARS
            with open("./variables.json","r") as f:
                vars_dict = json.load(f)

            vars = all_prod[data]['properties']['cube:variables']
            all_vars = []
            for k in vars:
                varname = str(vars[k]['name']['en'])
                if 'unit' in vars[k]:
                    varunit = str(vars[k]['unit'])
                else:
                    varunit = "u"
                all_vars.append(k)
                if k in vars_dict.keys():
                    pass
                else :
                    # Save variable name and unit in json file
                    vars_dict[k]=[varname,varunit]
                    vars_dict = json.dumps(vars_dict, indent = 4)
                    with open("./variables.json","w") as f:
                        f.write(vars_dict)

    return [START_DATE,END_DATE,D,all_vars]



def search_duplicate(JSON_SCRIPT,PRODUCT:str,VARIABLES:list):
    """ 
        Search if this copernicus product (=service) got another dataset (=product) with identical variable(s)

        Parameters
        ----------
        JSON_SCRIPT : PageElement)
            source code of a copernicus product
        PRODUCT : str
            name of a dataset in this page
        VARIABLES : list
            name of a variable in this dataset (str)

        Returns
        -------
        True 
            if another dataset in this service got same variable(s)
        False 
            if no duplicates found
    """
    json_object = json.loads(JSON_SCRIPT.contents[0])
    all_prod = json_object['props']['pageProps']['dataPackage']['dataset']['stacItems']
    
    # GET VARS OTHER PRODUCTS
    for data in all_prod :
        if not data.startswith(str(PRODUCT)): 
            if 'cube:variables' in all_prod[data]['properties']:
                vars = all_prod[data]['properties']['cube:variables']
                for k in vars: # check each var of other product
                    if k in VARIABLES: # if var present in chosen product
                        return True 
    return False



def get_prefix(PRODUCT:str):
    """ 
        Get prefix of the dataset

        Parameters
        ----------
        PRODUCT : str
            name of a dataset

        Returns
        -------
        str
            "no" if not found
    """
    with open("./prefix.json","r") as f:
        all_prefix = json.load(f)
    if PRODUCT in all_prefix.keys():
        return all_prefix[str(PRODUCT)]
    else:
        return "no"


def define_prefix(PRODUCT:str,PREFIX:str):
    """ 
        Save prefix of a dataset in prefix.json

        Parameters
        ----------
        PRODUCT : str
            name of a dataset
        PREFIX : str
            prefix of this dataset
    """
    # Save in json file
    with open("./prefix.json","r") as f:
        all_prefix = json.load(f)
    all_prefix[str(PRODUCT)]=str(PREFIX)
    all_prefix = json.dumps(all_prefix, indent = 4)
    with open("./prefix.json","w") as f:
        f.write(all_prefix)



def final_req(BDIR:str,JSON_SCRIPT,PRODUCT:str,PREFIX:str,VARIABLE:list,D:str,YEAR:str,USERNAME:str,PASSWORD:str):
    """ 
        Download subset dataset using motu fonctions

        Parameters
        ----------
        BDIR : str
            path to the backup folder
        JSON_SCRIPT : PageElement
            source code of a copernicus product
        PRODUCT : str
            name of a dataset in this page
        PREFIX : str
            prefix for this dataset
        VARIABLE : list(str)
            name of a variable in this dataset
        D : str
            depth range in format "--depth-min _dmin --depth-max _dmax" or "" if no depth
        YEAR : str
            year
        USERNAME : str
            username of copernicus account
        PASSWORD : str
            password of copernicus account

        Returns
        -------
        str
            name of output file already created, "" otherwise
    """
    path_coord = BDIR+"/coordinates.json"
    with open(path_coord,"r") as f:
        json_dict = json.load(f)
    LONG = json_dict["LONG"]
    LAT = json_dict["LAT"]

    # GET SERVICE ID
    SERVICE = re.search(r"service=[\w_-]+\\",str(JSON_SCRIPT))[0]
    SERVICE = SERVICE.replace("service=","")
    SERVICE = SERVICE.replace("\\","")

    # GET MOTU LINK
    MOTU = re.search(r'"motu":"[\w\:\/\.\-]+\?',str(JSON_SCRIPT))[0]
    MOTU = MOTU.replace('"motu":"',"")
    MOTU = MOTU.replace("?","")
    

    path = BDIR+"/NetCDF_files/"+SERVICE
    if not os.path.exists(path):
        os.mkdir(path)
    folder = gf.show_available_files_simple(BDIR+"/NetCDF_files",SERVICE)

    data_request_dict = []
    for i in range(len(VARIABLE)):
        # Add depth in name if available
        if str(D)!="":
            _dmin = str(D).split(" ")[1]
            _dmax = str(D).split(" ")[-1]
            OUTPUT_FILE = "["+_dmin+"-"+_dmax+"]"+VARIABLE[i]+'__'+YEAR
        else:
            OUTPUT_FILE = VARIABLE[i]+'__'+YEAR

        # Add prefix if 2 datasets with same variable
        if str(PREFIX)!="":
            f = str(PREFIX)+"pfx"+OUTPUT_FILE
            OUTPUT_FILE = f

        OUTPUT_FOLDER = os.path.join(BDIR,"NetCDF_files",SERVICE)
        
        # check if file already created
        if OUTPUT_FILE in folder:
            return OUTPUT_FILE

        req = 'python -m motuclient \
                --motu '+MOTU+' \
                --service-id '+SERVICE+' \
                --product-id '+str(PRODUCT)+' \
                --longitude-min '+str(LONG[0])+' --longitude-max '+str(LONG[1])+' \
                --latitude-min '+str(LAT[0])+' --latitude-max '+str(LAT[1])+' \
                --date-min "'+YEAR+'-01-01 00:00:00" --date-max "'+YEAR+'-12-30 23:59:59" \
                '+str(D)+' \
                --variable '+VARIABLE[i]+' \
                --out-dir '+OUTPUT_FOLDER+' --out-name '+OUTPUT_FILE+' \
                --user '+str(USERNAME)+' --pwd '+str(PASSWORD)

        data_request_dict.append(motu_option_parser(req))
    
    for i in range(len(data_request_dict)):
        motuclient.motu_api.execute_request(MotuOptions(data_request_dict[i]))

    return ""



def create_map_1d(FILEPATH:str,MONTH:str,DAY:str,DEPTH:float):
    """ 
        Create a map of 1 day of a NetCDF file

        Parameters
        ----------
        FILEPATH : str
            path to a NetCDF file
        MONTH : str
            month
        DAY : str
            day
        DEPTH : float
            depth

        Returns
        -------
        matplotlib figure
    """
    # Open and Read the file
    with xr.open_dataset(FILEPATH) as f:
        DS = f

    ### EXTRACT FROM FILENAME
    YEAR = FILEPATH.split('__')[-1]
    VAR_FULL = (FILEPATH.split('/')[-1]).split('__')[0]
    VAR = VAR_FULL.split("pfx")[-1]
    if "]" in VAR:
        VAR = VAR.split("]")[-1]

    if len(MONTH)==1:
        MONTH = '0'+str(MONTH)
    if len(DAY)==1:
        DAY = '0'+str(DAY)
    t = YEAR+'-'+str(MONTH)+'-'+str(DAY)

    # get var name and unit
    with open("./variables.json","r") as f:
        json_dict = json.load(f)
    VARID = VAR.split("pfx")[-1]
    VARID = VARID.split("]")[-1]
    if VARID in json_dict.keys():
        VARNAME = json_dict[VARID][0]
        VARUNIT = json_dict[VARID][1]

    # Plot a 2D map 
    if VAR == "analysed_sst":
        DS.analysed_sst.sel(time=t).plot()
    else:
        df = DS.to_dataframe()
        df1 = df.reset_index()
        if DEPTH!=0.0:
            df1 = df1.loc[(df1['time']==(t+'T12:00:00')) & (df1['depth']==DEPTH)]
        else :
            df1 = df1.loc[(df1['time']==(t+'T12:00:00'))]
        
        fig1, ax1 = plt.subplots()
        ax1.set_aspect('equal')
        if 'longitude' in list(df1.columns):
            tpc = ax1.tripcolor(df1['longitude'], df1['latitude'], df1[VAR])
        else :
            tpc = ax1.tripcolor(df1['lon'], df1['lat'], df1[VAR])
        fig1.colorbar(tpc).set_label(VARNAME+" in "+VARUNIT)
        if DEPTH!="":
            ax1.set_title("time = "+t+" / depth = "+str(DEPTH))
        else:
            ax1.set_title("time = "+t)
        ax1.set_xlabel("longitude [degrees_east]")
        ax1.set_ylabel("latitude [degrees_north]")
        return fig1




def create_map(FILEPATH:str,DEPTH:float,W:int,H:int,Z:int):
    """ 
        Create a map of 1 year or season or month statistics

        Parameters
        ----------
        FILEPATH : str
            path to a tif file
        DEPTH : float
            depth
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
    ### EXTRACT FROM FILENAME
    YEAR = FILEPATH.split('__')[-1]
    VAR_FULL = (FILEPATH.split('/')[-1]).split('__')[0]
    VAR = VAR_FULL.split("pfx")[-1]
    if "]" in VAR:
        VAR = VAR.split("]")[-1]

    # Open and Read the file
    with rioxarray.open_rasterio(FILEPATH,mask_and_scale=True) as f: # mark nodata as NaN
        DS = f
    DS = DS.rename(VAR) # need a name to be processed
    DS = DS.drop_vars("spatial_ref")


    # Plot a 2D map 
    df = DS.to_dataframe()
    df1 = ((df.reset_index()).drop(["band"],axis=1)).dropna() 
    df1 = df1.rename(columns={"x":"lon","y":"lat"})
    
    if DEPTH!=0.0:
        df1 = df1.loc[(df1['depth']==DEPTH)]
    
    fig1, ax1 = plt.subplots()
    fig1 = px.scatter_mapbox(df1,lat="lat",lon="lon",color=VAR,
                            mapbox_style="stamen-terrain",
                            title=YEAR,
                            width=W, height=H,zoom = Z)
    
    return fig1
    

         
def get_depths(FILEPATH:str,geotiff=False):
    """ 
        Get depth range of a dataset 

        Parameters
        ----------
        FILEPATH : str
            path to a NetCDF or a Geotiff file (precise geotiff=True)

        Returns
        -------
        list(float)
    """
    # Open and Read the file
    if geotiff==True :
        with rioxarray.open_rasterio(FILEPATH) as f:
            DS = f
        DS = DS.rename('name') # need a name to be processed
    else :
        with xr.open_dataset(FILEPATH) as f:
            DS = f
    df = DS.to_dataframe()
    df = df.reset_index()
    if 'depth' in list(df.columns):
        return df['depth'].unique().tolist()
    else:
        return []