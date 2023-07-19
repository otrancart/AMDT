###########
# IMPORTS #
###########

import streamlit as st
from streamlit_option_menu import option_menu
import mpld3
import streamlit.components.v1 as components
import pydeck as pdk
from PIL import Image


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import re

from datetime import date
import pymannkendall as mk

################ TO ADAPT ################
# Set working directory
if "aristarchus" not in os.getcwd():
    os.chdir("./aristarchus")

import script_motuclient as motu
import general_function as gf
import seasonnal_adjustment as sa
import correlation_sightings as corr
try:
    import script_qgis_software as soft
except:
    qgis_imported = False
else:
    qgis_imported = True


####################
# CACHED FUNCTIONS #
####################

# Streamlit runs your script from top to bottom at every user interaction or code change.
# whenever the function is called, it checks two things:
# - The values of the input parameters
# - The code inside the function


@st.cache_data(ttl=1800) # 30 minutes
def example_data():
    """ About - example tables """
    data1 = pd.DataFrame({'time':["2000-06-03 12:00:00"],'avg':["42.02893"],'std':["0.273928"]})
    data2 = pd.DataFrame({'Latitude':["42.23238"],'Longitude':["42.23238"],'Date':["03/06/2000"],'Species':["Pm"]})
    data3 = pd.DataFrame({'Latitude':["42.23238"],'Longitude':["42.23238"],'Date':["03/06/2000"],'Occurrences':["Pm"],'analysed_sst':["273.45"]})
    return data1,data2,data3


@st.cache_resource(ttl=3600) # 1 hour, all mutations on the function’s return value directly affect the object in the cache
def show_coordinates(LAT,LONG,chart_data):
    """ Set options - map """
    map = pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude=(float(LAT[0])+float(LAT[1]))/2,
                    longitude=(float(LONG[0])+float(LONG[1]))/2,
                    height=200,
                    zoom=6,
                    pitch=0,
                ),
                layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=chart_data,
                    pickable=True,
                    opacity=0.1,
                    stroked=False,
                    filled=True,
                    radius_scale=1,
                    radius_min_pixels=1,
                    radius_max_pixels=100,
                    line_width_min_pixels=1,
                    get_position='[lon, lat]',
                    get_radius=None,
                    get_color=[0,191,255],
                    get_line_color=[0, 0, 0],
                ),],)
    return map


@st.cache_data(ttl=900,show_spinner="Plotting general trend...") # 15 minutes
def run_all_MW(BDIR,SERVICE,VARIABLE):
    """ Meta-analysis - plot trend """
    mw,x,data,df_trend=sa.read_all_MW(BDIR,SERVICE,VARIABLE)
    figure = mpld3.fig_to_html(mw)
    return figure,data,df_trend,mw


@st.cache_data
def get_correlations(BDIR,SERVICE,VARIABLE):
    """ Meta-analysis - plot correlation, merge _CORR.csv files for a variable """
    df,spec = sa.get_corr(BDIR,SERVICE,VARIABLE)
    return df,spec


@st.cache_data(show_spinner="Plotting correlation...")
def plot_fig_corr(DATA,VARIABLE,_DMIN):
    """ Meta-analysis - plot correlation """
    fig,ax = sa.read_all_MW_CORR(DATA,VARIABLE,_DMIN)
    return fig,ax


@st.cache_data
def get_occ(CSVPATH):
    """ Show map - plot occurrences, get time range and occurrences categories """
    year,occ = corr.get_occ_infos(CSVPATH)
    return year,occ


#######################
# INTERFACE FUNCTIONS #
#######################

def filter_layers(all_prod:list,suffix:list):
    prodlist = []
    fullvariable = ""
    variables = []
    years_var = []
    all_years = {}
    for p in all_prod:
        # Get suffix
        prod = os.path.split(p)[1]
        suf = (((prod.split("avg")[-1]).split("std")[-1]).split("min")[-1]).split("max")[-1]
        if suf in suffix:
            prodlist.append(p)
            # Get variable name
            fullvariable = prod.split("__")[0]
            if fullvariable not in variables:
                variables.append(fullvariable)
                # Get year
                year = (prod.split("__")[-1]).split("_")[0]
                if years_var !=[]:
                    all_years[fullvariable]=years_var
                years_var = []
                years_var.append(year)
            else :
                # Get year
                year = (prod.split("__")[-1]).split("_")[0]
                if year not in years_var:
                    years_var.append(year)
    # last variable
    all_years[fullvariable]=years_var
    return prodlist,all_years,variables


def is_column_float(column):
    for item in column:
        if not isinstance(item, float):
            return False
    return True



########
# MAIN #
########

# GENERAL OPTIONS
st.set_page_config(
    page_title="Aristarchus MDT",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://github.com/otrancart/AMDT/issues",
        'About': None
    }
)

#st.markdown(""" <style>
#MainMenu {visibility: hidden;}
#footer {visibility: hidden;}
#</style> """, unsafe_allow_html=True)


# MENU SIDEBAR
image = Image.open('archi_logo.png')

with st.sidebar:
    col1_sidebar,col2_sidebar = st.columns([1.5,2])
    col1_sidebar.image(image, width=125)
    col2_sidebar.write("## :blue[Aristarchus] the MarineDataTrawler")
    col2_sidebar.write("produced by Archipelagos")

    choose = option_menu("Menu", ["About", "Set options", "Spatial analysis", "Meta-analysis", "Show map"],
                    icons=['house','pencil-square','pin-map-fill','search','map'],
                    # icons on https://icons.getbootstrap.com/
                    menu_icon="app-indicator", default_index=0,
                    styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "blue", "font-size": "20px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#6ADBDE"},
        }
    )


