############################################################################################

############################################################################################
import gpxpy.gpx
import pandas as pd
from datetime import timedelta
import os
import numpy as np
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt

import tracks_aux
import tracks_aux as t_aux
import sys
import folium
import time
import re

np.set_printoptions(threshold=sys.maxsize)

# define dictionary with colors
cols_dict = {0: 'blue', 1: 'orange', 2: 'green', 3: 'red', 4: 'purple', 5: 'brown',
             6: 'pink', 7: 'olive', 8: 'cyan', 10: 'black', 9: 'magenta'}

color_folium = ['#000000','#210003','#420007','#63000A','#85000D','#A60011','#C70014','#E80017','#FF0A23',
                '#FF293E','#FF475A','#FF6675','#FF8591','#FFA3AC','#FFC2C8','#FFE0E3']

colors = [
    'black',
    'black'
    'darkpurple',
    'purple',
    'darkblue',
    'blue',
    'lightblue',
    'lightgreen',
    'green',
    'darkgreen',
    'beige',
    'orange',
    'lightred',
    'red',
    'darkred',
]

# define some dictionary
track_dict = {}                     # ..for entire data of track
track_const_distance = {}           # ..for data which helds data of contant distance (DISTANZ) between way points
track_const_distance_common = {}    # ..data which helds the common part of all tracks after nearest neighbor analysis
range_dict = {}                     # ..helds the range data for each track
common_points_dict ={}

# define display settings for pandas data frame (all rows and columns shall be displayed
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# pandas dataframe for storing all lists
tmp_df = pd.DataFrame(columns=[])           # helper data frame
nbrs_pd = pd.DataFrame(columns=[])          # nearest neighbor information
lat_lon_pd = pd.DataFrame(columns=[])

SPEED_THRESH = 2                            # filter for speed
DISTANCE = 100                              # distance between way points (to reduce the data)
NS = 1000000000

# store the intermediate results in lists
lat = []
lon = []
elev = []
sp = []
times = []
speed = []
points = []
dist_per_point = []
distance = []
cum_elevation = []
speed_filt = []
dur = []
time_diff = []

lat_all = []
lon_all = []
elev_all = []
file_names = []
matched_points_of_tracks = []
index_to_be_deleted=[]
bins = []
comm_a = []
angle_bins = []
len_wp_track =[]

# define som contants
NO_LEN_TRACKS = []
NO_LEN_TRACKS_COMMON = []
START_INDEX_COMMON = []

lat_red_all, lon_red_all, dur, elev_red_all, distance_from_start_red_all = [], [], [], [],[]

# --------------------------- function definition ---------------------------------------------------
def f_PlausiCheck(nn):
    ''' check whether the way points are plausible, means way points detected by nearest neighbor
        belong to the correct range
        :parameter nn: nearest neighbor, way point per way point
        :return: 0: combination of tuple does not match the allowed combination
                 1: combination of tuple matches the allowed combination '''
    res = []  # array which helds the result of the range/per waypoint
    ret = 0  # return value
    r = 0

    for wp in nn:  # iterate over all the points per nearest neighbor list
        for i in range(0, N0_TRACKS):  # check all possible ranges
            r = 0
            if wp in range_dict[i]:
                r = i  # and store the track range which was found
                break
        res.append(r)  # and append to array for later check

    if tuple(res) in RANGE_PERMUT:  # check if the nearest neighbors are located in the correct range
        # if the range (track for waypoint is correct
        ret = 1
    else:
        # way point is located in wrong range (track)
        ret = 0

    return ret


def f__rangeCheck(nbrs):
    ''' extract line by line the way points as list and do a further check within f_PlausiCheck
     @:param: nbrs: result of the nearest neighbor analysis
     @:return: res: a list which indicates if a tuple is plausbible to the detected ranges '''
    # iterate of the tuple of nearest neighbors nbrs, send the data tofunction f_PlausiCheck which returns then
    # if a tuple matches which the plausibility (mark each tuple as true/fals
    # and add the information to the list
    res = [f_PlausiCheck(nn=[i for i in nbrs.loc[i,]]) for i in range(0, LEN_ALL_POINTS) ]

    # and return the result of the plausibility check
    return res


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)


# -------------------------------------------------------------- start of the main program ----------------------------

# change working directory
os.chdir("C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap")
# make a list of available gpx files in folder
f_list = [file for file in os.listdir() if '.gpx' in file]

