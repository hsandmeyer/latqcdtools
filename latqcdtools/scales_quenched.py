import numpy as np
from latqcdtools.tools import *

# Based on https://arxiv.org/pdf/1503.05652.pdf
# Latest update at 2017/07/08


def ln_r0(beta):
    b0 = 11./(4*np.pi)**2
    b1 = 102/(4*np.pi)**4
    c1 = -8.9664
    c2 = 19.21
    c3 = -5.25217
    c4 = 0.606828
    # old
    # c1=-8.98152
    # c2=19.2913
    # c3=-5.27804
    # c4=0.728086
    return ((beta/(12*b0)+b1/(2.*b0**2)*np.log(6*b0/beta))*(1+c1/beta+c2/beta**2)
            / (1+c3/beta+c4/beta**2))

# Based on https://arxiv.org/pdf/1503.05652.pdf
# Latest update at 2017/01/11


def ln_sqrtt0(beta):
    b0 = 11./(4*np.pi)**2
    b1 = 102/(4*np.pi)**4
    c1 = -9.945
    c2 = 24.191
    c3 = -5.334
    c4 = 1.452
    return (beta/(12*b0)+b1/(2.*b0**2)*np.log(6*b0/beta))*(1+c1/beta+c2/beta**2) /\
        (1+c3/beta+c4/beta**2)


r0_phys_GeV = 0.469/0.1973269718
#a in 1/GeV


def a_r0_invGeV(beta):
    return r0_phys_GeV/np.exp(ln_r0(beta))


sqrtt0r0_cont = 0.334
sqrtt0_phys = sqrtt0r0_cont*r0_phys_GeV


def a_t0_invGeV(beta):
    return sqrtt0_phys/np.exp(ln_sqrtt0(beta))


def a_r0_fm(beta):
    return GeVinv_to_fm(a_r0_invGeV(beta))


def a_t0_fm(beta):
    return GeVinv_to_fm(a_t0_invGeV(beta))
