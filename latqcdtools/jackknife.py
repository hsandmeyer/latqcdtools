import numpy as np
import math
import sys
from latqcdtools.tools import *
from latqcdtools.statistics import *
""" This file contains a jackknife routine that can handle arbitrary return
values of functions. Please look first at jackknife_old to understand what is going on."""


# Calculate pseudo values of elements of objects that are not tuple
def pseudo(mean, mean_i, numb_blocks):
    return numb_blocks * mean - (numb_blocks - 1) * mean_i


# Calculate pseudo values of elements of objects that might be tuples


#As in gattringer
# @reduce_tuple
# def jack_dev(data, axis = 0):
#    data = np.asarray(data)
#    return (data.shape[axis] - 1) * np.std(data, axis = axis, ddof = 0)
#
# @reduce_tuple
# def jack_mean(data, mean, axis = 0):
#    data = np.asarray(data)
#    mean_blocks = std_mean(data)
#    return mean - (data.shape[axis] - 1) * (mean_blocks - mean)


def pseudo_val(mean, mean_i, numb_blocks):
    if type(mean) is tuple:
        retvalue = ()
        for i in range(len(mean)):
            # print(mean[i])
            retvalue += (pseudo(np.array(mean[i]),
                         np.array(mean_i[i]), numb_blocks),)
            #retvalue += (np.array(mean_i[i]),)
        return retvalue
    else:
        #print(mean, mean_i)
        return pseudo(np.array(mean), np.array(mean_i), numb_blocks)
        # return np.array(mean_i)


"""
Jackknife routine for arbitray functions. This routine creates the jackknife like blocked
subsets of data and passes them to the function in the same format as in the input data.
So the idea is to write a function that computes an observable from a given data set.
This function can be put into this jackkife routine and will get the jackknifed blocked dat as
input. Based on the output of the function, the jackkife mean and error are computed.
The function may return multiple observables that are either scalars or numpy objects.
You can pass a multidimensional object as data, but the jackknife function has to 
know from which axis blocks should be removed. This is controlled by conf_axis (default = 0 for 
one dimensional arrays and default = 1 for higher order arrays).
    Parameters
    ----------
    func : callable
        The function that calculates the observable

    data : array_lik 
        Input data

    numb_blocks : integer
        Number of jackknife blocks

    conf_axis : integer, optional, default = 0 for dim(data) = 1
    and default = 1 for dim(data) >= 2
        Axis that should be resampled

    args : array_like or dict, default = ()
        optional arguements to be passed to func. If a dictionary the are passed as **args.


"""


def jackknife(func, data, numb_blocks=20, conf_axis=1, args=()):
    data = np.array(data)

# If the measurements are accessed by the second index in data,
# we construct the jackknife manually to allow different size of sets of measurements
# conf_axis ==1 is the only case which allows different length of data arrays per observable
    if conf_axis == 1:
        try:
            lengths = [len(data[i]) for i in range(len(data))]
            blocksizes = [math.floor(length / numb_blocks)
                          for length in lengths]
            for length in lengths:
                if length < numb_blocks:
                    raise IndexError("More number of blocks than datapoints!")
        except TypeError:  # if we get an 1D array
            conf_axis = 0
            length = data.shape[conf_axis]
            blocksize = math.floor(length / numb_blocks)

    else:
        length = data.shape[conf_axis]
        blocksize = math.floor(length / numb_blocks)

    if conf_axis == 1:
        numb_observe = len(data)
        used_data = [data[i][:numb_blocks * blocksizes[i]]
                     for i in range(numb_observe)]
        used_data = np.array(used_data)
    else:
        if length < numb_blocks:
            print("More number of blocks than datapoints! Exit!")
            print("  length, numb_blocks=", length, numb_blocks)
            sys.exit(-1)
        rolled_data = np.rollaxis(data, conf_axis)
        used_data = np.rollaxis(
            rolled_data[:numb_blocks * blocksize], 0, conf_axis + 1)

    if isinstance(args, dict):
        mean = func(used_data, **args)
    else:
        mean = func(used_data, *args)
    blockval = []
    for i in range(0, numb_blocks):
        block_data = []
        if conf_axis == 1:
            for k in range(0, numb_observe):

                block_data.append(data[k][0:i * blocksizes[k]])
                block_data[k] = np.concatenate((block_data[k], data[k][(i + 1)
                                                                       * blocksizes[k]:numb_blocks * blocksizes[k]]))
        else:
            # The Jackknife blocks are constructed by rolling the conf axis to the first index.
            # Then the jackknife blocks are built. Aferwards the we roll back
            rolled_data = np.rollaxis(data, conf_axis)
            for j in range(0, i * blocksize):
                block_data.append(rolled_data[j])
            for j in range((i + 1) * blocksize, numb_blocks * blocksize):
                block_data.append(rolled_data[j])
            block_data = np.rollaxis(np.array(block_data), 0, conf_axis + 1)
        block_data = np.array(block_data)

        if isinstance(args, dict):
            mean_i = func(block_data, **args)
        else:
            mean_i = func(block_data, *args)
        mean_i = pseudo_val(mean, mean_i, numb_blocks)
        blockval.append(mean_i)
    mean = std_mean(blockval)
    error = std_err(blockval)
    return(mean, error)