# now read the gpx files and output the progress in console
print('reading files...')
for no, f in enumerate(f_list): # iterate over the list of gpx files
    # print the file name which is currently read
    print(f)
    # add the filename to list which is later used for the matplotlib legend
    file_names.append(f)
    # read the file and store information in gpx object
    gpx_file = open(f)
    gpx = gpxpy.parse(gpx_file)

    # now iterate of the tracks
    for track in gpx.tracks:
        # and segments
        for segment in track.segments:

            # read each point with data of lateral, longitudinal, elevation and time from gpx file
            for point_nr, point in enumerate(segment.points):
                # and append data to list
                points.append(point)
                lat.append(point.latitude)
                lon.append(point.longitude)
                elev.append(point.elevation)
                times.append(point.time.time())

                if point_nr == 0:
                    # some post-calculated values are set to 0 for the first point, because some post calculated
                    # values are based on difference (data_point(i) - data point(i-1))
                    speed.append(0)
                    dist_per_point.append(0)
                    distance.append(0)
                    cum_elevation.append(0)
                    speed_filt.append(0)
                    dur.append(0)
                else:
                    # append the calculated data if the first point has been passed
                    speed.append(point.speed_between(segment.points[point_nr - 1]))         # speed between way points
                    dist_per_point.append(point.distance_3d(segment.points[point_nr - 1]))  # distance between wasy points
                    distance.append(sum(dist_per_point))                                    # distance from start to qay point

                    # calculate the elapsed time from start to current point_nr
                    dur.append(timedelta(hours=times[point_nr].hour,
                                         minutes=times[point_nr].minute,
                                         seconds=times[point_nr].second) -
                    
                               timedelta(hours=times[0].hour,
                                         minutes=times[0].minute,
                                         seconds=times[0].second))

                    # filter speed and store it in list
                    last_speed_filt = speed_filt[-1]
                    if (speed[point_nr] - last_speed_filt) > SPEED_THRESH:
                        speed_filt.append((last_speed_filt + last_speed_filt + SPEED_THRESH) / 2)
                    elif (last_speed_filt - speed[point_nr]) > SPEED_THRESH:
                        speed_filt.append((last_speed_filt + (last_speed_filt - SPEED_THRESH)) / 2)
                    else:
                        speed_filt.append((last_speed_filt + speed[point_nr]) / 2)

                    # calculate now the cummulated hight
                    if point.elevation > segment.points[point_nr - 1].elevation:
                        # calculate the increase between the last two way points
                        inc = point.elevation - segment.points[point_nr - 1].elevation

                        # get the last value
                        last_value = cum_elevation[-1]

                        # add increase of hight plus the reached hight at that waypoint
                        cum_elevation.append(last_value + inc)
                    else:
                        # get the last element and maintain it
                        cum_height = cum_elevation[-1]
                        cum_elevation.append(cum_height)

    # for later data processing copy all generated data of each track to temporary pandas data frame
    tmp_df['lateral'] = lat
    tmp_df['longitudinal'] = lon
    tmp_df['elevation [m]'] = elev
    tmp_df['cum_elevation [m]'] = cum_elevation
    tmp_df['times [h/m/s]'] = times
    tmp_df['dt_duration [s]'] = dur
    tmp_df['speed [km/h]'] = [s * 3.6 for s in speed]               # convert m/s to kph - non filtered speed
    tmp_df['filt speed [km/h]'] = [s * 3.6 for s in speed_filt]     # convert m/s to kph - filtered speed
    tmp_df['distance from start [m]'] = distance

    # now generate a column in pandas data frame which indicates a mulitiple of DISTANCE (just to reduce the data)
    # e.g. a 1 indicates that it is a multiple of DISTANCE
    tmp_df['match multiple'] = t_aux.f_FindValuesCloseToMultiple(tmp_df['distance from start [m]'].tolist(), DISTANCE)
    print('track no', no, 'with', len(tmp_df), 'way points')

    # copy temporay pandas data frame to dictionary (each value of dictionary helds the data of each track)
    track_dict.update({no: tmp_df})

    # now stack all lateral, longitudinal as well as elevation values in list, this is needed for later plotting the
    # original data of tracks
    lat_all.append(lat)
    lon_all.append(lon)
    elev_all.append(elev)

    # reset all lists for next loop
    lat, lon, elev, cum_elevation, dur, times, dist_per_point, s, speed_filt, distance, speed, dur_s = \
        [], [], [], [], [], [], [], [], [], [], [], []
    # reset pandas data frame as well as data per track for next loop
    tmp_df = pd.DataFrame(columns=[])

# calcuate the number of read tracks
N0_TRACKS = len(track_dict)

