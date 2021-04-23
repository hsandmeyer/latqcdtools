import numpy as np
from numpy.linalg import inv
from latqcdtools.statistics import *
from numpy.random import normal
from latqcdtools.plotting import *
import math


"""Compute the weighted mean if correlations are present"""


def cov_weighted_average(data, cov):
    W = np.ones_like(data)
    sig2 = 1 / (W.transpose().dot(inv(cov).dot(W)))
    av = sig2 * (W.transpose().dot(inv(cov).dot(data)))
    return av, np.sqrt(sig2)


"""
Compute the weighted mean
"""


def weighted_mean(data, weights):
    data = np.asarray(data)
    weights = np.asarray(weights)
    return np.sum(data.dot(weights))/np.sum(weights)


def chi_square(data, weights=None):
    if weights is None:
        weights = np.ones_like(data)
    data = np.asarray(data)
    mean = weighted_mean(data, weights)
    return np.sum(weights.dot((data - mean)**2))


# https://mathoverflow.net/questions/11803/unbiased-estimate-of-the-variance-of-a-weighted-mean
# In above source, the weights are normalized.

"""
Compute the variance of the weighted mean based on error propagation.
This is only valid if the error bars of the
data are of reasonable size, meaning that most of the error bars include the mean value.
If you expect that there are unknown systematic errors, you should use unbiased_mean_variance
instead.

Parameters
----------

errors: array_like
    The errors of the data points
weights: array_like, optional, default = None
    If you do not use weights = 1/errors**2, you can pass additional weights.
    If None, weights = computed as 1/errors**2
"""


def weighted_mean_variance(errors, weights=None):
    errors = np.asarray(errors)
    if weights is None:
        errors = np.asarray(errors)
        weights = 1 / errors**2
    return np.sum(weights**2 * errors**2) / np.sum(weights)**2


"""
Compute the biased weighted sample variance, i.e. the biased variance of an individual
measurement and not the variance of the mean. 
"""


def biased_sample_variance(data, weights):
    mean = weighted_mean(data, weights)
    V1 = np.sum(weights)
    return weights.dot((data - mean)**2) / V1


"""
Compute the unbiased weighted sample variance, i.e. the unbiased variance of an individual
measurement and not the variance of the mean. Do not use this function if your weights
are frequency weights.
"""


def unbiased_sample_variance(data, weights):
    V1 = np.sum(weights)
    V2 = np.sum(weights**2)
    return biased_sample_variance(data, weights) / (1 - (V2 / V1**2))


"""
Compute the unbiased variance of a weighted mean. Do not use this function if your weights
are frequency weights. This is more like a systematic error. The absolute size of the weights
does not matter. The error is constructed using the deviations of the individual data
points
"""


def unbiased_mean_variance(data, weights):
    V1 = np.sum(weights)
    V2 = np.sum(weights**2)
    return biased_sample_variance(data, weights) * V2 / (V1**2 - V2)


"""Add different gaussian distributions via bootstrapping and compute the
68% quantile of this distribution"""


def bootstr_add_dist(data, errors, nstat=1000, plot_hist=False):
    dists = ()
    for i in range(len(data)):
        dist = normal(data[i], errors[i], size=nstat)
        dists += (dist,)
    tot_dist = np.concatenate(dists)

    med, err = std_median(tot_dist), dev_by_dist(tot_dist)
    err_dist = tot_dist[(tot_dist < med + err) & (tot_dist > med - err)]
    if plot_hist:
        hist, bins = np.histogram(tot_dist, bins=math.ceil(nstat / 10))
        plt.hist(tot_dist, bins=bins)
        plt.hist(err_dist, bins=bins)
    return med, err
