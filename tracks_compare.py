############################################################################################
# script which reads gpx tracks and does some analysis
#  - plotting all tracks with original data
#  - plotting all tracks AND common section (common sections are identified via
#       nearest neigbor algorithm of scikit learn
#  - plotting the time advantage/lag compared to a referenced track over traveled distance
#  - speed of traveled distance
############################################################################################
import gpxpy.gpx
import pandas as pd
from datetime import timedelta
import os
import numpy as np
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
import tracks_aux as t_aux
import sys
from itertools import permutations

np.set_printoptions(threshold=sys.maxsize)

# define dictionary with colors
cols_dict = {0: 'blue', 1: 'orange', 2: 'green', 3: 'red', 4: 'purple', 5: 'brown',
             6: 'pink', 7: 'olive', 8: 'cyan', 10: 'black', 9: 'magenta'}

# define some dictionary
track_dict = {}                     # ..for entire data of track
track_const_distance = {}           # ..for data which helds data of contant distance (DISTANZ) between way points
track_const_distance_common = {}    # ..data which helds the common part of all tracks after nearest neighbor analysis
range_dict = {}                     # ..helds the range data for each track

# define display settings for pandas data frame (all rows and columns shall be displayed
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# pandas dataframe for storing all lists
points_df = pd.DataFrame(columns=[])        # all way points for the individual track
tmp_df = pd.DataFrame(columns=[])           # helper data frame
nbrs_pd = pd.DataFrame(columns=[])          # nearest neighbor information
times_pd = pd.DataFrame(columns=[])         # data with times and difference to reference track
speeds_pd = pd.DataFrame(columns=[])        # speed information between way points

SPEED_THRESH = 2                            # filter for speed
DISTANCE = 100                              # distance between way points (to reduce the data)

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


def f_rangeCheck(nbrs):
    ''' extract line by line the way points as list and do a further check within f_PlausiCheck
     @:param: nbrs: result of the nearest neighbor analysis
     @:return: res: a list which indicates if a tuple is plausbible to the dtected ranges '''
    # iterate of the tuple of nearest neighbors nbrs, send the data tofunction f_PlausiCheck which returns then
    # if a tuple matches which the plausibility (mark each tuple as true/fals
    # and add the information to the list
    res = [f_PlausiCheck(nn=[i for i in nbrs.loc[i,]]) for i in range(0, LEN_ALL_POINTS) ]

    # and return the result of the plausibility check
    return res


# -------------------------------------------------------------- start of the main program ----------------------------

# change current working directory
os.chdir("C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\compare")
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

# define some constants for later calculation
LEN_ALL_POINTS = len(sum_lat)
NO_LEN_TRACKS_WITH_0 = NO_LEN_TRACKS.copy()     # calculate the number of tracks and the length of each track
NO_LEN_TRACKS_WITH_0.insert(0, 0)               # insert 0 for later calculation
MIN_LEN_TRACK = min(NO_LEN_TRACKS)              # number of way points of shortest track
RANGE_PERMUT = list(permutations(list(range(0, N0_TRACKS))))    # make a list of possible combinations for later check
                                                                # if a combination of points is plausible

# make dictionary of ranges for each track, because they are her available in one list
# the output is e.g.  {0: range(0, 256), 1: range(256, 541), 2: range(541, 836), 3: range(836, 1108)}
# first track as a range from 0...255, the second track a range of 256..541, etc.
for i in range(0, N0_TRACKS):
    start = sum(NO_LEN_TRACKS_WITH_0[0:i + 1])      # calculate the start address
    end = sum(NO_LEN_TRACKS_WITH_0[1:i + 2])        # and end address
    print((start, end))                             # output value in console
    range_dict.update({i: range(start, end)})       # update dictionary: now with start and end

    # now set the new index for each track according to calculated start and end, because this data frame
    # helds now reduced number of way points (multiple of DISTANCE) and hence a re-index is required
    track_const_distance[i].index = range(start, end)

