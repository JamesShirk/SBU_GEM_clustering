# Clustering algorithm for GEMs @ SBU

## Running the code

Three files are needed:

1. cluster.py
2. cluster1D.py
3. transform.py

The following python packages are also necessary

- pandas
- numpy
- scipy
- pyroot

PYROOT should be configured by default with your root installation, you can check by running

        python3
         
        >>> import ROOT

If this doesn't result in an error, everything is likely okay.

The main code driver is in cluster.py. At the bottom, the code that actually runs is present

        if __name__ == "__main__":
            df1 = readFile_pd(sys.argv[1])
            df2 = readFile_pd(sys.argv[2])
            df = pd.concat([df1, df2], ignore_index=True, sort=False)
            df = cluster(df)
            plot(df)

One would run the code using the following:

        python3 cluster.py event_info_193.root event_info_194.root

One could generalize to any number of files in the code by reading in more from sys.argv (sys.argv is a variable length array that contains (in this example), [cluster.py, event_info_193.root, event_info_194.root] as strings)

If running over only one file is desired, just:

        if __name__ == "__main__":
            df = readFile_pd(sys.argv[1])
            df = cluster(df)
            plot(df)

## Explanation for what's happening

        df = readFile_pd(sys.argv[1])

The code for this can be found in lines 20 - 70 in cluster.py. A ROOT TTree is read in, converted to lists, and then converted to a pandas dataframe.

Python lists are like C++ vectors. A pandas dataframe is similar to a root TTree, but allows for one to write a function that takes in a row of the dataframe and perform an operation while not mutating the dataframe. Applying functions to dataframe rows is currently beyond the ROOT RDataFrame implementation.

Once this command has been run, your data has been read in. Your data frame is now effectively a 2D array. It has rows = number of events and 3 columns, pulse time, channel adc, and channel number.

        df = cluster(df)

This is the main driver that does all of the calculations. One can use the **df.apply()** method to apply a function to a row of a dataframe. Consider the simple example where you have a dataframe with two columns, x and y. One could then, e.g.:

        def add(row):
            return pd.Series([np.array(row['x']) + np.array(row['y'])], index = ['z'])

This could be appended to the existing dataframe via:

        df = df.join(df.apply(add, axis = 1))

All of the code works off of the principle, but with more complicated functions.

The first thing done inside of df = cluster(df) is to get the UV channels. All data from here on out is correlated to either a "u" strip or a "v" strip. The code that works here is:

        df = df.join(df.apply(cl.get_UV, axis = 1))

The main function is cl.get_UV, which is found in cluster1D.py.

        df = df[(df.u_chan_num.map(lambda chans: len(chans)) > 0) &(df.v_chan_num.map(lambda chans: len(chans)) > 0)]

This removes all events where there are only u hits, or only v hits. This is the same as saying that the length of the array containing the u or v channel numbers is greater than 0.

        df = df.join(df.apply(cl.cluster1D, axis=1, args = (0.05, 'v')))

Using the same idea as above, applying the function to a row, we run the cluster1D function which is defined in cluster1D.py.

## Final data

At this point the data looks like this:

| Name                | Data                                                |
| ---                 | ---                                                 |
| u_chan_num          |                                               [118] |
| v_chan_num          |                       [7, 9, 10, 11, 101, 102, 103] |
| u_chan_adc          |                                     [8541.33203125] |
| v_chan_adc          |   [698.3333129882812, 1446.6666259765625, 3380.3... |
| u_pulse_time        |                                     [8541.33203125] |
| v_pulse_time        |   [698.3333129882812, 1446.6666259765625, 3380.3... |
| u_chan_num_split    |                                             [[118]] |
| u_chan_adc_split    |                                     [8541.33203125] |
| u_pulse_time_split  |                                     [8541.33203125] |
| u_weighted_chan_num |                                               [118] |
| v_chan_num_split    |                   [[7, 9, 10, 11], [101, 102, 103]] |
| v_chan_adc_split    |   [[698.3333129882812, 1446.6666259765625, 3380.... |
| v_pulse_time_split  |   [[698.3333129882812, 1446.6666259765625, 3380.... |
| v_weighted_chan_num |             [10.058723859183127, 101.7823532675483] |

I will go through each row and explain, remember that I already split by U, V channels which are in the range of [0, 604] (each panasonic connector has 121 channels)

v_chan_num contains the 'v' channel numbers, e.g. all channels with signal above threshold where we counted a strip fiting. ADC and pulse time is the same, just the ADC and pulse time for the given hit.

v_chan_num_split is after the 1D clustering. In this example, the code found 2 clusters, so they are split twofold. The same is done for the adc and pulse_time. Finally, the weighted channel numbers are made. This is the weighted average within a cluster, where the weight factor is the ADC.