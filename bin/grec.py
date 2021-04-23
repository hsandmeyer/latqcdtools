#!/usr/bin/env python3
import numpy as np
from latqcdtools.fitting import *
import sys
import latqcdtools.jackknife as jk
import latqcdtools.bootstr as bs
from latqcdtools.tools import *
from latqcdtools.statistics import *
from latqcdtools.readin import *
from latqcdtools.plotting import *
from latqcdtools.reconst_corr import *
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("--file-warm", "-fw") 
parser.add_argument("--file-cold", "-fc") 
parser.add_argument("--nt-col", type = int, default = 1) 
parser.add_argument("--data-col", type = int, default = 2) 
parser.add_argument("--nsamples", "-ns", type = int, default = 1000) 
parser.add_argument("--from-sample", "-fs", action = 'store_true') 
parser.add_argument("--remove-Ntnorm", "-rn", action = 'store_true') 

args = parser.parse_args()


xdata_cold, data_cold, nconfs_cold = read_in_pure(args.file_cold, args.nt_col, args.data_col)
xdata_warm, data_warm, nconfs_warm = read_in_pure(args.file_warm, args.nt_col, args.data_col)



Nt_cold = len(data_cold)
Nt_warm = len(data_warm)

if args.remove_Ntnorm:
    data_cold /= Nt_cold**3
    data_warm /= Nt_warm**3



if args.from_sample:
    grec, grec_err = mean_and_std_dev([ Grec_direct(g_cold, Nt_warm, Nt_cold) for g_cold in data_cold.transpose()])
    g, g_err = mean_and_std_dev(data_warm, axis = 1)
    gdivgrec, gdivgrec_err = mean_and_std_dev(
            [ GdivGrec_direct(i[1], Grec_direct(i[0], Nt_warm, Nt_cold)) for i in zip(data_cold.transpose(), data_warm.transpose())])
    gdiffgrecdiff, gdiffgrecdiff_err = mean_and_std_dev(
            [ GDiffGrecDiff_direct(i[1], Grec_direct(i[0], Nt_warm, Nt_cold)) for i in zip(data_cold.transpose(), data_warm.transpose())])
    gsubgrecsub, gsubgrecsub_err = mean_and_std_dev(
            [ GSubGrecSub_direct(i[1], Grec_direct(i[0], Nt_warm, Nt_cold)) for i in zip(data_cold.transpose(), data_warm.transpose())])

else:
    grec, grec_err = bs.bootstr(Grec, data_cold, args.nsamples, args = (Nt_warm, ))
    g, g_err = bs.bootstr(std_mean, data_warm, args.nsamples, args = {'axis': 1})
    gdivgrec, gdivgrec_err = bs.bootstr(GdivGrec, [data_cold, data_warm], args.nsamples, conf_axis = 2)
    gdiffgrecdiff, gdiffgrecdiff_err= bs.bootstr(GDiffGrecDiff, [data_cold, data_warm], args.nsamples, conf_axis = 2)
    gsubgrecsub, gsubgrecsub_err= bs.bootstr(GSubGrecSub, [data_cold, data_warm], args.nsamples, conf_axis = 2)


print("#nt, G/G_rec, G/G_rec_err, Gdiff/G_rec_diff, Gdiff/G_rec_diff_err, Gsub/G_rec_sub, Gsub/G_rec_sub_err, G_rec, G_rec_err, G_warm, G_warm_err")
for i in range(len(gdiffgrecdiff)):
    print(i, gdivgrec[i], gdivgrec_err[i], gdiffgrecdiff[i], gdiffgrecdiff_err[i], gsubgrecsub[i], gsubgrecsub_err[i], grec[i], grec_err[i], g[i], g_err[i])
#plot_dots(xdata_warm, g)
#plot_dots(xdata_warm, grec)
#plot_dots(xdata_warm[:-1], gdiffgrecdiff, gdiffgrecdiff_err)
#plot_dots(xdata_warm[:-1], (g[:-1] - g[1:]) / (grec[:-1] - grec[1:]))
#plot_dots(xdata_warm[:-1], (g[:-1] - g[1:]) / (grec[:-1] - grec[1:]))
#plt.yscale('log')
#plt.show()

