###########
# IMPORTS #
###########

import os
import sys
import json
import cftime
import datetime

from qgis.core import *

from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsMapLayer,
    QgsProcessingFeedback
)

with open("./options.json","r") as f:
    json_dict = json.load(f)
# Supply path to qgis install location
QgsApplication.setPrefixPath(json_dict["qgis_path"], True)
# Append the path where processing plugin can be found
sys.path.append(json_dict["proc_path"])

# Create a reference to the QgsApplication.  
# Setting the second argument to False disables the GUI.
qgs = QgsApplication([], False)


from qgis import processing

from qgis.analysis import QgsZonalStatistics
from qgis.analysis import QgsNativeAlgorithms


from osgeo import gdal
gdal.PushErrorHandler('CPLQuietErrorHandler')
# hide ERROR 6: The PNG driver does not support update access to existing datasets.


### START QGIS ###
qgs.initQgis()

sys.path.append(json_dict["proc_path"])
    
import processing 
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# qgs.exitQgis()


##################
# QGIS FUNCTIONS #
##################


def add_layer(BDIR:str,FILEPATH:str,vlayer=False):
    """ 
        Add a layer to the QGIS instance

        Parameters
        ----------
        BDIR : str
            path to the backup folder 
        FILEPATH : str
            raster (.nc) or vector (.csv) layer file path (set vlayer=True)

        Returns
        -------
        QgsRasterLayer or QgsVectorLayer
    """
    if vlayer==True:
        vlayer = QgsVectorLayer(FILEPATH, "sightings", "ogr")
        QgsProject.instance().addMapLayer(vlayer)
        return vlayer
    
    SERVICE = FILEPATH.split("/")[-2]
    NAME = FILEPATH.split("/")[-1]

    path = BDIR+"/Layers/"+SERVICE
    if not os.path.exists(path):
        os.mkdir(path)

    rlayer = QgsRasterLayer(FILEPATH, NAME)
    QgsProject.instance().addMapLayer(rlayer)
    return rlayer



#########################
# FUNCTIONS - INTERFACE #
#########################