# do the "nearest neighbor" analysis with all way points of all tracks (stacked)
# depending on how many tracks need to be compared
# make 2d array with coordinates of ALL tracks (stacked!)
X = np.c_[sum_lat, sum_lon]
# train and fit the model
nbrs = NearestNeighbors(n_neighbors=N0_TRACKS, algorithm='ball_tree').fit(X)
# get the results of the analysis
distances, indices = nbrs.kneighbors(X)
# and put data of the indices in pandas data frame
nbrs_pd = pd.DataFrame(indices)
# do the range check for every nearest neighbor to check whether the tuple of indices returned by the nearest neighbor
# analysis is plausible
nbrs_pd['common'] = list(f_rangeCheck(nbrs_pd))
# and filter for members where plausible neighbors were found
nbrs_common = nbrs_pd[nbrs_pd['common'] == 1]

# let all tracks now start where the first common point in all tracks was found
for i in range(N0_TRACKS):
    #define start index, where tracks are equal onwards, ideally nbrs_common.index[0] works fine...
    # e.g. [8, 264, 550, 859] which means: the common part of the tracks begin at 8@fist track, 264@second track
    # 550@thrid track and 859@fourth track
    print(nbrs_common.head(15))
    idx = int(input('index please'))
    START_INDEX_COMMON.append(nbrs_common.loc[nbrs_common.index[idx],i])
    # filter table with information from start (where all tracks are common and copy the data to new pandas data frame
    track_const_distance_common[i]=track_const_distance[i].loc[START_INDEX_COMMON[i]::, :]
    # and drop not required coloums because they are re-calculated (e.g. distance from start would be now wrong because
    # some points have been removed due to the reduction of the way points according to DISTANCE
    track_const_distance_common[i]=track_const_distance_common[i].drop(['distance from start [m]','match multiple'],axis=1)

    # calculate the length of each track and store it in list
    NO_LEN_TRACKS_COMMON.append(len(track_const_distance_common[i]))
 # number of way points of shortest track - this is need because the shortes track defines the lenght where a
 # comparison is possible
MIN_LEN_TRACK_COMMON = min(NO_LEN_TRACKS_COMMON)

# now adjust all tracks on the length of the shortest track that a comparison of tracks is possible
for tr in range(N0_TRACKS):
    track_const_distance_common[tr] = track_const_distance_common[tr].loc[START_INDEX_COMMON[tr]:START_INDEX_COMMON[tr]+MIN_LEN_TRACK_COMMON-1:, :]

# now generate elapsed time@way point as well as distance traveled since start for each track
# iterate of the number of tracks
for tr in range(N0_TRACKS):
    # no iterate over the individual track
    for cnt,idx in enumerate(track_const_distance_common[tr].index):
        # the first element need a special handling for later difference calcluation
        if cnt==0:
            # duration at the fist common point is set to 0
            dur.append(timedelta(hours=0,minutes=0,seconds=0))
            #dur.append(0)
            # and store the value as a start time
            START_TIME=track_const_distance_common[tr].loc[idx,'times [h/m/s]']
        else:
            # calculate the elapsed time of each way point against START_TIME and store it in list
            times=track_const_distance_common[tr].loc[idx,'times [h/m/s]']
            dur.append(timedelta(hours=times.hour,
                                 minutes=times.minute,
                                 seconds=times.second) -

                       timedelta(hours=START_TIME.hour,
                                 minutes=START_TIME.minute,
                                 seconds=START_TIME.second))

    # store the list (elapsed time of each point compared to START_TIME)
    track_const_distance_common[tr]['elapsed time']=dur
    # and make a addtional column with fixed travled distance, based on DISTANCE
    track_const_distance_common[tr]['traveled_distande [m]']=[x * DISTANCE for x in range(0, MIN_LEN_TRACK_COMMON)]

    # reset temporary variables
    dur,START_TIME=[],0

