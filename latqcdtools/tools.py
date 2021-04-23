import multiprocessing
import numpy as np
import traceback
import importlib.util
import math
import sys
from latqcdtools.num_deriv import *
#import algopy

def check_numpy(*data):
    data=list(data)
    for i in range(len(data)):
        if isinstance(data[i], (list, tuple)):
            data[i] = np.array(data[i])
    return tuple(data)

def remove_nan(*data, test_cols = None):
    new_data = [[] for i in data ]
    if test_cols == None:
        test_cols = list(range(len(data)))
    for i in range(min(len(i) for i in data)):
        remove = False
        for j in test_cols:
            if np.isnan(data[j][i]):
                remove = True

        if not remove:
            for j in range(len(data)):
                new_data[j].append(data[j][i])
    return new_data

def remove_large(*data, threshold = 1e6, test_cols = None):
    if test_cols == None:
        test_cols = list(range(len(data)))
    new_data = [[] for i in data ]
    for i in range(min(len(i) for i in data)):
        remove = False
        for j in test_cols:
            if data[j][i] > threshold:
                remove = True

        if not remove:
            for j in range(len(data)):
                new_data[j].append(data[j][i])
    return new_data

def remove_large_err(*data, threshold = 1.0, col_val = 1, col_err = 2):
    new_data = [[] for i in data ]
    for i in range(min(len(i) for i in data)):
        remove = False
        if data[col_err][i] / data[col_val][i] > threshold:
            remove = True

        if not remove:
            for j in range(len(data)):
                new_data[j].append(data[j][i])
    return new_data


def is_array_scalar(x):
    return np.size(x) == 1

#Reparse the command line arguments such that negative float values are accepted
def reparse_argv():
    for i, arg in enumerate(sys.argv):
        if (arg[0] == '-') and isfloat(arg): sys.argv[i] = ' ' + arg

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def susz_one_dim(data):
    sum_1 = 0
    sum_2 = 0
    for i in data:
        sum_1 += i
        sum_2 += i * i
    sum_1 /= len(data)
    sum_2 /= len(data)
    return sum_2 - sum_1 * sum_1


def susz(data):
    res = []
    for i in data:
        res.append(susz_one_dim(i))
    return res


def rel_check(a, b, prec=1e-6, abs_prec = 1e-14):
    return math.isclose(a, b, rel_tol=prec, abs_tol = abs_prec)


# import module with a given path. Works with python 3.5+
def import_lib(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fm_to_MeVinv(x):
    return (1/197.3269718)*x

def fm_to_GeVinv(x):
    return (1/0.1973269718)*x

def MeVinv_to_fm(x):
    return 197.3269718*x

def GeVinv_to_fm(x):
    return 0.1973269718*x



def numToWords(num):
    if num > 9 or num < 0:
        raise ValueError("Numer 0-9 required")
    units = ['zero','one','two','three','four','five','six','seven','eight','nine']
    return units[num]

#Depricated. 
def my_mean(a):
    try:
        res = np.copy(a[0])
        for i in a[1:]:
            res += i
        return res / len(a)
    except:
        return a


#align data in memory
def aligned(a, alignment=32):
    if (a.ctypes.data % alignment) == 0:
        return a

    extra = int(alignment / a.itemsize)
    buf = np.empty(a.size + extra, dtype=a.dtype)
    ofs = int((-buf.ctypes.data % alignment) / a.itemsize)
    aa = buf[ofs:ofs+a.size].reshape(a.shape)
    np.copyto(aa, a)
    assert (aa.ctypes.data % alignment) == 0

    return aa


"""Get the number of parameters for a typical fitting function"""
def get_numb_params(func, x = 1, args = (), expand = True):
        params = []
        i = 0
        for i in range(1000):
            params.append(1)
            try:
                i += 1
                if expand:
                    func(x, *(tuple(params) + tuple(args)))
                else:
                    func(x, params, *args)
                return i
            except Exception as e:
                pass
        raise IndexError("Function does not work with up to 1000 parameters")

#Uneccessary with python3.5 (Shitty cluster has python 3.4)
def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def timeout(func, args=(), kwargs={}, timeout_duration=300):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    class TimeoutError(Exception):
        pass

    def wrap_func(*args):
        ret = func(*args[0], **args[1])
        args[2]["ret"] = ret

    p = multiprocessing.Process(target = wrap_func, args = (args, kwargs, return_dict))
    p.start()

    p.join(timeout_duration)

    # If thread is still active
    if p.is_alive():

        # Terminate
        p.terminate()
        p.join()
        raise TimeoutError("Time out for " + str(func))
    return return_dict["ret"]
