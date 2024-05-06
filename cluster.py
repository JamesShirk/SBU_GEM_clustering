import ROOT
import numpy as np
from timeit import default_timer as timer
import pandas as pd
import sys
import itertools

import cluster1D as cl
import transform as tr

'''
INPUT

name = Str of filename
OUTPUT

out = Jagged array of length M, where each sub-array is arr split about mi based on chan_num
'''

def generate_list_ttree(tree):
    chan_num = []
    chan_adc = []
    pulse_time = []
    

    for entry in tree:
        event_chan_num = []
        event_chan_adc = []
        event_pulse_time = []
        for i in range(entry.multiplicity):
            # remove all single multiplcity events
            if entry.multiplicity <= 1:
                pass
            event_chan_num.append(entry.chan_num[i])
            event_chan_adc.append(entry.chan_adc[i])
            event_pulse_time.append(entry.pulse_time[i])
        # remove all empty events
        if (event_chan_num == [] or len(event_chan_num) == 1):
            continue
        chan_num.append(event_chan_num)
        chan_adc.append(event_chan_adc)
        pulse_time.append(event_pulse_time)
    return chan_num, chan_adc, pulse_time

'''
INPUT

name = Str of filename

OUTPUT

df = pandas dataframe with 3 columns
    each column is comprised of 1D lists of various lengths (from 2 - a few hundred)
'''

def readFile_pd(name):
    f = ROOT.TFile(name)
    tree = f.Get("T")
    
    chan_num, chan_adc, pulse_time = generate_list_ttree(tree)

    df = pd.DataFrame({
        'chan_num': chan_num,
        'chan_adc': chan_adc,
        'pulse_time': pulse_time
    })

    return df


def cluster(df):
    #split based on U or V channel
    df = df.join(df.apply(cl.get_UV, axis = 1))

    # remove events where there wasnt a u or v strip hit
    df = df[(df.u_chan_num.map(lambda chans: len(chans)) > 0) &
             (df.v_chan_num.map(lambda chans: len(chans)) > 0)]
    
    # remove redundant columns
    df.drop(columns = ['chan_num', 'chan_adc', 'pulse_time'], inplace = True)

    # apply clustering to u, v seperately
    df = df.join(df.apply(cl.cluster1D, axis=1, args = (0.05, 'u')))
    df = df.join(df.apply(cl.cluster1D, axis=1, args = (0.05, 'v')))

    # remove redundant columns
    df.drop(columns = ['u_chan_num', 'u_chan_adc', 'u_pulse_time',
                       'v_chan_num', 'v_chan_adc', 'v_pulse_time'])
    return df


def product(row):
    u_chans, v_chans = np.array(row['u_weighted_chan_num']), np.array(row['v_weighted_chan_num'])
    u_adc, v_adc = np.array(row), np.array(row[''])
    pass

#generate simple hitmap of all pairs
def plot(df):
    u_hits = df['u_weighted_chan_num'].to_numpy()
    v_hits = df['v_weighted_chan_num'].to_numpy()

    pairs_2 = []
    for i in range(len(u_hits)):
        if len(u_hits[i]) == 1 and len(v_hits[i]) == 1:
            pairs_2.append([u_hits[i][0], v_hits[i][0]])
    pairs = []
    for i in range(len(u_hits)):
        pairs +=list(itertools.product(u_hits[i],v_hits[i]))

    for i in range(len(pairs)):
        pairs[i] = tr.transform(pairs[i], 0.82, np.radians(26.5))
    cartesian_coords = tr.affine_translation(pairs)

    for i in range(len(pairs_2)):
        pairs_2[i] = tr.transform(pairs_2[i], 0.82, np.radians(26.5))
    cartesian_coords2 = tr.affine_translation(pairs_2)

    c = ROOT.TCanvas()
    hits = ROOT.TH2D("hits", "Hits", 100, -300, 300, 100, -500, 100)
    for i in cartesian_coords2:
        hits.Fill(i[0], i[1])
    c.Draw()
    hits.GetXaxis().SetTitle("x (mm)")
    hits.GetYaxis().SetTitle("y (mm)")
    hits.Draw("colz")
    c.SaveAs("plots/hits.pdf")



if __name__ == "__main__":
    df1 = readFile_pd(sys.argv[1])
    df2 = readFile_pd(sys.argv[2])
    df = pd.concat([df1, df2], ignore_index=True, sort=False)
    #df = df1.append(df2)
    df = cluster(df)
    print(df.iloc[1])
    plot(df)