# now copy the time/speed information from track_const_distance_common in times_pd/speeds_pd for later time comparison
for i in range(N0_TRACKS):
    # move the elapesed time track by track to times_pd by using a suitable name for each column
    times_pd.loc[:,'Track_'+str(i)]=track_const_distance_common[i]['elapsed time'][0:MIN_LEN_TRACK].values
    # do the same for the speed information in another pandas data frame
    speeds_pd.loc[:, 'Track_' + str(i)] = track_const_distance_common[i]['filt speed [km/h]'][0:MIN_LEN_TRACK].values
# now add the distance, fixed steps, used for the x axes when plotting the data
times_pd['Distance [m]']=[x * DISTANCE for x in range(0, MIN_LEN_TRACK_COMMON)]
speeds_pd['Distance [m]']=[x * DISTANCE for x in range(0, MIN_LEN_TRACK_COMMON)]



# START time correction -----------------------------------------------------------------------------------
times_l=[]
track_corr_l = []
time_cum = timedelta(hours=0,minutes=0,seconds=0)
# iterate now over the available tracks
for tr in times_pd.columns[0:N0_TRACKS]:
    # and than over the several way points within the track
    for i in range(1,len(times_pd.index)):
        # split the current time information of the way point - only time is required
        #tmp = str(times_pd.loc[i,tr]).split(' ')[-1]
        h1,min1,sec1 = [int(i) for i in str(times_pd.loc[i,tr]).split(' ')[-1].split(':')]

        # and the time information from previous way point - only time is required
        #tmp = str(times_pd.loc[i-1,tr]).split(' ')[-1]
        h0,min0,sec0 = [int(i) for i in str(times_pd.loc[i-1,tr]).split(' ')[-1].split(':')]

        # calculate the delay between the way points in the current track
        delta = (timedelta(hours=h1,minutes=min1,seconds=sec1) -
              timedelta(hours=h0,minutes=min0,seconds=sec0))

        # record the last calculated time difference as long the time_l list exist
        if len(times_l)!=0:
            cur_diff = times_l[-1]

        # if the calculated time difference is lager than on minute (assumuming pausing time)
        if delta > timedelta(seconds=59):
            # use the previous information
            times_l.append(cur_diff)
        else:
            # calculated time difference is in valid range, hence append the newly calculated delta time
            times_l.append(timedelta(hours=h1,minutes=min1,seconds=sec1) -
                  timedelta(hours=h0,minutes=min0,seconds=sec0))

        time_cum += times_l[-1]                 # sum the time differences of the track
        track_corr_l.append(time_cum)

    # insert NULL values at the beginning due to the fact, that the previous calcualtion does not start from the
    # the beginning but a starting value of 00:00:00 is required in the newly calculated columns
    times_l.insert(0,timedelta(seconds=0))
    track_corr_l.insert(0, timedelta(seconds=0))

    # now add the newly calculated "difference between way points" per track
    # and the corrected duration within the track in a pandas data frame
    times_pd[str(tr)+'_corr']=track_corr_l

    # now reset values for next loop to avoid uncontrolled addition of values
    times_l=[]
    track_corr_l=[]
    time_cum = timedelta(hours=0, minutes=0, seconds=0)

# now rearange the columns again - matplot lib part expects the columns to be displayed in a specific order
column_list = list(times_pd.columns)[-N0_TRACKS::1] + ['Distance [m]'] + list(times_pd.columns[:N0_TRACKS])
times_pd=times_pd.reindex(columns=column_list)
# END time correction --------------------------------------------------------------------------------------



# now make a pandas dataframe with calculation of the time distance compared between tracks
# interate now only over the tracks, because the pandas dataframe contains also the speed info
# difference calculation is based on seconds(!) and no time object
tr = times_pd.columns[1:N0_TRACKS]  # iterate from second track...last track. The first track is the reference!
for t in tr:  # iterate now over each individual track
    # first one is set to zero, that later difference calculation is possible
    time_diff.append(0)

    # loop over the current track
    for i in list(times_pd.index)[1::]: # ignore the first element
        # and add the time difference between way points of current track to linked way point of referenced track
        time_diff.append(float((times_pd.loc[i, 'Track_0_corr'].total_seconds() - times_pd.loc[i, t].total_seconds())))
    # once loop over track is completed move the ist to pandas data frame
    times_pd['diff_track_' + str(t)] = time_diff
    # and reset the temp buffer for next loop
    time_diff = []


