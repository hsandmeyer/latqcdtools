from latqcdtools.tools import rel_check


def print_results(res, res_true, res_err=None, res_err_true=None, text="", prec=1e-4):
    test = True
    try:
        res[0]
    except (IndexError, TypeError):
        res = [res]
    try:
        res_true[0]
    except (IndexError, TypeError):
        res_true = [res_true]

    for i in range(len(res)):
        if not rel_check(res[i], res_true[i], prec):
            test = False
            print("res[" + str(i) + "] = " + str(res[i])
                  + " != res_true[" + str(i) + "] = " + str(res_true[i]))
        if res_err is not None and res_err_true is not None:
            if not rel_check(res_err[i], res_err_true[i], prec):
                test = False
                print("res_err[" + str(i) + "] = " + str(res_err[i])
                      + " != res_err_true[" + str(i) + "] = " + str(res_err_true[i]))
    print("============================")
    if test:
        print(text + " passed")
    else:
        print(text + " FAILED!")
    print("============================")
    print()
