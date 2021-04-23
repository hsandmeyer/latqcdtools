import numpy as np
import latqcdtools.jackknife as jk
import glob
import math as mt
import sys


def read_files(paths, ID_sep, stream_pos):
    filelist = []

    for i in range(len(paths)):
        # print(i)
        expanded = glob.glob(paths[i]+"*")
        # print(expanded)
        filelist.extend(expanded)

    for i in filelist:
        if len(i.split(ID_sep)) > 2:
            sys.exit("Error! More than one seperator!")

    def sort_func(x): return (
        x.split(ID_sep)[-2][stream_pos:], int(x.split(ID_sep)[-1]))
    filelist.sort(key=sort_func)

    for i in range(len(filelist)-1):
        basename, _, ID = filelist[i].partition(ID_sep)
        basename2, _, ID2 = filelist[i+1].partition(ID_sep)
        if int(ID) > int(ID2) and basename[stream_pos:] == basename2[stream_pos:]:
            for j in filelist:
                print(j)
            print(ID, ID2)
            sys.exit("Error! Files are not sorted correctly!!")

    raw_data = []
    for i in filelist:
        raw_data.append(np.loadtxt(i, dtype=np.float64, unpack=True))

    return filelist, np.asarray(raw_data)