##########################################################################################################
##########################################################################################################
##########################################################################################################
if choose == "About":
    # Remove extra space
    st.write('<style>div.block-container{padding-top:2rem;padding-bottom:2rem;}</style>', unsafe_allow_html=True)
    
    st.title('Welcome to :blue[ARISTARCHUS] the :blue[MarineDataTrawler] !')

    st.write("""The purpose of Aristarchus the MarineDataTrawler is to make spatial analysis easier, using marine environmental variables 
    from [Copernicus](https://data.marine.copernicus.eu/products) database, such as 🌡️ sea surface temperature,
    🧂 salinity, 💚 plankton...""")
    st.write("You will need to create a [copernicus account](https://data.marine.copernicus.eu/register) in order to download satellite data in NetCDF files.")

    st.header("What is a NetCDF file?")
    st.write("""NetCDF (Network Common Data Form) is a file format for storing multidimensional scientific data.
    For each longitude, latitude and date, you will have a corresponding data. In **:blue[Spatial analysis]** 
    you can first create a NetCDF file for 1 year at a specific area.""")
    st.write("To change the desired coordinates, update it in **:blue[Set options]**")
    
    st.header("What will be created in the backup folder?")
    st.write("You can set the backup folder in **:blue[Set options]**")

    col1_about, col2_about = st.columns(2)
    with col1_about:
        st.write(" 3 folders will be created:")
        st.write("""
        - **NetCDF_files** : :green[.nc files], 1 file = 1 variable at 1 year at delimited depths if required
        - **Layers** : :green[.tif files] for statistics on each pixel
        - **Results** : 
            - :green[__MW.txt] are used to save moving window analysis, 
            - :green[__CORR.csv] are used to save correlation between species presence and variables data

        Each of these folders are divided in subfolders created automatically, each name correspond to 
        the name of the copernicus service providing the dataset(s). During NetCDF file creation you will 
        be asked to define prefix for datasets sharing same service and variable.""")
    with col2_about:
        d1,d2,d3 = example_data()
        st.write(d1)
        st.text("example of name__7-MW.txt data")
        st.write(d2)
        st.text("example of occurrences species.csv data")
        st.write(d3)
        st.text("example of name__species-CORR.csv data")


    st.header("Spatial analysis")
    st.write("In order to analyse an environmental variable you must first create a NetCDF file for this variable")
    st.write(""" You can either:
    - analyse the average of an environmental variable over the whole area within 1 year (moving window)
    - compute statistics (avg,std,min-max) of an environmental variable for each pixel using QGIS software
    - correlate occurrence data (coordinates and date) with the correspondent environmental variable within 1 year.
    To do this you will need to upload a csv containing the presence data (see species.csv example above) in **:blue[Spatial analysis]**""")
    
    st.header("Meta-analysis")
    st.write(""" This page is used to:
    - show general trend of a variable with all the MW analysis created for 1 dataset, 
    it will compute also a 12-months MW (can take few seconds) of all data. Several tests are
    performed : 
        - Linear regression 
        - Mann-Kendall Trend Test
        - Seasonal-Trend decomposition using LOESS

    - plot occurrences correlated on MW """)
    st.write("You can also compare 2 dataset moving windows.")
    


##########################################################################################################
##########################################################################################################
##########################################################################################################
elif (choose == "Set options"):
    ################ TO ADAPT ################
    # Get current options
    with open("./options.json","r") as f:
        json_dict = json.load(f)
    bdir = json_dict["backup_path"]
    qpath = json_dict["qgis_path"]
    ppath = json_dict["proc_path"]

    st.header('OPTIONS',anchor="1")

    #################
    # BACKUP FOLDER #
    #################
    bf = st.text_input('Backup folder',bdir)
    info1 = st.empty()
    info2 = st.empty()
    info3 = st.empty()

    if bf!=bdir:
        ################ TO ADAPT ################
        if bf.endswith("/"):
            bf = bf[:-1]
            st.info("Removing last /")
        try:           
            # Create folders
            path = os.path.join(bf,"Layers")
            if not os.path.exists(path):
                os.mkdir(path) 
                info1.text("Creating folder: Layers")

            path = os.path.join(bf,"NetCDF_files")
            if not os.path.exists(path):
                os.mkdir(path)
                info2.text("Creating folder: NetCDF_files")
            
            path = os.path.join(bf,"Results")
            if not os.path.exists(path):
                os.mkdir(path)
                info3.text("Creating folder: Results")
        except :
            st.error("This folder doesn't exist")
        else:
            ################ TO ADAPT ################
            # Save in options.json
            with open("./options.json","r") as f:
                json_dict = json.load(f)
            json_dict["backup_path"] = bf
            json_dict = json.dumps(json_dict, indent = 4)
            with open("./options.json","w") as f:
                f.write(json_dict)
            st.success('New path saved!', icon="✅")


    ###############
    # COORDINATES #
    ###############
    path_coord = os.path.join(bf,"coordinates.json")
    if os.path.exists(path_coord): 
        # Get coordinates of the folder
        with open(path_coord,"r") as f:
            json_dict = json.load(f)
        long = json_dict["LONG"]
        lat = json_dict["LAT"]
    else :
        long = [0,0]
        lat = [0,0]

    col1_options, col2_options,col3_options = st.columns([1,1,4])
    with col1_options:
        lon_min = st.text_input('Longitude min ↔',value=long[0])
        lat_min = st.text_input('Latitude min ↕',value=lat[0])
    with col2_options:
        lon_max = st.text_input('Longitude max ↔',value=long[1])
        lat_max = st.text_input('Latitude max ↕',value=lat[1])
    

    with st.expander("How to get coordinates"):
        st.write("Use the Corpernicus tool [My Ocean Pro](https://data.marine.copernicus.eu/viewer/expert)")


    # Check if coordinates are floats
    try:
        float(lon_min)
        float(lon_max)
        float(lat_min)
        float(lat_max)
        lat = [lat_min,lat_max]
        lon = [lon_min,lon_max]
    except:
        st.warning('Please enter decimal numbers only (with . not ,)', icon="⚠️")
        st.stop()


    # Set up data of the map
    latr = float(lat_max)-float(lat_min)
    lonr = float(lon_max)-float(lon_min)

    chart_data = pd.DataFrame(
    np.stack(
        (np.random.uniform(float(lon_min),float(lon_min)+lonr,size=10000),
        np.random.uniform(float(lat_min),float(lat_min)+latr,size=10000)),
        axis=0).T,
        columns=['lon', 'lat'])

    with col3_options:
        # Show map
        map_coord = show_coordinates(lat,long,chart_data)
        st.write(map_coord)


    col1b_options,col2b_options = st.columns([2,4])
    with col1b_options:
        ch_coord = st.button("Save coordinates",use_container_width=True)
    with col2b_options:
        st.warning('If you want to analyze another area, change the backup folder before save')
    

    if ch_coord:
        if (lon_min!=long[0]) or (lon_max!=long[1]) or (lat_min!=lat[0]) or (lat_max!=lat[1]):
            # Save in coordinates.json
            json_dict = {}
            json_dict["LONG"] = [lon_min,lon_max]
            json_dict["LAT"] = [lat_min,lat_max]
            json_dict = json.dumps(json_dict, indent = 4)
            with open(path_coord,"w") as f:
                f.write(json_dict)
            st.success('New coordinates saved!', icon="✅")
        else:
            st.info('Same coordinates')
        

    #############
    # QGIS PATH #
    #############
    qgis_path = st.text_input('QGIS path (last folder=:blue[qgis])',qpath)
    proc_path = st.text_input('Processing plugin path (last folder=:blue[plugins])',ppath)
    info = st.empty()

    with st.expander("How to get QGIS paths"):
        st.write("Search QGIS on Start menu and right-click on the software icon and search 'Open installation directory'.")
        st.write("For the Processing plugin, open QGIS, go to 'Extension' then 'Manage extensions' then find the Processing plugin and click on the installed version.")

    if (qgis_path and proc_path)!="":
        if (qgis_path!=qpath) or (proc_path!=ppath):
            ################ TO ADAPT ################
            if qgis_path.endswith("/"):
                qgis_path = qgis_path[:-1]
                st.info("Removing last /")
            if proc_path.endswith("/"):
                proc_path = proc_path[:-1]
                st.info("Removing last /")
            if (not os.path.exists(qgis_path)) or (not os.path.exists(proc_path)):
                st.error("This path doesn't exist")
                info.text("Actual qgis path: "+qpath+"\nActual processing plugin path: "+ppath)
            else :
                ################ TO ADAPT ################
                # Save in options.json
                with open("./options.json","r") as f:
                    json_dict = json.load(f)
                json_dict["qgis_path"] = qgis_path
                json_dict["proc_path"] = proc_path
                json_dict = json.dumps(json_dict, indent = 4)
                with open("./options.json","w") as f:
                    f.write(json_dict)
                st.success('New path saved!', icon="✅")
            
                # Import qgis module
                try:
                    import script_qgis_software as soft
                except:
                    qgis_imported = False
                    st.error("Wrong path")
                    st.stop()
                else:
                    qgis_imported = True
     