## -------------------------------------------------- the data -------------------------------------------------------
#
## --------------------------------------------- 'original tracks ----------------------------------------------------
for i in range(0, N0_TRACKS):
    matched_points_of_tracks.append(nbrs_common[i].tolist())
plt.figure(2)
plt.title('original tracks')
plt.ylabel('lateral')
plt.xlabel('longitudinal')
for i in range(0, len(lat_all)):
    plt.scatter(lon_all[i], lat_all[i],
                c=cols_dict[i],
                s=2,
                label=file_names[i])
plt.legend(loc='upper left', markerscale=6)
plt.show()

## ---------------------------------------- 'common sections' --------------------------------------------------------
#plt.figure(3)
#plt.title('common sections')
#plt.ylabel('lateral')
#plt.xlabel('longitudinal')
#
## loop over all tracks
#for i in range(0, N0_TRACKS):
#    # and plot each track and give plot a name
#    plt.scatter(lon_red_all[i], lat_red_all[i],
#                c=cols_dict[i],
#                s=5,
#                label=file_names[i])
#    # plot the common sections
#    for no, p in enumerate(matched_points_of_tracks[i]):
#        plt.scatter(sum_lon[p], sum_lat[p], c=cols_dict[10], s=5)
#
#        # every km and only for track one to avoid to many text
#        if no%(1000/DISTANCE)==0 and i==0:
#            # plot the distance from start
#            plt.text(sum_lon[p],sum_lat[p],s=str(round(sum_distance_from_start[p]/1000,1)))
#plt.legend(loc='upper left', markerscale=6)
#plt.show()

# --------------------------------- time advantage/lag over distance and elevation ------------------------------------
fig, ax1 = plt.subplots()
ax1.set_title(' time advantage/lag over distance')
ax1.set_xlabel('traveled distance [km]')
ax1.set_ylabel(' time [min]')
ax1.grid(True)

for i in range(1,N0_TRACKS):
   idx=times_pd.columns[i+N0_TRACKS*2] # start column = diff_track_Track_1 up to diff_track_Track_x
   print(idx)
   ax1.plot(times_pd['Distance [m]']/1000,              # x axes = distance
            times_pd[idx]/60,c=cols_dict[i],            # y axes = calculated difference of current track to referenced track
            label=file_names[i])

ax1.plot(times_pd['Distance [m]']/1000,                 # plot the reference line
        [0]*len(times_pd),
        c=cols_dict[0],
        label=file_names[0]+'_REF')
ax1.legend(loc='upper left',markerscale=6)              # place the legend

ax2=ax1.twinx()                                             # second y axis for elevation required hence share the y axes
ax2.plot(times_pd['Distance [m]']/1000,                     # plot the x axes
          track_const_distance_common[0]['elevation [m]'],  # and plot the elevation a second y axes
         c='black',
         linewidth=3)
ax2.set_ylabel('elevation [m]')                             # set the name of the y axes
plt.show()

## ------------------------------------------------ speeds/ average speed --------------------------------------
#plt.figure(7)
#plt.title('speeds along track')
#plt.xlabel(' km ')
#plt.ylabel('speed')
#for i in range(0,N0_TRACKS):
#    plt.plot(times_pd['Distance [m]']/1000,
#             track_const_distance_common[i]['filt speed [km/h]'],
#             label=file_names[i])
#    plt.plot(times_pd['Distance [m]']/1000,
#             [track_const_distance_common[i]['filt speed [km/h]'].mean()]*len(times_pd['Distance [m]']),
#             c=cols_dict[i])
#    y_text=track_const_distance_common[i]['filt speed [km/h]'].tolist()[-1]
#plt.legend(loc='upper left')
#plt.show()