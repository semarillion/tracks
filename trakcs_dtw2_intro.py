from dtaidistance import dtw_ndim
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import gpxpy.gpx

np.set_printoptions(linewidth=1100)
tmp_df = pd.DataFrame(columns=[])
track_dict = {}
points = []
lat = []
lon = []
elev = []

FILE_PATH_GPX = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap'

# change the directory
os.chdir(FILE_PATH_GPX)

# get list of available gpx files on local drive and output them on console
f_list=set([file for file in os.listdir() if '.gpx' in file])
print('\nfound tracks on local computer..')
print(*f_list,sep='\n')

print('\nreading files...')
for no,f in enumerate(f_list):
    print('\n',f)
    gpx_file = open(f)
    gpx = gpxpy.parse(gpx_file)

    # no iterate over the entire track data and extract multiple information
    for track in gpx.tracks:
        for segment in track.segments:

            # read each point with data of lateral, longitudinal, elevation and time
            for point_nr, point in enumerate(segment.points):
                points.append(point)
                lat.append(point.latitude)
                lon.append(point.longitude)
                elev.append(point.elevation)

    # for later data processing copy all generated data of each track to temporary pandas data frame
    tmp_df['longitudinal'] = lon
    tmp_df['lateral'] = lat
    tmp_df['elevation [m]'] = elev

    # now generate a column in pandas data frame which indicates a mulitiple of DISTANCE (just to reduce the data)
    # e.g. a 1 indicates that it is a multiple of DISTANCE
    #tmp_df['match multiple'] = f_FindValuesCloseToMultiple(tmp_df['distance from start [m]'].tolist(), DISTANCE)
    #print('track no', no, 'with', len(tmp_df), 'way points')

    # use only the data with a multiple of a specific distance
    #tmp_df=tmp_df[tmp_df['match multiple']==1]

    # due to multiple operation before the index is now wrong, hence the index column is reseted
    # and the newly added index column is dropped
    #tmp_df=tmp_df.reset_index(drop=True)

    # finally copy temporay pandas data frame to dictionary (each value of dictionary helds the data of each track)
    track_dict.update({no: tmp_df})

    # reset all lists for next loop
    lat, lon, elev = [],[],[]
    # reset pandas data frame as well as data per track for next loop
    tmp_df = pd.DataFrame(columns=[])

series1 = np.array(track_dict[0].loc[:,'longitudinal':'lateral'])
series2 = np.array(track_dict[1].loc[:,'longitudinal':'lateral'])


dtw_distance_12,dtw_matrix_12 = dtw_ndim.warping_paths(series1,series2)

dtw_distance_12_n = round(dtw_distance_12/(len(series1)+len(series2)),4)

plt.figure()
plt.plot(series1[:,0],series1[:,1],c='b',label='series1')
plt.plot(series2[:,0],series2[:,1],c='g',label='series2')
plt.legend(loc='upper left', markerscale=6)
plt.show()

#print('dtw_distance_12_n,dtw_distance_13_n,dtw_distance_23_n')
#print(dtw_distance_12_n,dtw_distance_13_n,dtw_distance_23_n)

plt.figure()
plt.title('dtw_matrix_12')
plt.imshow(dtw_matrix_12,cmap='cool',interpolation='nearest')
plt.show()



