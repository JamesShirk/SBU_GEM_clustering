import pandas as pd
import numpy as np
import ROOT

# goal:

# take final dataframe and put it back into a tree

"""
TTree *tree = new TTree("T","Pulse_data");
tree->Branch("evt_num",&evt_num,"evt_num/i");//Event number
tree->Branch("eff_flag",&eff_flag,"eff_flag/i");//Efficient or non-efficient
tree->Branch("evt_adc",evt_adc,"evt_adc[1280]/D");//For each channel total adc count
tree->Branch("evt_threshold",evt_threshold,"evt_threshold[1280]/D");//For each channel threshold
tree->Branch("evt_adc_corr",evt_adc_corr,"evt_adc_corr[1280]/D");//For each channel corrected total adc count
tree->Branch("multiplicity",&multiplicity,"multiplicity/i");//How many channels have valid signals
tree->Branch("chan_num",chan_num,"chan_num[multiplicity]/i");//Channel number, to identify which channels have signals
tree->Branch("chan_adc",chan_adc,"chan_adc[multiplicity]/D");//For each valid channel total adc count
tree->Branch("chan_adc_corr",chan_adc_corr,"chan_adc_corr[multiplicity]/D");//For each valid channel corrected total adc count
tree->Branch("pulse_num",pulse_num,"pulse_num[multiplicity]/i");//How many pulse for each channel
// tree->Branch("pulse_wid",pulse_wid,"pulse_wid[10]/D");//Time width of each pulse, TOT. Multiple of 25 ns
// tree->Branch("pulse_max_adc",pulse_max_adc,"pulse_max_adc[10]/D");//Max ADC count for each pulse
// tree->Branch("pulse_peak_pos",pulse_peak_pos,"pulse_peak_pos[10]/D");//Time position of each pulse peak 
// tree->Branch("pulse_adc",pulse_adc,"pulse_adc[10]/D");//For each pulse total ADC count
// tree->Branch("pulse_adc_corr",pulse_adc_corr,"pulse_adc_corr[10]/D");//For each pulse corrected total ADC count
tree->Branch("pulse_time",pulse_time,"pulse_time[multiplicity]/D");//For each pulse start time, mid point of time bin


TFile *fin = new TFile(file_name,"READ");//Opens the input root file
valid_evt=0;//Number of valid event for the volatge is zero at start

"""

def make_tree(df, name):
    f = ROOT.TFile(name, "RECREATE")
    tree = ROOT.TTree("T", "clustered_1d")

    u_copy = df[["u_weighted_chan_num", "u_weighted_chan_adc", "u_weighted_chan_tme"]].copy()
    v_copy = df[["v_weighted_chan_num", "v_weighted_chan_adc", "v_weighted_chan_tme"]].copy()

    u_copy = u_copy.explode(["u_weighted_chan_num", "u_weighted_chan_adc", "u_weighted_chan_tme"])
    v_copy = v_copy.explode(["v_weighted_chan_num", "v_weighted_chan_adc", "v_weighted_chan_tme"])

    nRows = u_copy.iloc[-1].name

    evt_num = ROOT.vector('int')(0)
    u_chan_num = ROOT.vector('float')(0)
    u_chan_adc = ROOT.vector('float')(0)
    u_plse_tme = ROOT.vector('float')(0)
    v_chan_num = ROOT.vector('float')(0)
    v_chan_adc = ROOT.vector('float')(0)
    v_plse_tme = ROOT.vector('float')(0)

    tree.Branch("event_num", evt_num)
    tree.Branch("u_chan_num", u_chan_num)#, "u_chan_num/D")
    tree.Branch("u_chan_adc", u_chan_adc)#, "u_chan_adc/D")
    tree.Branch("u_plse_tme", u_plse_tme)#, "u_plse_tme/D")
    tree.Branch("v_chan_num", v_chan_num)#, "v_chan_num/D")
    tree.Branch("v_chan_adc", v_chan_adc)#, "v_chan_adc/D")
    tree.Branch("v_plse_tme", v_plse_tme)#, "v_plse_tme/D")

    for i in range(nRows):
        try:
            nUvals = len(u_copy.loc[i].index)
        except:
            continue
        if isinstance(u_copy.loc[i], pd.Series):
            u_chan_num.push_back(u_copy.loc[i]["u_weighted_chan_num"])
            u_chan_adc.push_back(u_copy.loc[i]["u_weighted_chan_adc"])
            u_plse_tme.push_back(u_copy.loc[i]["u_weighted_chan_tme"])
            evt_num.push_back(i)
        else:
            for j in range(nUvals):
                u_chan_num.push_back(u_copy.loc[i].iloc[j]["u_weighted_chan_num"])
                u_chan_adc.push_back(u_copy.loc[i].iloc[j]["u_weighted_chan_adc"])
                u_plse_tme.push_back(u_copy.loc[i].iloc[j]["u_weighted_chan_tme"])
                evt_num.push_back(i)

    nRows = v_copy.iloc[-1].name

    for i in range(nRows):
        try:
            nVvals = len(v_copy.loc[i].index)
        except:
            continue
        if isinstance(v_copy.loc[i], pd.Series):
            v_chan_num.push_back(v_copy.loc[i]["v_weighted_chan_num"])
            v_chan_adc.push_back(v_copy.loc[i]["v_weighted_chan_adc"])
            v_plse_tme.push_back(v_copy.loc[i]["v_weighted_chan_tme"])
            evt_num.push_back(i)
        else:
            for j in range(nVvals):
                v_chan_num.push_back(v_copy.loc[i].iloc[j]["v_weighted_chan_num"])
                v_chan_adc.push_back(v_copy.loc[i].iloc[j]["v_weighted_chan_adc"])
                v_plse_tme.push_back(v_copy.loc[i].iloc[j]["v_weighted_chan_tme"])
                evt_num.push_back(i)
    tree.Fill()

    f.Write()
    f.Close()

    return 0

# def make_tree(df, name):
#     data = {key: df[key].values for key in ["u_chan_num_split", "v_chan_num_split"]}
#     #print(data)
#     for i in data["u_chan_num_split"]:
#         print(i)
#         i = np.array(i, dtype = object)
#     for i in data["v_chan_num_split"]:
#         i = np.array(i, dtype = object)
#     #print(data)
#     rdf = ROOT.RDF.FromNumpy(data)
#     rdf.Snapshot("tree", "out.root")