# extract values in tables with multiple of DISTANCE and save coordinates in array
# now at first iterate over the number of tracks
for i in range(N0_TRACKS):
    # take only the way points with a specific distance, defined in DISTANCE
    track_const_distance.update({i: track_dict[i][track_dict[i]['match multiple'] == 1]})

    # and then extract from this list the following data to separate lists
    lat_red_all.append(track_const_distance[i]['lateral'].tolist())
    lon_red_all.append(track_const_distance[i]['longitudinal'].tolist())
    distance_from_start_red_all.append(track_const_distance[i]['distance from start [m]'].tolist())

    # store the track length of each individual track, needed for later range check
    NO_LEN_TRACKS.append(len(track_const_distance[i]))

# now stack all lat, lon and distance from start information of all tracks (reduced points - multiple of DISTANCE)
# this is indicated by the _red_ name in variables
sum_lat, sum_lon, sum_distance_from_start = [], [], []          # reset the temporary lists
for i in range(N0_TRACKS):                                      # interate over all tracks
    sum_lat += (lat_red_all[i])                                 # stack the lateral data
    sum_lon += (lon_red_all[i])                                 # and longitudinal data
    sum_distance_from_start+=(distance_from_start_red_all[i])   # and distance from start at each point

NO_LEN_TRACKS_WITH_0 = NO_LEN_TRACKS.copy()     # calculate the number of tracks and the length of each track
NO_LEN_TRACKS_WITH_0.insert(0, 0)               # insert 0 for later calculation
MIN_LEN_TRACK = min(NO_LEN_TRACKS)              # number of way points of shortest track

# now copy the stacked lateral as well as longitudinal information in data frame
lat_lon_pd['lat']=sum_lat
lat_lon_pd['lon']=sum_lon

# make the initial stacked array which helds all values for lat an long
X = np.c_[sum_lat, sum_lon]
X_all = X.copy()

# make dictionary of ranges for each track, because they are her available in one list
# the output is e.g.  {0: range(0, 256), 1: range(256, 541), 2: range(541, 836), 3: range(836, 1108)}
# first track as a range from 0...255, the second track a range of 256..541, etc.
print('starting range check...')
for i in range(0, N0_TRACKS):
    start = sum(NO_LEN_TRACKS_WITH_0[0:i + 1])      # calculate the start address
    end = sum(NO_LEN_TRACKS_WITH_0[1:i + 2])        # and end address
    print((start, end))                             # output value in console
    range_dict.update({i: range(start, end)})       # update dictionary: now with start and end

    # now defie the bins: each range of the bin is equal to the range of the individual track
    bins.append(end)

    # now set the new index for each track according to calculated start and end, because this data frame
    # helds now reduced number of way points (multiple of DISTANCE) and hence a re-index is required
    track_const_distance[i].index = range(start, end)
range_dict_inv = dict((v,k) for k,v in range_dict.items())

# complete first bin, starting from 0
bins.insert(0,0)
print('range check completed')

# ------------------------------------------ 'plot original tracks ----------------------------------------------------
color_map = discrete_cmap(len(lat_all), 'jet')

plt.figure(2)
plt.title('original tracks')
plt.ylabel('lateral')
plt.xlabel('longitudinal')
for i in range(0, len(lat_all)):
    plt.scatter(lon_all[i], lat_all[i],
                c=[i+1]*len(lon_all[i]),
                cmap=color_map,
                s=2,
                label=file_names[i])
plt.legend(loc='upper left', markerscale=6)
plt.show()