##########################################################################################################
##########################################################################################################
##########################################################################################################
elif choose == "Spatial analysis":
    # Remove extra space
    st.write('<style>div.block-container{padding-top:2rem;padding-bottom:2rem;}</style>', unsafe_allow_html=True)
    
    ################ TO ADAPT ################
    # Get path to backup folder
    with open("./options.json","r") as f:
        json_dict = json.load(f)
    bdir = json_dict["backup_path"]

    # Get coordinates
    path_coord = os.path.join(bdir,"coordinates.json")
    try:
        with open(path_coord,"r") as f:
            json_dict = json.load(f)
        lon = json_dict["LONG"]
        lat = json_dict["LAT"]
    except:
        st.error("File not found: "+path_coord)
        st.stop()
    
    choose_option = option_menu(None, ["Download a 1 year NetCDF file", "Daily average data", "Statistics on each pixel", "Upload an occurrences file", "Correlation with occurrences"],
                         default_index=0,
                         icons=['cloud-download','graph-up','grid','cloud-upload','link'],
                         # icons on https://icons.getbootstrap.com/
                         orientation="horizontal",
                         styles={
        "container": {"padding": "5!important", "background-color": "lavender"},
        "icon": {"color": "blue", "font-size": "20px"}, 
        "nav-link": {"font-size": "14.5px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#6ADBDE"},
        }
        )


    #################################
    # DOWNLOAD A 1 YEAR NETCDF FILE #
    #################################
    if choose_option=="Download a 1 year NetCDF file":
        # Get files in NetCDF file
        try:
            dirlist_nc = gf.show_available_files(bdir,"NetCDF_files")
        except:
            st.error("Folder not found: "+os.path.join(bdir,'NetCDF_files'))
            st.stop()


        # Availables NetCDF files and infos
        col1_netcdf, col2_netcdf = st.columns([2,1])
        with col2_netcdf: 
            st.write("__Current backup folder:__ "+os.path.split(bdir)[1])

            st.info("""The more the area is big and the dataset resolution is high, 
            the more time it will take to download the NetCDF file (few minutes, 
            depending on your internet connection). Each file is few MB.""")

            with st.expander('Current availables NetCDF files:'):
                st.write(dirlist_nc)
                
            st.info("[What is this variable ?](https://marine.copernicus.eu/glossary)")


        # Create NetCDF
        with col1_netcdf:
            st.write("Search for a dataset on https://data.marine.copernicus.eu/products")
            link = st.text_input('Paste the link of the dataset')

            # Check if URL is correct
            if (not re.match(r"https://data\.marine\.copernicus\.eu/product/",link)) and (link!=""):
                st.warning('Please paste a link starting by https://data.marine.copernicus.eu/product/...', icon="⚠️")
            elif re.match(r"https://data\.marine\.copernicus\.eu/product/",link):
                json_script = motu.extract_json(link)
                all_prod_id = motu.get_products(json_script)
                    
                # CHOOSE DATASET
                if all_prod_id==[]:
                    st.error("No dataset found")
                    st.stop()
                elif len(all_prod_id)>1:
                    product = st.selectbox('Choose the dataset', all_prod_id)
                else :
                    product = all_prod_id[0]
                    
                # GET INFOS DATASET
                infos = motu.get_infos(json_script,product)

                start_date = str(infos[0])
                end_date = str(infos[1])
                depth = infos[2]
                all_vars = infos[3]
                    
                # GET PREFIX DATASET
                pfx = motu.get_prefix(product)
                if pfx == "no": # no prefix found
                    pfx_check = motu.search_duplicate(json_script,product,all_vars)
                    if pfx_check == True: # duplicates found
                        _pfx = st.text_input('Define a prefix for this dataset:')
                        if _pfx == "":
                            st.stop()
                        else:
                            if not re.match(r"^[a-zA-Z0-9\-]+$", _pfx):
                                st.warning('Prefix contains forbidden characters, please use letters, digits or - only', icon="⚠️")
                                st.stop()
                            elif (_pfx!="no") and (_pfx!="pfx") and (_pfx!=""):
                                motu.define_prefix(product,_pfx)
                                pfx = _pfx
                                st.success('Prefix saved', icon="✅")
                                st.experimental_rerun()
                            else :
                                st.warning('Please choose another prefix', icon="⚠️")
                                st.stop()
                    else : # duplicates not found
                        pfx = ""
                        motu.define_prefix(product,pfx)
                st.info("Prefix for this dataset: "+pfx)

                # CHOOSE YEAR
                st.write("Available time range: "+start_date+" to "+end_date)
                if end_date[5:] != "12-31": # remove last year if not full
                    end_year = int(end_date[:4])-1
                    end_date = str(end_year)+end_date[4:]
                elipse = st.checkbox("All time range (not recommended)")
                if elipse:
                    year = [start_date.split('-')[0],end_date.split('-')[0]]
                    st.write(year)
                else :
                    year = st.slider('Pick a year', min_value=int(start_date.split('-')[0]), max_value=int(end_date.split('-')[0]))
                    
                # CHOOSE DEPTH RANGE
                if depth!=[]:
                    dmin = -infos[2][1]
                    dmax = -infos[2][0]
                    units = str(infos[2][2])
                    st.write("Available depth range: "+str(dmin)+" to "+str(dmax)+" in "+units)
                    _dmin = st.number_input('Min depth', int(dmin), int(dmax),step=1)
                    _dmax = st.number_input('Max depth', int(_dmin+1), int(dmax),step=1)
                    depth = "--depth-min "+str(_dmin)+" --depth-max "+str(_dmax)
                else :
                    depth = ""
                    
                # CHOOSE VARIABLES
                vars = st.multiselect('Variables', all_vars)

                if vars!=[]:
                    st.write("Copernicus account")
                    user = st.text_input('Enter your username:')
                    pwd = st.text_input('Enter your password:',type='password')
                                
                    create = st.button('Create NetCDF file')

                    if create:
                        if (user=="") or (pwd==""):
                            st.warning('Please enter your copernicus account', icon="⚠️")
                            st.stop()
                        alc = []
                        with st.spinner("Please wait few minutes..."):
                            if type(year)==list:
                                for y in range(int(year[0]),int(year[1])+1):
                                    filec = motu.final_req(bdir,json_script,product,pfx,vars,depth,str(y),user,pwd)
                                    if filec!="":
                                        alc.append(filec)
                            else :
                                filec = motu.final_req(bdir,json_script,product,pfx,vars,depth,str(year),user,pwd)
                                if filec!="":
                                    alc.append(filec)
                        if alc!=[]:
                            st.warning('File(s) already created: '+str(alc), icon="⚠️")
                            st.success('Other file(s) .nc saved in: '+bdir+'/NetCDF_files', icon="✅")
                        else :                
                            st.success('File(s) .nc saved in: '+bdir+'/NetCDF_files', icon="✅")
          

    ######################
    # DAILY AVERAGE DATA #
    ######################
    if choose_option=="Daily average data":
        tab1_MW, tab2_MW = st.tabs(["available MW", "create MW (.txt)"])
        
        # Availables MW 
        with tab1_MW: 
            try:
                dirlist_res = gf.show_available_files(bdir,"Results")
            except:
                st.error("Folder not found: "+os.path.join(bdir,'Results'))
                st.stop()
            
            if dirlist_res=={}:
                st.warning('No MW file found', icon="⚠️")
            else : 
                service_res_avMW = st.selectbox('Choose the service', dirlist_res.keys())
                if dirlist_res[service_res_avMW]==[]:
                    st.warning('No MW file found in '+service_res_avMW, icon="⚠️")
                else : 
                    # Get only MW files
                    product_all_avMW = []
                    for p in dirlist_res[service_res_avMW]:
                        if p.endswith("MW.txt"):
                            product_all_avMW.append(p) 
                    product_avMW = st.selectbox('Choose the dataset', product_all_avMW)
                    
                    # Path to MW
                    path_file_avMW = os.path.join(bdir,"Results",service_res_avMW,product_avMW)
                    # Plot MW
                    mw_graph = sa.read_MW(path_file_avMW)
                    st.pyplot(mw_graph)


        # Create MW
        with tab2_MW:
            try:
                dirlist_nc = gf.show_available_files(bdir,"NetCDF_files")
            except:
                st.error("Folder not found: "+os.path.join(bdir,'NetCDF_files'))
                st.stop()

            if dirlist_nc=={}:
                st.warning('No NetCDF file found', icon="⚠️")
            else : 
                col1_MW, col2_MW = st.columns([1,2])
                with col1_MW:
                    window = st.number_input("Window over 1 year(in days)", min_value=7, max_value=31, step=1)
                with col2_MW:
                    st.write("")
                    st.info("The more the window is large, the more data will be lost (start and end of year)")

                service_nc_MW = st.selectbox('Choose the service', dirlist_nc.keys(),key='mw')
                if dirlist_nc[service_nc_MW]==[]:
                    st.warning('No NetCDF file found', icon="⚠️")
                    st.stop()

                path_res = os.path.join(bdir,"Results",service_nc_MW)
                if os.path.exists(path_res):
                    # check if MW already created
                    filelist_res = gf.show_available_files_simple(os.path.split(path_res)[0],service_nc_MW)
                    for p in filelist_res:
                        prod = p.replace("-MW.txt","")
                        prod = prod.replace("__"+str(window),"")
                        if prod in dirlist_nc[service_nc_MW]:
                            dirlist_nc[service_nc_MW].remove(prod)
                    if dirlist_nc[service_nc_MW]==[]:
                        st.warning('All files already created', icon="⚠️")
                        st.stop()

                # Choose nb of MW to create
                nb = st.radio("Number of files",("one MW","several MW","all MW"))
                if nb=="one MW":
                    product_nc_MW = st.selectbox('Choose the dataset', dirlist_nc[service_nc_MW])
                elif nb=="several MW":
                    product_nc_MW = st.multiselect('Choose the datasets', dirlist_nc[service_nc_MW])
                elif nb=="all MW":
                    product_nc_MW = dirlist_nc[service_nc_MW]
                    st.write(product_nc_MW)

                show_mw = st.button('Save moving window')
                            
                if show_mw:
                    with st.spinner("Please wait..."):
                        if type(product_nc_MW)!=list:
                            # Path to NetCDF
                            path_file_MW = os.path.join(bdir,"NetCDF_files",service_nc_MW,product_nc_MW)
                            mw = sa.moving_window(bdir,path_file_MW,int(window))
                        else:
                            for p in product_nc_MW:
                                # Path to NetCDF
                                path_file_MW = os.path.join(bdir,"NetCDF_files",service_nc_MW,p)
                                mw = sa.moving_window(bdir,path_file_MW,int(window))

                        if mw==None:
                            st.warning('Please choose a daily or monthly dataset', icon="⚠️")
                        else:
                            st.success('File(s) .txt saved in '+os.path.split(path_file_MW)[0], icon="✅")
                            st.pyplot(mw)


    ############################
    # STATISTICS ON EACH PIXEL #
    ############################
    if choose_option=="Statistics on each pixel":
        tab1_layer, tab2_layer = st.tabs(["available layers", "create layer (.tif)"])

        # Availables Layers
        with tab1_layer: 
            try:
                dirlist_lay = gf.show_available_files(bdir,"Layers")
            except:
                st.error("Folder not found: "+os.path.join(bdir,'Layers'))
                st.stop()
            
            if dirlist_lay=={}:
                st.warning('No Layer found', icon="⚠️")
            else : 
                service_lay = st.selectbox('Choose the service', dirlist_lay.keys())
                if dirlist_lay[service_lay]==[]:
                    st.warning('No Layer file found', icon="⚠️")
                else :
                    st.write(dirlist_lay[service_lay])


        # Create Layer
        with tab2_layer:
            if qgis_imported==False:
                # Import qgis module
                try:
                    import script_qgis_software as soft
                except:
                    st.error("QGIS path not found, please set in Set options")
                    st.stop()
                else:
                    qgis_imported = True

            try:
                dirlist_nc = gf.show_available_files(bdir,"NetCDF_files")
            except:
                st.error("Folder not found: "+os.path.join(bdir,"NetCDF_files"))
                st.stop()
            try:
                filelist = gf.show_available_files_simple(bdir,"Layers")
            except:
                st.error("Folder not found: "+os.path.join(bdir,"Layers"))
                st.stop()
            
            if dirlist_nc=={}:
                st.warning('No NetCDF file found', icon="⚠️")
            else : 
                stats = st.multiselect("Choose statistics to compute",["average","standard deviation","min and max"])
                timer = st.selectbox("Choose time range",["year","season","month"])
                service_nc_lay = st.selectbox('Choose the service', dirlist_nc.keys(),key="s2")
                if dirlist_nc[service_nc_lay]==[]:
                    st.warning('No NetCDF file found', icon="⚠️")
                else :
                    nb = st.radio("Time range",("over one year","over several years"))
                    if nb=="over one year":
                        product_nc_lay = st.selectbox('Choose the dataset', dirlist_nc[service_nc_lay])
                    elif nb=="over several years":
                        product_nc_lay = st.multiselect('Choose the datasets', dirlist_nc[service_nc_lay])
                        
                    create_tif = st.button('Save .tif files')
                                
                    if create_tif:
                        with st.spinner("Please wait..."):
                            if type(product_nc_lay)!=list:
                                # Path to NetCDF
                                path_file_lay = os.path.join(bdir,"NetCDF_files",service_nc_lay,product_nc_lay)
                                soft.run_qgis_analysis(bdir,path_file_lay,stats,timer)
                            else:
                                for p in product_nc_lay:
                                    path_file_lay = os.path.join(bdir,"NetCDF_files",service_nc_lay,p)
                                    soft.run_qgis_analysis(bdir,path_file_lay,stats,timer)
                        st.success('File(s) .tif saved in '+os.path.split(path_file_lay)[0], icon="✅")


    ##############################
    # UPLOAD AN OCCURRENCES FILE #
    ##############################
    if choose_option=="Upload an occurrences file":
        col1_upload, col2_upload = st.columns([2,1])

        # Show and delete files
        with col2_upload :
            with st.expander('Current availables occurrences files:'):
                ################ TO ADAPT ################
                occpath = os.getcwd()+"/../Occurrences"
                if not os.path.exists(occpath):
                    os.mkdir(occpath) 
                filelist_occ = gf.show_available_files_simple(os.getcwd()+"/..","Occurrences")
                st.table(filelist_occ)
                
                _file = st.selectbox("Choose a file",filelist_occ)
                suppr = st.button("Delete file")
                if suppr :
                    ################ TO ADAPT ################
                    os.remove(os.getcwd()+"/../Occurrences/"+_file)
                    st.success('File deleted: '+_file, icon="✅")
                    st.experimental_rerun()

            st.info("Presence data only")

            with st.expander("File must contain"):
                st.write("**Columns (other accepted name):**")  
                st.write("""
                - Latitude (latitude, lat, LAT, LATITUDE)
                - Longitude (longitude, lon, long, LON, LONG, LONGITUDE)
                - Date (date, day, Day, Timestamp, DATE, DAY, TIMESTAMP)""")


        # Upload file
        with col1_upload :
            uploaded_file = st.file_uploader('Upload a CSV',type="csv")
            if uploaded_file:
                dataframe = pd.read_csv(uploaded_file,sep=",")
                    
                data = {}
                other = []
                for col in list(dataframe.columns):
                    if col in ['Latitude','latitude','lat','LAT','LATITUDE']:
                        # verify if all floats
                        if is_column_float(dataframe[col])==True:
                            data['Latitude']=dataframe[col]
                        else:
                            st.warning('Column '+col+' contains non-floats values', icon="⚠️")
                            st.stop()
                    elif col in ['Longitude','longitude','lon','long','LON','LONG','LONGITUDE']:
                        # verify if all floats
                        if is_column_float(dataframe[col])==True:
                            data['Longitude']=dataframe[col]
                        else:
                            st.warning('Column '+col+' contains non-floats values', icon="⚠️")
                            st.stop()
                    elif col in ['Date','date','day','Day','Timestamp','DATE','DAY','TIMESTAMP']:
                        data['Date']=dataframe[col]
                    else : 
                        other.append(col)
                    
                # check if necessary cols are presents
                if ('Latitude' or 'Longitude' or'Date') not in data.keys():
                    st.warning('Necessary column absent, please reupload updated file', icon="⚠️")
                    st.stop()
                
                # ask for date format
                _dayfirst = st.radio("Day before month?",[True,False])

                # select col for occurrences and choose name
                col_occ = st.selectbox("Choose a column for occurrences",other)
                name_occ = st.text_input('Choose a name for this occurrences sheet',uploaded_file.name.split(".csv")[0])
                if re.search(r"[^\w_-]",name_occ):
                    st.warning('Please choose a name without special character', icon="⚠️")
                    st.stop()
                if name_occ+".csv" in filelist_occ:
                    st.warning('Name already taken', icon="⚠️")
                    st.stop()

                check_occ = st.button("Save file")
                if check_occ:
                    data['Occurrences']=dataframe[col_occ]
                    data['Date']=pd.to_datetime(data['Date'], dayfirst=_dayfirst,format='mixed')
                    # data['Year'] = data['Year'].astype(int).astype(str)
                    ################ TO ADAPT ################
                    OUTPUT_FILE = os.getcwd()+'/../Occurrences/'+name_occ+'.csv'
                    pd.DataFrame(data).to_csv(OUTPUT_FILE, sep=',', encoding='utf-8')
                    st.success('File saved in: '+OUTPUT_FILE, icon="✅")


    ################################
    # CORRELATION WITH OCCURRENCES #
    ################################
    if choose_option=="Correlation with occurrences":
        # Get files in NetCDF_files, Results and Occurrences
        try:
            dirlist_nc = gf.show_available_files(bdir,"NetCDF_files")
        except:
            st.error("Folder not found: "+os.path.join(bdir,'NetCDF_files'))
            st.stop()
        try:
            dirlist_res = gf.show_available_files(bdir,"Results")
        except:
            st.error("Folder not found: "+os.path.join(bdir,"Results"))
            st.stop()
        try:
            ################ TO ADAPT ################
            filelist_occ = gf.show_available_files_simple(os.getcwd()+"/..","Occurrences")
        except:
            st.error("Folder not found: 'Occurrences'")
            st.stop()
        

        col1_corr,col2_corr = st.columns([2,1])
        if filelist_occ == []:
            st.warning('Please upload an occurrence file first', icon="⚠️")
            st.stop()
        else :
            with col1_corr:
                csvfile = st.selectbox('Choose occurrences file', filelist_occ)
            with col2_corr:
                st.write("__Current backup folder:__ "+os.path.split(bdir)[1])

                # Merge all csv
                st.write("_Several files already created:_")
                merge = st.button('Merge all correlation files of '+csvfile,use_container_width=True)

                if merge:
                    d=corr.merge_all_CORR(bdir,csvfile)
                    st.success('File saved in: '+os.path.join(bdir,csvfile.split(".")[0]+'-ALLCORR.csv'), icon="✅")

        # CORR already created
        with col2_corr:
            with st.expander('Current availables correlation files:'):
                all_avCORR = {}
                for k in dirlist_res.keys():
                    avCORR = []
                    for f in dirlist_res[k]:
                        if f.endswith("CORR.csv"):
                            avCORR.append(f)
                    all_avCORR[k]=avCORR
                st.write(all_avCORR)
                

        # Create CORR
        if dirlist_nc=={}:
            st.warning('No NetCDF file found', icon="⚠️")
        else :
            with col1_corr:
                service_nc_CORR = st.selectbox('Choose the service', dirlist_nc.keys())
                if dirlist_nc[service_nc_CORR]==[]:
                    st.warning('No NetCDF file found', icon="⚠️")
                    st.stop()
            
                create = st.button('Correlation with occurrences',use_container_width=True)
                st.info("Rerun correlation replace created files")

                if create:
                    ################ TO ADAPT ################
                    csvpath = os.path.join(os.getcwd()+"/..",'Occurrences',csvfile)
                
                    with st.spinner("Please wait..."):
                        df=corr.correlation(bdir,csvpath,service_nc_CORR)
                    OUTPUT_FILE = bdir+"/Results/"+service_nc_CORR
                    st.success('File saved in: '+OUTPUT_FILE, icon="✅")



