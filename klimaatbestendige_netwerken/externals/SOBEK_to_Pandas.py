# -*- coding: utf-8 -*-
"""
Created on Thu Jan 04 2018
Last modified  14-6-2019

Script to convert SOBEK3 output to Panda DataFrames
Run stand-alone to export the entire output folder to .csv files

@author: Jurjen de Jong
"""

import os
import glob
import pandas as pd
import netCDF4
import re

def nc2dicts(directory):
    '''
    This script will read all netcdf files in a SOBEK 3.6+ output
    directory and place this in Pandas DataFrames. Each .nc-file
    will get it's own DataFrame
    '''

    # get name of all nc file in the directory
    filelist = glob.glob(os.path.join(directory, '*.nc'))

    # open all data in the nc files
    datadict = {}
    for ncfile in filelist:
        df = read_nc(ncfile)
        if len(df):
            datadict[filename] = df

    return datadict

def read_nc(ncfile, return_attributes=True):
    ncfid = netCDF4.Dataset(ncfile)
    filename = os.path.splitext(os.path.basename(ncfile))[0]
    print('Opening file:', filename)

    time = ncfid.variables['time']
    time = netCDF4.num2date(time[:], time.units)
    # time = pd.DatetimeIndex(time)  # This code crashed somehow
    # time = pd.date_range(time[0], time[1], periods=len(time))  # work around for crash
    # time = time.round('1 s')

    varnames = ncfid.variables
    key = [key for key in varnames.keys() if re.match('(.*)_id', key)]
    names = ncfid.variables[key[0]][:]
    names = [s.strip() for s in netCDF4.chartostring(names)]

    df = {}
    df_attributes = {}
    for v in ncfid.variables:
        var = ncfid.variables[v]
        if not v == 'time' and var.dimensions[0] == 'time':
            print('Reading:', v)
            data = var[:]
            df[v] = pd.DataFrame(data, index=time, columns=names)
        elif not v == 'time' and var.dimensions[0] == 'id' and return_attributes:
            data = var[:]
            if len(data.shape)>1:
                data = [d.strip() for d in netCDF4.chartostring(data)]
            df_attributes[v] = pd.Series(data=data, index=names)

    if len(df):
        df = pd.concat(df, axis=1)

    if return_attributes:
        if len(df_attributes):
            df_attributes = pd.concat(df_attributes, axis=1)
        return df, df_attributes
    else:
        return df

if __name__ == '__main__':
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory()

    datadict = nc2dicts(directory)

    print('Writing output files' )
    for filename, df in datadict.items():
        for quantity in df.columns.levels[0]:
            df[quantity].to_csv(os.path.join(directory, '{}_{}.csv'.format(filename, quantity)))
