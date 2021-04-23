import numpy as np
import math
from numpy.random import randint
from numpy.random import normal
from latqcdtools.tools import *
from latqcdtools.statistics import *
import latqcdtools.logger as lg
import sys




#recursive function to fill the sample
def recurs_append(src_data, sample_data, axis, conf_axis, sample_size, same_rand_for_obs):

    #break condition. At this point we fill the sample.
    if axis + 1 == conf_axis:
        numb_observe = len(src_data)
        if sample_size == 0:
            sample_sizes = [ len(i) for i in src_data ]
        else:
            sample_sizes = [ sample_size for i in src_data ]

        if not same_rand_for_obs:
            randints = [randint(0, len(src_data[x]), size=sample_sizes[x])
                    for x in range(numb_observe)]
        else:
            tmp_rand = randint(0, len(src_data[0]), size=sample_sizes[0]) 
            randints = [tmp_rand for x in range(numb_observe)]
        for x in range(numb_observe):
            sample_data.append(np.array(src_data[x])[randints[x]])
        return

    else:
        for i in range(len(src_data)):
            sample_data.append([])
            recurs_append(src_data[i], sample_data[i], axis + 1, conf_axis,
                    sample_size, same_rand_for_obs)



"""
Bootstrap for arbitray functions. This routine resamples the data and passes
them to the function in the same format as in the input. So the idea is to write
a function that computes an observable from a given data set. This function can be put into
this bootstrap routine and will get bootstrap samples as input. Based on the output of the
function, the bootstrap mean and error are computed. The function may return multiple
observables that are either scalars or numpy objects.
You can pass a multidimensional object as data, but the bootstrap function has to 
know which axis should be resampled which is controlled by conf_axis (default = 0 for 
one dimensional arrays and default = 1 for higher order arrays.
    Parameters
    ----------
    func : callable
        The function that calculates the observable

    data : array_lik 
        Input data

    numb_samples : integer
        Number of bootstrap samples

    same_rand_for_obs : boolean, optional, default = False
        Use the same random numbers for each observable accessed by index conf_axis - 1.
        Please note:
            - Objects that are accessed by an axis >= conf_axis + 1 do always have the same
            random numbers.
            - Objects that are accessed by axis conf_axis < conf_axis - 1 never share the same
            random numbers.

    conf_axis : integer, optional, default = 0 for dim(data) = 1
        or default = 1 for dim(data) >= 2
        Axis that should be resampled

    return_sample : boolean, optional, default = False
        Along with the mean and the error also return the results from the individual samples

    seed: integer, optional, default = None
        seed for the random generator. If None, the default seed from numpy is used
        (probably from time)

    same_rand_for_obs : boolean, optional, default = False
        same random numbers per observable

    err_by_dist : boolean, optional, default = False
        Compute the error from the distribution using the median and the 68% quantile

    args : array_like or dict, default = ()
        optional arguments to be passed to func. If a dictionary the are passed as **args.


"""


def bootstr(func, data, numb_samples, sample_size = 0, same_rand_for_obs = False,
        conf_axis = 1, return_sample = False, seed = None, err_by_dist = False,
        nmax_exceptions = 0, args=()):
    try:
        data[0][0]
    except IndexError:
        conf_axis = 0
    #data = np.array(data)
    if seed is not None:
        np.random.seed(seed)


    sampleval = []
    if numb_samples > 100:
        progress_step = int(numb_samples / 100)
    else:
        progress_step = 1

    i = 0
    failed_tries = 0
    while i < numb_samples:
        if i % progress_step == 0:
            lg.progress("%i%%" % (i / numb_samples * 100,))

        # start sampling
        sample_data = []
        src_data = data
        if conf_axis == 0: #Case of one dimensional array is special
            if sample_size == 0:
                sample_size_tmp = len(src_data)
            else:
                sample_size_tmp = sample_size
            randints = randint(0, len(src_data), size=sample_size_tmp)
            sample_data = src_data[randints]

        else:
            axis = 0
#We use a recursive function to fill the sample_data.
#We call it itself until axis reaches the conf_axis.
            recurs_append(src_data, sample_data, axis, conf_axis,
                    sample_size, same_rand_for_obs)

        sample_data = np.array(sample_data)
        try:
            if isinstance(args, dict):
                mean_i = func(sample_data, **args)
            else:
                mean_i = func(sample_data, *args)
            sampleval.append(mean_i)
        except Exception as e:
            failed_tries += 1
            if failed_tries >= nmax_exceptions:
                raise ValueError("More than " + str(nmax_exceptions) +
                        " of the function calls failed")
            lg.warn("Ignoring exception", e)
            continue

        i += 1

    if not err_by_dist:
        mean = std_mean(sampleval)
        error = std_dev(sampleval)
    else:
        mean = std_median(sampleval)
        error = dev_by_dist(sampleval)
    if return_sample:
        return sampleval, mean, error
    return(mean, error)