def run_qgis_analysis(BDIR:str,FILEPATH:str,STATS:list,TIMERANGE:str):
    """ 
        Compute statistics over a raster layer

        Parameters
        ----------
        BDIR : str
            path to the backup folder 
        FILEPATH : str
            NetCDF file path
        STATS : list (str)
            name of analysis:average/standard deviation/min and max
        TIMERANGE : str
            name of timerange:year/season/month
    """
    LAYER = add_layer(str(BDIR),str(FILEPATH))

    SERVICE = str(LAYER.dataProvider().dataSourceUri()).split("/")[-2]
    NAME = str(LAYER.dataProvider().dataSourceUri()).split("/")[-1]
    bandcount = LAYER.bandCount()
    
    # Get depth dimension
    depth_dim = int(round(bandcount/365))

    # Get bands divided by time range
    LAYER2 = None
    if TIMERANGE == 'season':
        # Get year of file
        YEAR = int(NAME.split("__")[-1])

        # Try add next year
        YEARn = YEAR+1
        FILEPATH2 = FILEPATH.replace(str(YEAR),str(YEARn))
        if os.path.exists(FILEPATH2):
            LAYER2 = add_layer(str(BDIR),str(FILEPATH2))

        # Get day number start season
        _spring = (datetime.date(YEAR, 3, 21)-datetime.date(YEAR, 1, 1)).days
        _summer = (datetime.date(YEAR, 6, 21)-datetime.date(YEAR, 1, 1)).days
        _autumn = (datetime.date(YEAR, 9, 21)-datetime.date(YEAR, 1, 1)).days
        _winter = (datetime.date(YEAR, 12, 21)-datetime.date(YEAR, 1, 1)).days
        if LAYER2 != None :
            _end = (datetime.date(YEARn, 3, 21)-datetime.date(YEARn, 1, 1)).days
        else : 
            _end = (datetime.date(YEAR, 12, 31)-datetime.date(YEAR, 1, 1)).days

        # BANDRANGE = [[firstdayseason1,endayseason1],[firstdayseason2,endayseason2],...]
        # endayseason1 == firstdayseason2
        BANDRANGE = [[_summer,_autumn],[_autumn,_winter],[_winter,_end]]
        BANDRANGE = [[element*depth_dim for element in el] for el in BANDRANGE]
        # Starting at first day of spring
        BANDRANGE.insert(0,[_spring,_summer*depth_dim])
        suf = ["spring","summer","autumn","winter"]

    elif TIMERANGE == 'month':
        # Get year of file
        YEAR = int(NAME.split("__")[-1])

        # Get day number start month
        _fev = (datetime.date(YEAR, 2, 1)-datetime.date(YEAR, 1, 1)).days
        _mars = (datetime.date(YEAR, 3, 1)-datetime.date(YEAR, 1, 1)).days
        _avr = (datetime.date(YEAR, 4, 1)-datetime.date(YEAR, 1, 1)).days
        _mai = (datetime.date(YEAR, 5, 1)-datetime.date(YEAR, 1, 1)).days
        _juin = (datetime.date(YEAR, 6, 1)-datetime.date(YEAR, 1, 1)).days
        _juli = (datetime.date(YEAR, 7, 1)-datetime.date(YEAR, 1, 1)).days
        _aout = (datetime.date(YEAR, 8, 1)-datetime.date(YEAR, 1, 1)).days
        _sept = (datetime.date(YEAR, 9, 1)-datetime.date(YEAR, 1, 1)).days
        _octo = (datetime.date(YEAR, 10, 1)-datetime.date(YEAR, 1, 1)).days
        _nov = (datetime.date(YEAR, 11, 1)-datetime.date(YEAR, 1, 1)).days
        _dec = (datetime.date(YEAR, 12, 1)-datetime.date(YEAR, 1, 1)).days
        _end = (datetime.date(YEAR, 12, 31)-datetime.date(YEAR, 1, 1)).days

        # BANDRANGE = [[firstdaymonth1,endaymonth1],[firstdaymonth2,endaymonth2],...]
        # endaymonth1 == firstdaymonth2
        BANDRANGE = [[_fev,_mars],[_mars,_avr],[_avr,_mai],[_mai,_juin],[_juin,_juli],[_juli,_aout],[_aout,_sept],[_sept,_octo],[_octo,_nov],[_nov,_dec],[_dec,_end]]
        BANDRANGE = [[element*depth_dim for element in el] for el in BANDRANGE]
        # Starting at january
        BANDRANGE.insert(0,[1,_fev*depth_dim])
        suf = ["1","2","3","4","5","6","7","8","9","10","11","12"]

    elif TIMERANGE == 'year':
        # Starting at 01/01
        BANDRANGE = [[1,bandcount]]
        suf = [""]


    # Processing algorithms
    feedback = QgsProcessingFeedback()


    # 10*DEPTHDIM

    s = 0
    # for each division in BANDRANGE
    for B in BANDRANGE :
        if LAYER2==None:
            # Average
            if "average" in STATS:
                tempexp = ['"{0}@{1}"'.format(LAYER.name(), bandnum) for bandnum in range(B[0],B[1]+1)]
                tempexp = '+'.join(tempexp) # sum all bands
                avg = '('+tempexp+')/{0}'.format(B[1]-B[0]) # firstdaymonth2 - firstdaymonth1

                params = { 
                'EXPRESSION' : avg,
                'LAYERS':[LAYER.source()],
                'CELLSIZE':None,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':str(BDIR)+'/Layers/'+str(SERVICE)+'/'+str(NAME)+'_avg'+suf[s]
                }
                processing.run('qgis:rastercalculator', params, feedback=feedback)
        

            # Variance and standard deviation
            if "standard deviation" in STATS:
                avg = ['"{0}@{1}"'.format(LAYER.name(), bandnum) for bandnum in range(B[0],B[1]+1)]
                avg = '+'.join(avg) # sum all bands
                avg = '('+avg+')/{0}'.format(B[1]-B[0]) # firstdaymonth2 - firstdaymonth1

                tempexp = ['"{0}@{1}"'.format(LAYER.name(), bandnum) for bandnum in range(B[0],B[1]+1)]
                tempexp = ('-'+str(avg)+')^2 + (').join(tempexp) # band - avg)² + (band - avg)² + (band
                var = '(('+tempexp+'-'+str(avg)+')^2)/{0}'.format(B[1]-B[0]) # firstdaymonth2 - firstdaymonth1
                std = 'sqrt('+var+')'
                
                params = { 
                'EXPRESSION' : std,
                'LAYERS':[LAYER.source()],
                'CELLSIZE':None,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':str(BDIR)+'/Layers/'+str(SERVICE)+'/'+str(NAME)+'_std'+suf[s]
                }
                processing.run('qgis:rastercalculator', params, feedback=feedback)


            # Maximum and minimum value
            if "min and max" in STATS:
                tempexp = 'MIN("{0}@{1}","{0}@{2}")'.format(LAYER.name(),B[0],B[0]+1)
                for i in range(B[0]+2,B[1]+1):
                    tempexp = 'MIN('+tempexp+',"{0}@{1}")'.format(LAYER.name(),i)

                params = { 
                'EXPRESSION' : tempexp,
                'LAYERS':[LAYER.source()],
                'CELLSIZE':None,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':str(BDIR)+'/Layers/'+str(SERVICE)+'/'+str(NAME)+'_min'+suf[s]
                }
                processing.run('qgis:rastercalculator', params, feedback=feedback)

                tempexp = 'MAX("{0}@{1}","{0}@{2}")'.format(LAYER.name(),B[0],B[0]+1)
                for i in range(B[0]+2,B[1]+1):
                    tempexp = 'MAX('+tempexp+',"{0}@{1}")'.format(LAYER.name(),i)

                params = { 
                'EXPRESSION' : tempexp,
                'LAYERS':[LAYER.source()],
                'CELLSIZE':None,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':str(BDIR)+'/Layers/'+str(SERVICE)+'/'+str(NAME)+'_max'+suf[s]
                }
                processing.run('qgis:rastercalculator', params, feedback=feedback)

        # next suffix
        s += 1
