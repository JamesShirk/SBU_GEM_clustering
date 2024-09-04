import ROOT
import numpy as np
from timeit import default_timer as timer
import pandas as pd
import sys
import itertools
import os

import cluster1D as cl
import transform as tr
import make_tree as tree

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

    cartesian_coords_cut = []
    for i in cartesian_coords:
        if i[0] < -120 or i[0] > 120:
            continue
        if i[1] > 0 or i[1] < -400:
            continue
        cartesian_coords_cut.append(i)

    for i in range(len(pairs_2)):
        pairs_2[i] = tr.transform(pairs_2[i], 0.82, np.radians(26.5))
    cartesian_coords2 = tr.affine_translation(pairs_2)

    c = ROOT.TCanvas()
    hits = ROOT.TH2D("hits", "Hits", 1000, -300, 300, 1000, -500, 100)
    for i in cartesian_coords:
        hits.Fill(i[0], i[1])
    c.Draw()
    hits.GetXaxis().SetTitle("x (mm)")
    hits.GetYaxis().SetTitle("y (mm)")
    hits.Draw("colz")
    c.SaveAs("plots/hits.pdf")


    c2 = ROOT.TCanvas()
    #hits_cut = ROOT.TH2D("hits_cut", "Hits_cut", 100, -150, 150, 100, -430, 30)
    hits_cut = ROOT.TH2D("hits_cut", "Hits_cut", 1000, -300, 300, 1000, -500, 100)
    for i in cartesian_coords_cut:
        hits_cut.Fill(i[0], i[1])
    c2.Draw()
    hits_cut.GetXaxis().SetTitle("x (mm)")
    hits_cut.GetYaxis().SetTitle("y (mm)")
    hits_cut.Draw("colz")
    c2.SaveAs("plots/hits_cut.pdf")

    c3 = ROOT.TCanvas()
    hits_2 = ROOT.TH2D("hits_cut", "Hits_cut", 1000, -300, 300, 1000, -500, 100)
    for i in cartesian_coords2:
        hits_2.Fill(i[0], i[1])
    c3.Draw()
    hits_2.GetXaxis().SetTitle("x (mm)")
    hits_2.GetYaxis().SetTitle("y (mm)")
    hits_2.Draw("colz")
    c3.SaveAs("plots/hits_2.pdf")

    cluster_size = ROOT.TH1D("clusters", "clusters", 9, 1, 10)

    c1 = ROOT.TCanvas()
    for i in u_hits:
        cluster_size.Fill(len(i))
    for i in v_hits:
        cluster_size.Fill(len(i))
    c1.Draw()
    cluster_size.GetXaxis().SetTitle("N clusters")
    cluster_size.GetYaxis().SetTitle("#")
    cluster_size.Draw("colz")
    c1.SaveAs("plots/cluster_size.pdf")



if __name__ == "__main__":

    files = os.listdir(sys.argv[1])
    dfs = []
    for file in files:
        dfs.append(readFile_pd("{}{}".format(sys.argv[1], file)))
    df = pd.concat(dfs, ignore_index = True, sort = False)
    #df = readFile_pd(sys.argv[1])
    df = cluster(df)
    #tree.make_tree(df, "cluster_193.root")
    #print(df.iloc[1])
    plot(df)