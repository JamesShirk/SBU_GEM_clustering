import numpy as np
from scipy.stats import gaussian_kde, iqr
from scipy.signal import argrelextrema, find_peaks
from KDEpy import FFTKDE
import pandas as pd

# floating channels are indexed as 

# 1 9 33 41 65 73 97 
def removeFloating(chan_num, chan_adc, pulse_time):
    chan_num_out = []
    chan_adc_out = []
    pulse_time_out = []
    for i in range(len(chan_num)):
        floating_channels = [1, 9, 33, 41, 65, 73, 97]
        if chan_num[i] in floating_channels:
            continue
        delta = chan_num[i] % 128
        floating_channels.append(delta)
        floating_channels.sort()
        num = floating_channels.index(delta)
        chan_num_out.append(chan_num[i] - num - (chan_num[i]//128) * 7)
        chan_adc_out.append(chan_adc[i])
        pulse_time_out.append(chan_adc[i])
    return np.array(chan_num_out), np.array(chan_adc_out), np.array(pulse_time_out)
        


'''
INPUT

row = pandas df row with 3 columns, chan_num, chan_adc, pulse_time

OUTPUT

out = pandas df series with 6 columns split up based on u or v
'''

def get_UV(row):
    #convert rows into array for better operations
    chan_num = np.array(row['chan_num'])
    chan_adc = np.array(row['chan_adc'])
    pulse_time = np.array(row['pulse_time'])

    chan_num, chan_adc, pulse_time = removeFloating(chan_num, chan_adc, pulse_time)

    u_index = np.empty_like(chan_num, dtype = bool)

    #fill array with true if it's a 'u' index, 'v' if not
    for i in range(len(chan_num)):
        if chan_num[i] % 242 <= 120:
            u_index[i] = True
        else:
            u_index[i] = False
    #re-index the rows to be from 0 to 121*5 (605)
    chan_num = chan_num % 121 + chan_num//242 * 121

    # fill u_chans with the elements where u_index is true, and v_chans where v_index is false
    # do same for adc and time
    u_chans, v_chans = chan_num[u_index], chan_num[~u_index]
    u_adc, v_adc = chan_adc[u_index], chan_adc[~u_index]
    u_time, v_time = pulse_time[u_index], pulse_time[~u_index]

    return pd.Series([u_chans, v_chans, u_adc, v_adc, u_time, v_time], 
                     index = ['u_chan_num', 'v_chan_num', 'u_chan_adc', 'v_chan_adc', 'u_pulse_time', 'v_pulse_time'])


# Wrapper function for cluster1D. For now just checks to make sure there is more than one element 
def cluster1D(row, bw = 0.05, dir = 'u'):
    index = [dir+'_chan_num_split', dir+'_chan_adc_split', dir+'_pulse_time_split', dir+'_weighted_chan_num']
    
    # just go ahead and return everything if it only has one element
    if len(row[dir+'_chan_num']) == 1:
        return pd.Series([[row[dir+'_chan_num']], row[dir+'_chan_adc'], row[dir+'_pulse_time'], row[dir+'_chan_num']], 
            index = index)
    else:
        # if more than 1 element, continue with main driver
        return __cluster1D(row, index, bw, dir)

def __cluster1D(row, index, bw = 0.05, dir = 'u'):
    chan_num = np.array(row[dir+'_chan_num'])
    chan_adc = np.array(row[dir+'_chan_adc'])
    pulse_time = np.array(row[dir+'_pulse_time'])

    # use KDE to generate minima locations
    # i.e. find locations to split the 1D clusters
    mi = generate_minima(chan_num, bw)

    # if there are no minima e.g, u channels look like: [313, 314]
    # go ahead and return it
    if len(mi) == 0:
        return pd.Series([[chan_num], [chan_adc], [pulse_time], [np.average(chan_num, weights = chan_adc)]], 
                          index = index)

    # split arrays about minima
    chan_num_out = split(chan_num, mi, chan_num)
    chan_adc_out = split(chan_adc, mi, chan_num)
    pulse_time_out = split(pulse_time, mi, chan_num)
    # take weighted average of each cluster
    weighted_chan_num = weighted_average(chan_num_out, chan_adc_out)
    #return
    return pd.Series([chan_num_out, chan_adc_out, pulse_time_out, weighted_chan_num], 
                     index = [dir+'_chan_num_split', dir+'_chan_adc_split', dir+'_pulse_time_split', dir+'_weighted_chan_num'])

'''
INPUT

arr = Jagged array of length N, where each sub-array is cluster to be averaged
weights = Jagged array of length N


OUTPUT

out = Nx1 array of weighted cluster positions
'''

def weighted_average(arr, weights):
    weightedAverage = np.empty(len(arr))
    for i in range(len(arr)):
        weight_sum = 0
        out_sum = 0
        for j in range(len(arr[i])):
            weight_sum += np.abs(weights[i][j])
            out_sum += arr[i][j]*weights[i][j]
        weightedAverage[i] = out_sum/weight_sum
    return weightedAverage

'''
INPUT

arr = 1xN array to be split
mi = Mx1 array of minima in channel numbers
chan_num = 1xN array of channel numbers

OUTPUT

out = Jagged array of length M, where each sub-array is arr split about mi based on chan_num
'''

def split(arr, mi, chan_num):
    out = [arr[chan_num < mi[0]].tolist()]
    for i in range(len(mi)):
        if i == (len(mi) - 1):
            out.append(arr[chan_num >= mi[-1]].tolist())
            continue
        out.append(arr[(chan_num >= mi[i]) * (chan_num <= mi[i+1])].tolist())
    out = list(filter(None, out))
    return out

'''
INPUT

chan_num = 1xN array
bw = scalar bandwith value, controls std of kernel


OUTPUT

mi = Mx1 array of minima points in chan_num
'''

def generate_minima(chan_num, bw):
    if len(chan_num) > 13:
        kernelx, kernely = FFTKDE(kernel = 'gaussian', bw = 'ISJ').fit(chan_num).evaluate()
        mi = find_peaks(-1*kernely)[0]
        mi = kernelx[mi]
    else:
        kernely = gaussian_kde(chan_num ,bw_method=bw)
        kernelx = np.linspace(0, 639, 640)
        mi = find_peaks(-1*kernely(kernelx))[0]
    return mi