##########################################################################################################
##########################################################################################################
##########################################################################################################
elif choose == "Meta-analysis":
    # Remove extra space
    st.write('<style>div.block-container{padding-top:2rem;padding-bottom:2rem;}</style>', unsafe_allow_html=True)
    
    ################ TO ADAPT ################
    # Get path to backup folder
    with open("./options.json","r") as f:
        json_dict = json.load(f)
    bdir = json_dict["backup_path"]

    # Get files in Results
    try:
        dirlist_res = gf.show_available_files(bdir,"Results")
    except:
        st.error("Folder not found: "+bdir+'/Results')
        st.stop()

    st.write("__Current backup folder:__ "+os.path.split(bdir)[1])

    tab1_metaanalysis, tab2_metaanalysis = st.tabs(["Show 1 dataset data", "Compare 2 datasets"])

    with tab1_metaanalysis:
        if dirlist_res=={}:
            st.warning('No Results file found, please create MW file first', icon="⚠️")
            st.stop()
        else :
            service_res_all_avMW = st.selectbox('Choose the service', dirlist_res.keys())
            all_avMW = []
            for f in dirlist_res[service_res_all_avMW]:
                if f.endswith("MW.txt"):
                    ### EXTRACT FROM FILENAME
                    v = f.split("__")[0] # PREFIXpfx[DMIN-DMAX]VARIABLE
                    if v!="":
                        v = v+"-"+(f.split("__")[-1]).split("-")[0] # PREFIXpfx[DMIN-DMAX]VARIABLE-WINDOW
                        if v not in all_avMW:
                            all_avMW.append(v)
            variable_MW = st.selectbox('Choose the variable', all_avMW)

            # Clear cache
            cc_button = st.button("Data have changed !",use_container_width=True)
            if cc_button :
                st.cache_data.clear()
                st.experimental_rerun()
                

        tab1b_metaanalysis, tab2b_metaanalysis = st.tabs(["All data : trend", "Occurrences correlation"])
        

        #########
        # TREND #
        #########
        with tab1b_metaanalysis:
            fig_html,original_data,df_trend,fig = run_all_MW(bdir,service_res_all_avMW,variable_MW)
            components.html(fig_html, height=410,scrolling=True)
            st.text("↑ Click on loop and select area to zoom in")

            # Save figure
            savefig = st.button("Save figure",use_container_width=True)
            if savefig:
                output_fig = os.path.join(bdir,variable_MW+".png")
                fig.savefig(output_fig)
                st.success('Fig saved in '+output_fig, icon="✅")


            # Linear regression and MK test
            st.subheader("Linear regression and Mann-Kendall Trend Test")
            col1_tests,col2_tests = st.columns([1,2])
            r,ts = sa.regression(df_trend)
            
            with col1_tests:
                st.write("")
                st.write(f"slope (95%): {r.slope} +/- {ts*r.stderr}")
                st.write(f"pvalue: {r.pvalue}")
                st.write(f"rvalue: {r.rvalue}")
                st.write(f"standard error : {r.stderr}")

            fig2, ax2 = plt.subplots()
            ax2.plot(df_trend['time'].to_numpy(), df_trend['avg'].to_numpy(), 'b', label='12 months window')
            ax2.plot(df_trend['time'].to_numpy(), r.intercept + r.slope*df_trend.index.to_numpy(), 'r', label='fitted line')
            ax2.legend(loc='upper left')
            ax2.set_title(variable_MW)
            col2_tests.write(fig2)

            with col2_tests:
                # Save figure
                savefig2 = st.button("Save figure",key="s2",use_container_width=True)
                if savefig2:
                    output_fig2 = os.path.join(bdir,"LR-"+variable_MW+".png")
                    fig2.savefig(output_fig2)
                    st.success('Fig saved in '+output_fig2, icon="✅")

            DF = original_data.drop('std',axis=1) 
            DF = DF.set_index('time')
            with col1_tests:
                st.write(":red["+str(mk.original_test(DF))+"]")
                st.write("_If the p-value is lower than 0.05, there is statistically significant evidence that a trend is present in the time series data._")
            

            # STL test
            st.subheader("Seasonal-Trend decomposition using LOESS")
            fig3,r3 = sa.stl_test(original_data)
            st.pyplot(fig3)

            # Save figure
            savefig3 = st.button("Save figure",key="s3",use_container_width=True)
            if savefig3:
                output_fig3 = os.path.join(bdir,"STL-"+variable_MW+".png")
                fig3.savefig(output_fig3)
                st.success('Fig saved in '+output_fig3, icon="✅")

            # LR and MK on trend
            col1_testtr,col2_testtr = st.columns(2)
            r3b,ts3b = sa.regression(r3.trend)
            col1_testtr.write("**Linear regression on trend**")
            col1_testtr.write(r3b)
            col2_testtr.write("**Mann-Kendall Trend Test on trend**")
            col2_testtr.write(":red["+str(mk.original_test(r3.trend))+"]")


        ###############
        # CORRELATION #
        ###############
        with tab2b_metaanalysis:
            col1_corr, col2_corr = st.columns([4,1])
            with col1_corr:
                df,spec = get_correlations(bdir,service_res_all_avMW,variable_MW)
            if df.empty:
                st.error("No correlation file found")
            else :
                dmin = df['Date'].min()
                f,x = plot_fig_corr(original_data,variable_MW,dmin)
                with col2_corr:
                    st.write("Occurrences")
                    spec_choice = st.multiselect('Choose type', spec)
                with col1_corr:
                    f = sa.plot_corr(f,x,variable_MW,df,spec_choice)
        
                    fig_html = mpld3.fig_to_html(f)
                    components.html(fig_html, height=410,scrolling=True)
                    st.text("↑ Click on loop and select area to zoom in")
                with col2_corr:
                    # Save figure
                    savefigcorr = st.button("Save figure",key="scorr")
                    if savefigcorr:
                        output_figcorr = os.path.join(bdir,"CORR-"+variable_MW+".png")
                        f.savefig(output_figcorr)
                        st.success('Fig saved in '+output_figcorr, icon="✅")
    

    ##############
    # COMPARISON #
    ##############
    with tab2_metaanalysis:
        col1_comp,col2_comp=st.columns(2)

        # Choice dataset 1
        with col1_comp:
            service_comp = st.selectbox('Choose the service 1', dirlist_res.keys())
            all_avMW_comp = []
            for f in dirlist_res[service_comp]:
                if f.endswith("MW.txt"):
                ### EXTRACT FROM FILENAME
                    v = f.split("__")[0]
                    if v not in all_avMW_comp:
                        all_avMW_comp.append(v)
            variable_comp = st.selectbox('Choose the variable 1', all_avMW_comp)

        # Choice dataset 2
        with col2_comp:
            service_compb = st.selectbox('Choose the service 2', dirlist_res.keys())
            all_avMW_compb = []
            for f in dirlist_res[service_compb]:
                if f.endswith("MW.txt"):
                    ### EXTRACT FROM FILENAME
                    v = f.split("__")[0]
                    if v not in all_avMW_compb:
                        all_avMW_compb.append(v)
            variable_compb = st.selectbox('Choose the variable 2', all_avMW_compb)
            #comp = st.button("Compare",use_container_width=True)

        if service_comp == service_compb:
            if variable_comp == variable_compb:
                st.warning('Please choose 2 different datasets', icon="⚠️")
                st.stop()
        
        mw,x1,x2=sa.compare_MW(bdir,service_comp,variable_comp,service_compb,variable_compb)
        marg = st.slider('Zoom out', min_value=0.0, max_value=2.0,step=0.1)
        x1.margins(0, marg)   
        x2.margins(0, marg)     
        st.write(mw)
            