"""Same as standard bootstrap routine, but the data are generated by gaussian noise
around the mean values in data. The width of the distribution is controlled by
data_std_dev. Note, that the function has to average over samples. This means, that 
data_std_dev should always be the standard deviation of a single measurement and not the
standard deviation of a mean"""

def bootstr_from_gauss(func, data, data_std_dev, numb_samples, sample_size = 1, 
        return_sample=False, seed=None, err_by_dist = False,
        nmax_exceptions = 0, args=()):
    data = np.asarray(data)
    data_std_dev = np.asarray(data_std_dev)
    if seed is not None:
        np.random.seed(seed)

    numb_observe = len(data)

    sampleval = []

    if numb_samples > 100:
        progress_step = int(numb_samples / 100)
    else:
        progress_step = 1

    i = 0
    failed_tries = 0
    while i < numb_samples:

        if i % progress_step == 0:
            lg.progress("%i%%" % (i / numb_samples * 100,))

        sample_data = []
        for k in range(numb_observe):
            if sample_size == 1:
                sample_data.append(normal(data[k], data_std_dev[k]))
            else:
                sample_data.append(normal(data[k], data_std_dev[k], sample_size))

        sample_data = np.array(sample_data)
        try:
            if isinstance(args, dict):
                mean_i = func(sample_data, **args)
            else:
                mean_i = func(sample_data, *args)
            sampleval.append(mean_i)
        except Exception as e:
            failed_tries += 1
            if failed_tries >= nmax_exceptions:
                raise ValueError("More than " + str(nmax_exceptions) +
                        " of the function calls failed")
            lg.warn("Ignoring exception", e)
            continue

        i += 1

    if not err_by_dist:
        mean = std_mean(sampleval)
        error = std_dev(sampleval)
    else:
        mean = std_median(sampleval)
        error = dev_by_dist(sampleval)
    if return_sample:
        return sampleval, mean, error
    return(mean, error)


# Demonstration how to use the bootstr function
def demonstrate_bootstr():
    def simple_mean(a):
        return np.mean(a)

    def div_simple(a, b, c):
        return b * a[0] / (c * a[1])

    def div_old(a, b, c):
        return b * np.mean(a[0]) / (c * np.mean(a[1]))

    def f(a, b, c):
        return b * np.mean(a[0]) / (c * np.mean(a[1]))

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
        return (np.array([[f(a, b, c), f(a, b, c), f(a, b, c)], [f(a, b, c),
            f(a, b, c), f(a, b, c)]]), np.array([f(a, b, c), f(a, b, c)]),
            np.array(f(a, b, c)))

    def divnp_conf2(a, b, c):
        a=a[0]
        return (np.array([[f(a, b, c), f(a, b, c), f(a, b, c)],
            [f(a, b, c), f(a, b, c), f(a, b, c)]]),
            np.array([f(a, b, c), f(a, b, c)]), np.array(f(a, b, c)))

    data_length = 100
    print("Data lengths =", data_length)
    a, b, c = (np.random.normal(1, 2, size=data_length),
            np.random.normal(1, 2, size=data_length),
            np.random.normal(1, 2, size=data_length))

    print("100 samples")
    mn_simple, err_simple = bootstr(simple_mean, a, 100)
    print(mn_simple)
    print(err_simple)

    print("100 samples, sample_size 1000")
    mn_simple, err_simple = bootstr(simple_mean, a, 100, 100)
    print(mn_simple)
    print(err_simple)

    print("100 samples, sample_size 10")
    mn_simple, err_simple = bootstr(simple_mean, a, 100, 10)
    print(mn_simple)
    print(err_simple)


    print("Other stuff functions")
    mn1, err1 = bootstr(div1, [a, b], 100, 100, args=(2, 2))
    print(mn1)
    print(err1)

    mn2, err2 = bootstr(div2, [a, b], 10000, 100, args=(2, 2))
    print(mn2)
    print(err2)

    mn3, err3 = bootstr(div3, [a, b], 1000, args=(2, 2))
    print(mn3)
    print(err3)

    mn4, err4 = bootstr(div4, [a, b], 1000, args=(2, 2))
    print(mn4)
    print(err4)

    mn1, err1 = bootstr(divnp1, [a, b], 1000, args=(2, 2))
    print(mn1)
    print(err1)

    mn2, err2 = bootstr(divnp2, [a, b], 1000, args=(2, 2))
    print(mn2)
    print(err2)

    mn3, err3 = bootstr(divnp3, [a, b], 1000, args=(2, 2))
    print(mn3)
    print(err3)

    mn4, err4 = bootstr(divnp4, [a, b], 1000, args=(2, 2))
    print(mn4)
    print(err4)

    mn4, err4 = bootstr(divnp5, [a, b], 1000, args=(2, 2))
    print(mn4)
    print(err4)

    print("conf_axis = 2")
    mn4, err4 = bootstr(divnp_conf2, [[a, b]], 1000, conf_axis=2, args=(2, 2))
    print(mn4)
    print(err4)

#demonstrate_bootstr()