# older version that does not support objects,
# just scalars as a return value of func. Much simpler to read
def jackknife_old(func, data, numb_blocks, args=()):
    length = len(data[0])
    blocksize = math.floor(length / numb_blocks)
    numb_observe = len(data)
    used_data = [data[i][:numb_blocks * blocksize]
                 for i in range(numb_observe)]
    mean = func(used_data, *args)
    blockval = []
    for i in range(0, numb_blocks):
        block_data = []
        for k in range(0, numb_observe):
            block_data.append([])
            for j in range(0, i * blocksize):
                block_data[k].append(data[k][j])
            for j in range((i + 1) * blocksize, numb_blocks * blocksize):
                block_data[k].append(data[k][j])
        mean_i = func(block_data, *args)
        mean_i = numb_blocks * mean - (numb_blocks - 1) * mean_i
        blockval.append(mean_i)
    mean = np.mean(blockval)
    error = 0.0
    for i in range(0, numb_blocks):
        error += (blockval[i] - mean) * (blockval[i] - mean)
    error = math.sqrt(error / (numb_blocks - 1))
    error /= math.sqrt(numb_blocks)
    return(mean, error)

# Wrapper to use simpler functions which do not have to average


def jackknife_simple(func, data, numb_blocks, args=()):
    def func_simple(data):
        means = [np.mean(data[i]) for i in range(len(data))]
        return func(means, *args)
    return jackknife(func_simple, data, numb_blocks)


# Demonstration how to use the jackknife function
def demonstrate_jackknife():
    def simple_mean(a):
        return np.mean(a)

    def div_simple(a, b, c):
        return b * a[0] / (c * a[1])

    def div_old(a, b, c):
        return b * np.mean(a[0]) / (c * np.mean(a[1]))

    def f(a, b, c):
        return b * np.mean(a[0]) / (c * np.mean(a[1]))
        # return np.mean(a[0])

    def div1(a, b, c):
        return ([[f(a, b, c), f(a, b, c)], [f(a, b, c), f(a, b, c)]],
                [f(a, b, c), f(a, b, c)], f(a, b, c))

    def div2(a, b, c):
        return [[f(a, b, c), f(a, b, c)], [f(a, b, c), f(a, b, c)]]

    def div3(a, b, c):
        return [f(a, b, c), f(a, b, c)]

    def div4(a, b, c):
        return f(a, b, c)

    def divnp1(a, b, c):
        return (np.array([[f(a, b, c), f(a, b, c)], [f(a, b, c), f(a, b, c)]]),
                np.array([f(a, b, c), f(a, b, c)]), np.array(f(a, b, c)))

    def divnp2(a, b, c):
        return np.array([[f(a, b, c), f(a, b, c)], [f(a, b, c), f(a, b, c)]])

    def divnp3(a, b, c):
        return np.array([f(a, b, c), f(a, b, c)])

    def divnp4(a, b, c):
        return np.array(f(a, b, c))

    def divnp5(a, b, c):
        return (np.array([[f(a, b, c), f(a, b, c), f(a, b, c)], [f(a, b, c), f(a, b, c), f(a, b, c)]]),
                np.array([f(a, b, c), f(a, b, c)]), np.array(f(a, b, c)))

    a, b, c = (np.random.normal(10, 2, size=1000), np.random.normal(10, 2, size=1000),
               np.random.normal(10, 2, size=1000))

    mn_simple, err_simple = jackknife(simple_mean, a, 10)
    print(mn_simple)
    print(err_simple)

    mn_old, err_old = jackknife_old(div_old, [a, b], 10, args=(2, 2))
    print(mn_old, err_old)

    mn_simple, err_simple = jackknife_simple(
        div_simple, [a, b], 10, args=(2, 2))
    print(mn_simple, err_simple)

    mn1, err1 = jackknife(div1, [a, b], 10, args=(2, 2))
    print(mn1)
    print(err1)

    mn2, err2 = jackknife(div2, [a, b], 10, args=(2, 2))
    print(mn2)
    print(err2)

    mn3, err3 = jackknife(div3, [a, b], 10, args=(2, 2))
    print(mn3)
    print(err3)

    mn4, err4 = jackknife(div4, [a, b], 10, args=(2, 2))
    print(mn4)
    print(err4)

    mn1, err1 = jackknife(divnp1, [a, b], 10, args=(2, 2))
    print(mn1)
    print(err1)

    mn2, err2 = jackknife(divnp2, [a, b], 10, args=(2, 2))
    print(mn2)
    print(err2)

    mn3, err3 = jackknife(divnp3, [a, b], 10, args=(2, 2))
    print(mn3)
    print(err3)

    mn4, err4 = jackknife(divnp4, [a, b], 10, args=(2, 2))
    print(mn4)
    print(err4)

    mn4, err4 = jackknife(divnp5, [a, b], 10, args=(2, 2))
    print(mn4)
    print(err4)

# demonstrate_jackknife()
