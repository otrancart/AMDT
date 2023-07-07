For developers
==============

Configuration files
-------------------
- **options.json** contains backup folder path and qgis path
- **prefix.json** contains saved prefixes for datasets that share common service (url) and variables
- **variables.json** contains id, name and unit of each variable available in Copernicus

The coordinates are saved in the backup folder in **coordinates.json**

Filenames
---------
Here are the format of files created by AMDT.

Common variables:
    - SERVICE
    - VARIABLE (can contain _)
    - YEAR
    - DEPTH (DMIN/DMAX)
    - PREFIX (needed if shared SERVICE and VARIABLE)
    - STAT
        - avg/std/min/max
        - by season : avgspring/avgsummer/avgautumn/avgwinter
        - by month : avg1/avg2/.../avg12
    - OCC : name of csv occurrences file correlated
    - WIN : number of days in window

forbidden character (bash or already used): ``--`` ``_`` ``__`` ``(`` ``)`` ``[`` ``]`` ``|`` ``*`` ``?`` ``!``

Each subfolder = 1 SERVICE

==================================  ======================================= =============================================== ================================================                 
NetCDF_files                        Layers                                  Results
----------------------------------  --------------------------------------- ------------------------------------------------------------------------------------------------
.nc                                 .tif                                    .txt                                            .csv
==================================  ======================================= =============================================== ================================================
VARIABLE__YEAR                      VARIABLE__YEAR_STAT                     VARIABLE__YEAR__WIN-MW.txt                      VARIABLE__YEAR__OCC-CORR.csv
[DMIN-DMAX]VARIABLE__YEAR           [DMIN-DMAX]VARIABLE__YEAR_STAT          [DMIN-DMAX]VARIABLE__YEAR__WIN-MW.txt           [DMIN-DMAX]VARIABLE__YEAR__OCC-CORR.csv
PREFIXpfxVARIABLE__YEAR             PREFIXpfxVARIABLE__YEAR_STAT            PREFIXpfxVARIABLE__YEAR__WIN-MW.txt             PREFIXpfxVARIABLE__YEAR__OCC-CORR.csv
PREFIXpfx[DMIN-DMAX]VARIABLE__YEAR  PREFIXpfx[DMIN-DMAX]VARIABLE__YEAR_STAT PREFIXpfx[DMIN-DMAX]VARIABLE__YEAR__WIN-MW.txt  PREFIXpfx[DMIN-DMAX]VARIABLE__YEAR__OCC-CORR.csv
==================================  ======================================= =============================================== ================================================

