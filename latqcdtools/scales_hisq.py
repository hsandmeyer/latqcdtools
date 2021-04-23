import numpy as np
from latqcdtools.tools import *


def beta_func(beta):
    nf = 3.
    b0 = (11.-2.*nf/3.)/(4*np.pi)**2
    b1 = (102.-38.*nf/3.)/(4*np.pi)**4
    return (b0*10./beta)**(-b1/(2.*b0**2))*np.exp(-beta/(20.*b0))


# https://arxiv.org/pdf/1111.1710.pdf
def a_times_fk_2012(beta):  # a*fk
    c0fk = 7.65667
    c2fk = 32911.0
    d2fk = 2388.0
    return (c0fk*beta_func(beta)+c2fk*10./beta*beta_func(beta)**3) / \
        (1+d2fk*10./beta*beta_func(beta)**2)

# https://arxiv.org/pdf/1407.6387.pdf
# Fit by Peter Petreczky in mail at 25/01/2018


def a_times_fk_2014(beta):  # a*fk
    c0fk = 7.49415
    c2fk = 46049.0
    d2fk = 3671.0
    return (c0fk*beta_func(beta)+c2fk*10./beta*beta_func(beta)**3) / \
        (1+d2fk*10./beta*beta_func(beta)**2)

# https://arxiv.org/pdf/1407.6387.pdf


def a_div_r1_2014(beta):
    c0 = 43.1
    c2 = 343236.0
    d2 = 5514.0
    return (c0*beta_func(beta) + c2*(10/beta)*beta_func(beta)**3) / \
        (1 + d2*(10/beta)*beta_func(beta)**2)


# https://arxiv.org/pdf/1111.1710.pdf
def a_div_r1_2012(beta):
    c0 = 44.06
    c2 = 272102.0
    d2 = 4281.0
    return (c0*beta_func(beta) + c2*(10/beta)*beta_func(beta)**3) / \
        (1 + d2*(10/beta)*beta_func(beta)**2)


# As all the usual scales are from 2012 we use that as default
def a_fk_invGeV_2012(beta):
    fKexpnew = 156.1
    return (a_times_fk_2012(beta)*np.sqrt(2.)*1000)/fKexpnew


def a_fk_fm_2012(beta):
    return GeVinv_to_fm(a_fk_invGeV(beta))


def a_fk_invGeV_2014(beta):
    fKexpnew = 156.1
    return (a_times_fk_2014(beta)*np.sqrt(2.)*1000)/fKexpnew


def a_fk_fm_2014(beta):
    return GeVinv_to_fm(a_fk_invGeV_2014(beta))


def a_r1_invGeV_2012(beta):
    r1_phys_fm = 0.3106  # https://arxiv.org/pdf/1111.1710.pdf
    return fm_to_GeVinv(r1_phys_fm*a_div_r1_2012(beta))


def a_r1_fm_2012(beta):
    r1_phys_fm = 0.3106  # https://arxiv.org/pdf/1111.1710.pdf
    return r1_phys_fm*a_div_r1_2012(beta)


def a_r1_invGeV_2014(beta):
    r1_phys_fm = 0.3106  # https://arxiv.org/pdf/1407.6387.pdf
    return fm_to_GeVinv(r1_phys_fm*a_div_r1_2014(beta))


def a_r1_fm_2014(beta):
    r1_phys_fm = 0.3106  # https://arxiv.org/pdf/1407.6387.pdf
    return r1_phys_fm*a_div_r1_2014(beta)