print('\tstart analysis...')
N0_TRACKS_TO_BE_DISPLAYES=0
t_start_knn_analysis = time.monotonic_ns()
for tr in range(N0_TRACKS,1,-1):
    t_start_ovl = time.monotonic_ns()
    print('\t\tlooking for multiple of',tr,'overlapping',end='')

    # do the "nearest neighbor" analysis with all way points of all tracks (stacked)
    # depending on how many tracks need to be compared
    # make 2d array with coordinates of ALL tracks (stacked!)
    # train and fit the model
    nbrs = NearestNeighbors(n_neighbors=tr, algorithm='ball_tree').fit(X)

    # store the distances as well as indices
    distances, indices = nbrs.kneighbors(X)

    # and put data of the indices in pandas data frame
    nbrs_pd = pd.DataFrame(indices)

    # columns to iterate
    cols = nbrs_pd.columns

    t_start_bins_eval = time.monotonic_ns()
    # now go over all the columns
    for col in list(cols):
        len_wp_track = []
        # extract the way points to bins according the range where a specific way point is located
        nbrs_pd['tr'+str(col)] = pd.cut(x=nbrs_pd[col], bins=bins, labels=list(range(N0_TRACKS)), right=False)

    # now iterate over the entire table, starting from the top and check whether a valid combination of
    # way points have been detected
    for idx in nbrs_pd.index:
        # ..and extract the detected ranges of the tracks to an nd array
        t=np.array(nbrs_pd.loc[idx,'tr0':])

        # now count the bins
        a = np.bincount(t)
        # and remove the not needed bins of 0
        a = a[a>0]

        # a value is plausible
        # - if all the ranges appear once
        # - the way point is clearly identified to which range it belongs
        if np.all(a == 1) == True:
            # combination of detected ranges plausible - mark it with 1 for later filtering
            comm_a.append(1)
        else:
            # combination of ranges are not plausible - mark it with 0
            comm_a.append(0)
    # copy the results of the common analysis into new data frame
    nbrs_pd['common'] = comm_a

    # and filter for members where plausible neighbors were found
    nbrs_common = nbrs_pd[nbrs_pd['common'] == 1]
    comm_a = []

    #index_to_be_deleted_ = np.empty(shape=(1,))
    #for t_ in range(tr-1,0,-1):
    #    index_to_be_deleted_ = np.c_[nbrs_common[t_]].flatten()
    #index_to_be_deleted_ = np.unique(index_to_be_deleted_)
    #print(index_to_be_deleted_)

    for i in nbrs_common.index:                         # iterate now over the nearest neighbor columns
        temp=(list(nbrs_common.loc[i,:]))               # make a list of the available members
        index_to_be_deleted+=temp                       # and add them to a list which is used later for deleting
                                                       # the entries in X (stacked)
                                                       # and displying the section with overlapping
        temp=[]                                         # delete the temporary array

    common_points_dict.update({tr:X[index_to_be_deleted]})   # store the common points in dictionary
    #common_points_dict.update({tr: X[index_to_be_deleted_]})  # store the common points in dictionary

    if len(common_points_dict[tr] > 0):                        # detect how many tracks need to
        N0_TRACKS_TO_BE_DISPLAYES+=1                    # displayed, where an overlapping was detected

    #X_new=np.delete(X,index_to_be_deleted_,axis=0)       # delete the points which are identified multiple points of
    X_new = np.delete(X, index_to_be_deleted, axis=0)   # delete the points which are identified multiple points of
                                                        # of all the tracks
    index_to_be_deleted=[]                              # clear list for next loop

    X=X_new.copy()                                      # x_new contains the opoen points to be analyzed
    t_end_ovl = time.monotonic_ns()
    print('bin analysis',(t_end_ovl - t_start_bins_eval)/NS,'s')
    print('..',(t_end_ovl-t_start_ovl)/NS,'s')

common_points_dict.update({1:X})    # nearest neighbor with single points not possible, hence
                                    # need to copy at the end of the loop
N0_TRACKS_TO_BE_DISPLAYES+=1
t_end_knn_analysis = time.monotonic_ns()
print('\n\nnearest neighbor analysis completion took',(t_end_knn_analysis-t_start_knn_analysis)/1000000000,'s')

#---------------------------------------- 'common sections' --------------------------------------------------------
plt.figure(3)
plt.title('common sections - fast algo')
plt.ylabel('lateral')
plt.xlabel('longitudinal')
color_map = discrete_cmap(N0_TRACKS_TO_BE_DISPLAYES, 'jet')

x=[]
y=[]
point_color=[]
for i in range(N0_TRACKS_TO_BE_DISPLAYES,0,-1): # no stack all multiple sections and link a color to each point
    x+= common_points_dict[i][:, 1].tolist()
    y+= common_points_dict[i][:, 0].tolist()
    point_color+= [i] * len(common_points_dict[i])

plt.scatter(x, y,
            c=point_color,
            cmap=color_map,
            s=5)
plt.colorbar(ticks=range(N0_TRACKS_TO_BE_DISPLAYES,0,-1))
plt.show()


# display multiple section in map
my_map = folium.Map(location=[48.87320775989272, 10.039810323943671], zoom_start=14,tiles='Stamen Terrain')

idx_col=0
for section in common_points_dict.keys():
    if len(common_points_dict[section])==0:
        continue
    for pts in common_points_dict[section]:
        lat,lon=pts
        folium.CircleMarker(location=[lat,lon],
                            fill=True,
                            fill_color=color_folium[idx_col],#colors[section],
                            color=color_folium[idx_col],#colors[section],
                            radius=0.5,
                            weight=2).add_to(my_map)
    idx_col+=1
my_map.save("./overlap_tracks.html")