##########################################################################################################
##########################################################################################################
##########################################################################################################
elif choose == "Show map":
    # Remove extra space
    st.write('<style>div.block-container{padding-top:2rem;padding-bottom:2rem;}</style>', unsafe_allow_html=True)
    
    ################ TO ADAPT ################
    # Get path to backup folder
    with open("./options.json","r") as f:
        json_dict = json.load(f)
    bdir = json_dict["backup_path"]


    # Get coordinates
    path_coord = os.path.join(bdir,"coordinates.json")
    try:
        with open(path_coord,"r") as f:
            json_dict = json.load(f)
        lon = json_dict["LONG"]
        lat = json_dict["LAT"]
    except:
        st.error("File not found: "+bdir+'/coordinates.json')
        st.stop()
    
    # Get files in NetCDF_files, Layers and Occurrences
    try:
        dirlist_nc = gf.show_available_files(bdir,"NetCDF_files")
    except:
        st.error("Folder not found: "+bdir+'/NetCDF_files')
        st.stop()
    try:
        dirlist_lay = gf.show_available_files(bdir,"Layers")
    except:
        st.error("Folder not found: "+bdir+'/Layers')
        st.stop()
    try:
        ################ TO ADAPT ################
        dirlist_occ = gf.show_available_files_simple(os.getcwd()+"/..","Occurrences")
    except:
        st.error("Folder not found: "+os.getcwd()+"/../Occurrences")
        st.stop()


    st.write("__Current backup folder:__ "+os.path.split(bdir)[1])

    tab1_map,tab2_map,tab3_map,tab4_map,tab5_map = st.tabs(["occurrences only","variable per day", "variable per month", "variable per season", "variable per year"])
    st.set_option('deprecation.showPyplotGlobalUse', False)
    

    ###############
    # OCCURRENCES #
    ###############
    with tab1_map:    
        if dirlist_occ == []:
            st.warning('Please upload an occurrences file first', icon="⚠️")
        else:
            ################ TO ADAPT ################
            occ = st.selectbox("Choose occurrence file",dirlist_occ)
            occ_path = os.getcwd()+"/../Occurrences/"+str(occ)
            
            y,o = get_occ(occ_path)
            _years = st.multiselect('Years',y,default=y)
            _occs = st.multiselect('Occurrences',o,default=o)
            
            ds_occ = corr.create_map_occ(occ_path,_years,_occs,800,600,7)
            st.write(ds_occ)


    #######
    # DAY #
    #######
    with tab2_map:      
        if dirlist_nc == {}:
            st.warning('Please create a NetCDF file first', icon="⚠️")
            st.stop()

        with st.expander('Map options'):
            service_daymap = st.selectbox('Choose the service', dirlist_nc.keys(),key="s1")
            if dirlist_nc[service_daymap]==[]:
                st.warning('No NetCDF file found', icon="⚠️")
            else:
                product_daymap = st.selectbox('Choose the dataset', dirlist_nc[service_daymap],key="p1")

                # Path to NetCDF
                path_file_day = os.path.join(bdir,"NetCDF_files",service_daymap,product_daymap)

                ### EXTRACT FROM FILENAME
                year_day = path_file_day.split('__')[-1]

                minval = date.fromisoformat(year_day+'-01-01')
                maxval = date.fromisoformat(year_day+'-12-31')
                date_choice = st.date_input('Choose a date',value = minval,min_value=minval,max_value=maxval)

                depth_day = motu.get_depths(path_file_day)
                if depth_day !=[]:
                    choice_depth_day = st.selectbox('Choose depth', depth_day)
                else :
                    choice_depth_day = 0.0

        if 'product_daymap' in locals():
            ds = motu.create_map_1d(path_file_day,str(date_choice.month),str(date_choice.day),choice_depth_day)
            st.pyplot(ds)
    

    # Check if statistics created
    if dirlist_lay == {}:
        tab3_map.warning('Please compute statistics on each pixel first', icon="⚠️")
        tab4_map.warning('Please compute statistics on each pixel first', icon="⚠️")
        tab5_map.warning('Please compute statistics on each pixel first', icon="⚠️")
        st.stop()


    #########
    # MONTH #
    #########
    with tab3_map: 
        with st.expander('Map options'):
            service_monthmap = st.selectbox('Choose the service', dirlist_lay.keys(),key="s3")
            if dirlist_lay[service_monthmap]==[]:
                st.warning('No Layer file found', icon="⚠️")
            else:
                # filter layers
                prodlist_monthmap,all_years,variables = filter_layers(dirlist_lay[service_monthmap],["1","2","3","4","5","6","7","8","9","10","11","12"])
                if prodlist_monthmap == []:
                    st.warning('No statistics over month', icon="⚠️")
                else:
                    c1,c2,c3 = st.columns(3)
                    with c1 : 
                        variable_monthmap = st.selectbox('Choose the variable',variables,key="v3")
                        prodlist_monthmap = [p for p in prodlist_monthmap if variable_monthmap in p]
                    with c2 :
                        years_variable = all_years[variable_monthmap]
                        year_monthmap = st.selectbox('Choose the year',years_variable,key="y3")
                        prodlist_monthmap = [p for p in prodlist_monthmap if year_monthmap in p]
                    with c3 :
                        stat_monthmap = st.selectbox('Choose the statistics',['avg','std','min','max'],key="st3")
                        prodlist_monthmap = [p for p in prodlist_monthmap if stat_monthmap in p]

                    if prodlist_monthmap==[]:
                        st.warning('No file available, choose another statistic', icon="⚠️")
                    else:
                        # Path to Layer
                        i = 1
                        pathfiles = {}
                        for p in prodlist_monthmap:
                            pathfiles[i] = os.path.join(bdir,"Layers",service_monthmap,p)
                            i+=1

                        depth_month = motu.get_depths(pathfiles[1],geotiff=True)
                        if depth_month !=[]:
                            choice_depth_month = st.selectbox('Choose depth', depth_month)
                        else :
                            choice_depth_month = 0.0

        if ('variable_monthmap' and 'pathfiles') in locals():
            z = st.slider('Zoom', min_value=0, max_value=20,step=1,value=7,key="z3")

            # Create maps
            i = 1
            maps_month = {}
            for path in pathfiles.values():
                maps_month[i] = motu.create_map(path,float(choice_depth_month),800,600,z)
                i+=1

            ### EXTRACT FROM FILENAME
            VAR_FULL = (os.path.split(pathfiles[1])[1]).split('__')[0]
            VAR = VAR_FULL.split("pfx")[-1]
            if "]" in VAR:
                VAR = VAR.split("]")[-1]

            ################ TO ADAPT ################
            # Get var name and unit
            with open("./variables.json","r") as f:
                json_dict = json.load(f)
            if VAR in json_dict.keys():
                VARNAME = json_dict[VAR][0]
                VARUNIT = json_dict[VAR][1]

            
            choose = st.select_slider('Choose a month', ['January','February','March','April','Mai','June','July','August','September','October','November','December'])
            months = {'January':1,'February':2,'March':3,'April':4,'Mai':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
            st.subheader(VARNAME+" in "+VARUNIT)
            st.write(maps_month[months[choose]])

    

    ##########
    # SEASON #
    ##########
    with tab4_map:   
        with st.expander('Map options'):
            service_seasonmap = st.selectbox('Choose the service', dirlist_lay.keys(),key="s4")
            if dirlist_lay[service_seasonmap]==[]:
                st.warning('No Layer file found', icon="⚠️")
            else:
                # filter layers
                prodlist_seasonmap,all_years,variables = filter_layers(dirlist_lay[service_seasonmap],["spring","summer","autumn","winter"])
                if prodlist_seasonmap == []:
                    st.warning('No statistics over season', icon="⚠️")
                else:
                    c1,c2,c3 = st.columns(3)
                    with c1 : 
                        variable_seasonmap = st.selectbox('Choose the variable',variables,key="v4")
                        prodlist_seasonmap = [p for p in prodlist_seasonmap if variable_seasonmap in p]
                    with c2 :
                        years_variable = all_years[variable_seasonmap]
                        year_seasonmap = st.selectbox('Choose the year',years_variable,key="y4")
                        prodlist_seasonmap = [p for p in prodlist_seasonmap if year_seasonmap in p]
                    with c3 :
                        stat_seasonmap = st.selectbox('Choose the statistics',['avg','std','min','max'],key="st4")
                        prodlist_seasonmap = [p for p in prodlist_seasonmap if stat_seasonmap in p]

                    if prodlist_seasonmap==[]:
                        st.warning('No file available, choose another statistic', icon="⚠️")
                    else:
                        # Path to Layer
                        path_file1= os.path.join(bdir,"Layers",service_seasonmap,prodlist_seasonmap[0])
                        path_file2= os.path.join(bdir,"Layers",service_seasonmap,prodlist_seasonmap[1])
                        path_file3= os.path.join(bdir,"Layers",service_seasonmap,prodlist_seasonmap[2])
                        path_file4= os.path.join(bdir,"Layers",service_seasonmap,prodlist_seasonmap[3])

                        depth_season = motu.get_depths(path_file1,geotiff=True)
                        if depth_season !=[]:
                            choice_depth_season = st.selectbox('Choose depth', depth_season)
                        else :
                            choice_depth_season = 0.0

        if ('variable_seasonmap' and 'path_file1') in locals():
            z = st.slider('Zoom', min_value=0, max_value=20,step=1,value=7,key="z4")

            ds1 = motu.create_map(path_file1,float(choice_depth_season),450,500,z)
            ds2 = motu.create_map(path_file2,float(choice_depth_season),450,500,z)
            ds3 = motu.create_map(path_file3,float(choice_depth_season),450,500,z)
            ds4 = motu.create_map(path_file4,float(choice_depth_season),450,500,z)

            ### EXTRACT FROM FILENAME
            VAR_FULL = (os.path.split(path_file1)[1]).split('__')[0]
            VAR = VAR_FULL.split("pfx")[-1]
            if "]" in VAR:
                VAR = VAR.split("]")[-1]

            ################ TO ADAPT ################
            # Get var name and unit
            with open("./variables.json","r") as f:
                json_dict = json.load(f)
            if VAR in json_dict.keys():
                VARNAME = json_dict[VAR][0]
                VARUNIT = json_dict[VAR][1]

            st.subheader(VARNAME+" in "+VARUNIT)
            col1_season, col2_season = st.columns(2)
            col1_season.write(ds1)
            col1_season.write(ds3)
            col2_season.write(ds2)
            col2_season.write(ds4)


    ########
    # YEAR #
    ########
    with tab5_map:      
        with st.expander('Map options'):
            service_yearmap = st.selectbox('Choose the service', dirlist_lay.keys(),key="s5")
            if dirlist_lay[service_yearmap]==[]:
                st.warning('No Layer file found', icon="⚠️")
                st.stop()

            # filter layers
            prodlist_yearmap = []
            for p in dirlist_lay[service_yearmap]:
                prod = os.path.split(p)[1]
                suf = (((prod.split("avg")[-1]).split("std")[-1]).split("min")[-1]).split("max")[-1]
                if suf not in ["spring","summer","autumn","winter","1","2","3","4","5","6","7","8","9","10","11","12"]:
                    prodlist_yearmap.append(p)
            if prodlist_yearmap == []:
                st.warning('No statistics over year', icon="⚠️")
                st.stop()
                    
            product_yearmap = st.selectbox('Choose the file', prodlist_yearmap,key="p4")
            
            # Path to Layer
            path_file_year = os.path.join(bdir,"Layers",service_yearmap,product_yearmap)
            
            depth_year = motu.get_depths(path_file_year,geotiff=True)
            if depth_year !=[]:
                choice_depth_year = st.selectbox('Choose depth', depth_year)
            else :
                choice_depth_year = 0.0

        ### EXTRACT FROM FILENAME
        VAR_FULL = (os.path.split(path_file_year)[1]).split('__')[0]
        VAR = VAR_FULL.split("pfx")[-1]
        if "]" in VAR:
            VAR = VAR.split("]")[-1]

        ################ TO ADAPT ################
        # Get var name and unit
        with open("./variables.json","r") as f:
            json_dict = json.load(f)
        if VAR in json_dict.keys():
            VARNAME = json_dict[VAR][0]
            VARUNIT = json_dict[VAR][1]

        st.subheader(VARNAME+" in "+VARUNIT)
        ds_year = motu.create_map(path_file_year,float(choice_depth_year),800,600,7)
        st.write(ds_year)

