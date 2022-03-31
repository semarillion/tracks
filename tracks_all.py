import datetime
import sys
import gpxpy.gpx
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import timedelta
import os
from tracks_aux import f_CalcAngleDeg,f_FindValuesCloseToMultiple,f_CalWpDistance

# define some dictionary
track_dict = {}                     # ..for entire data of track
cols_dict={0:'blue',1:'orange',2:'green',3:'red',4:'purple',5:'brown',6:'pink',7:'olive',8:'cyan'}
cat_dir_dict = {0:'N',1:'NO',2:'O',3:'SO',4:'S',5:'SW',6:'W',7:'NW'}

cols_track = ['tr_name',
              'tr_cum_eval',
              'tr_highest_point',
              'tr_lowest_point',
              'tr_duration',
              'tr_distance',
              'tr_gradient',
              'tr_import_datetime']

# set display options for pandas data frame
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# create empty pandas dataframe for storing all lists
tmp_df = pd.DataFrame(columns=[])
tracks_sum_pd = pd.DataFrame(columns=[])
tracks_to_be_imported_pd = pd.DataFrame(columns=[])

# constants
DISTANCE = 50 # distance between way points in m (to reduce the data)

# file paths's
FILE_PATH_GPX = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap'
FILE_PATH_CSV = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap\\csv'
FILE_STATISTICS = 'all_track_statistics.csv'

# store the intermediate results in lists
lat=[]
lon=[]
elev=[]
times=[]
speed=[]
points=[]
dist_per_point=[]
distance=[]
cum_elevation=[]
dur=[]

lat_all=[]
lon_all=[]
elev_all=[]
sp_all=[]
angle_bins = [0]

# generate the bins according the wind direction, see https://de.wikipedia.org/wiki/Windrichtung
for i in range(0,360,45):
    angle_bins.append(i+22.5)
# loop does not include the last value, hence it is added at a last step
angle_bins.append(360.0)

# section local functions ----------------------------------------------------------------------------------------
def f_CalculateData(tmp_df):
    ''' this function is called for every track to be analyzed. I generates several data e.g. distance,
    elevation, gradient, time and speed between way points
    @param tmp_df: dataframe which helds some data
    @type tmp_df: pandas data frame
    @return: eangle,dist_wp, elevation_wp, gradient_wp,time_delta_wp, speed_wp
            calculated values based on information in pandas data frame
    @rtype: tuple'''

    # init needed arrays
    angle,dist_wp,elevation_wp,gradient_wp, time_delta_wp, speed_wp = [],[], [], [],[],[]

    # iterate now over index of the current track
    for idx in tmp_df.index:
        # skip the first index because for further calculation a difference is needed, hence we start from 2. point
        if idx == 0:
            dist_wp.append(0)
            elevation_wp.append(0)
            gradient_wp.append(0)
            time_delta_wp.append(0)
            speed_wp.append(0)
        else:
            # get the coordinates from current point and point before and calculate the distance as well as angel
            # between the two way points
            p1 = tuple(tmp_df.loc[idx, 'longitudinal':'lateral'])
            p0 = tuple(tmp_df.loc[idx - 1, 'longitudinal':'lateral'])
            # add the calculated angle to list
            angle.append(f_CalcAngleDeg(p0, p1))
            dist_wp.append(f_CalWpDistance(p0,p1))

            # calculate the difference of elevation between two way points
            delta = tmp_df.loc[idx,'elevation [m]'] - tmp_df.loc[idx-1,'elevation [m]']
            elevation_wp.append(round(delta,3))

            # calculate th gradient between two qway points
            delta = (elevation_wp[-1]/dist_wp[-1])*100
            gradient_wp.append( round(delta,2) )

            # calculate the time difference between two waypoints
            h1 = tmp_df.loc[idx, 'times [h/m/s]'].hour
            m1 = tmp_df.loc[idx, 'times [h/m/s]'].minute
            s1 = tmp_df.loc[idx, 'times [h/m/s]'].second
            t1 = timedelta(hours=h1,minutes=m1,seconds=s1)
            h0 = tmp_df.loc[idx-1, 'times [h/m/s]'].hour
            m0 = tmp_df.loc[idx-1, 'times [h/m/s]'].minute
            s0 = tmp_df.loc[idx-1, 'times [h/m/s]'].second
            t0 = timedelta(hours=h0, minutes=m0, seconds=s0)
            time_delta_wp.append((t1-t0).total_seconds())

            # calculate the average speed between two waypoints
            speed_wp.append(dist_wp[-1]/time_delta_wp[-1]*3.6)


    # add the last calculated value as the last list in element, this is needed because one eleement is
    # missing (due to skipping the index 0)
    last_angle = angle[-1]
    angle.append(last_angle)

    return angle,dist_wp, elevation_wp, gradient_wp,time_delta_wp, speed_wp

# end section local functions ---------------------------------------------------------------------------------------



# main program -----------------------------------------------------------------------------------------------------

# change the directory
os.chdir(FILE_PATH_GPX)

# read csv of track statistic to check which track has been analyzed so far and to identify later which tracks
# are newly added in the list
try:
    tracks_sum_pd = pd.read_csv(FILE_STATISTICS,index_col=None)
except:
    tracks_sum_pd = pd.DataFrame(columns=cols_track)
    tracks_sum_pd.to_csv(FILE_STATISTICS,index=False)
# extract the track names only to list
track_name_l = set(tracks_sum_pd['tr_name'].to_list())
print('\nfound recorded tracks...')
print(*track_name_l,sep='\n')

# get list of available gpx files on local drive and output them on console
f_list=set([file for file in os.listdir() if '.gpx' in file])
print('\nfound tracks on local computer..')
print(*f_list,sep='\n')

# compare and list tracks which are not imported yet and output them on console or terminate program
diff_track_list = f_list.difference(track_name_l)
if len(diff_track_list)==0:
    print('\n\nnothing to import')
    sys.exit()
else:
    print('\ntracks to be imported...')
    print(*diff_track_list,sep='\n')

print('\nreading files...')
for no,f in enumerate(diff_track_list):
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
                times.append(point.time.time())

                # init values for the beginning - set all values to zero
                if point_nr == 0:
                    dist_per_point.append(0)
                    distance.append(0)
                    cum_elevation.append(0)
                    dur.append(0)
                else:
                    dist_per_point.append(
                        point.distance_3d(segment.points[point_nr - 1]))  # distance between wasy points
                    distance.append(sum(dist_per_point))  # distance from start to qay point

                    # calculate the duration from start to current point_nr
                    dur.append(timedelta(hours=times[point_nr].hour,
                                         minutes=times[point_nr].minute,
                                         seconds=times[point_nr].second) -

                               timedelta(hours=times[0].hour,
                                         minutes=times[0].minute,
                                         seconds=times[0].second))

                    # calculate the cummulated height over track
                    if point.elevation > segment.points[point_nr - 1].elevation:

                        # calculate the increas between the last two way points
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
    tmp_df['longitudinal'] = lon
    tmp_df['lateral'] = lat
    tmp_df['elevation [m]'] = elev
    tmp_df['cum_elevation [m]'] = cum_elevation
    tmp_df['times [h/m/s]'] = times
    tmp_df['dt_duration [s]'] = dur
    tmp_df['distance from start [m]'] = distance

    # now generate a column in pandas data frame which indicates a mulitiple of DISTANCE (just to reduce the data)
    # e.g. a 1 indicates that it is a multiple of DISTANCE
    tmp_df['match multiple'] = f_FindValuesCloseToMultiple(tmp_df['distance from start [m]'].tolist(), DISTANCE)
    print('track no', no, 'with', len(tmp_df), 'way points')

    # use only the data with a multiple of a specific distance
    tmp_df=tmp_df[tmp_df['match multiple']==1]

    # due to multiple operation before the index is now wrong, hence the index column is reseted
    # and the newly added index column is dropped
    tmp_df=tmp_df.reset_index(drop=True)

    # calculate some more data ...e.g. angle between points, distance between points, speed between points
    # elevation between points, gradient, needed time as well as speed between two way points
    print('add more data..')
    tmp_df['angle'],\
    tmp_df['dist_wp'],\
    tmp_df['elevation_wp'],\
    tmp_df['gradient_wp'],\
    tmp_df['time_delta_wp'],\
    tmp_df['speed_wp [km/h]']=f_CalculateData(tmp_df)

    # Based on the driven angle between the last two way points the angle is now categorized
    # and added as a new column to the pandas dataframe
    tmp_df['cat_dir'] = pd.cut(x=tmp_df['angle'],
                               include_lowest=True,                     # include also the lowest value to border
                               bins=angle_bins,                         # bins according the wind direction
                               labels=(0, 1, 2, 3, 4, 5, 6, 7, 0),      # wind direction category
                               ordered=False)                           # allows multiple lables (due to angle jump at
                                                                        # 0°/360°

    # Previously, the angle was mapped into a direction category and now the direction category
    # is mapped in wind directions (e.g. NO, SW, etc.) and then added to the pandas dataframe
    tmp_df['dir']= [cat_dir_dict[i] for i in tmp_df['cat_dir'].to_list()]

    # drop not needed column
    tmp_df=tmp_df.drop(['match multiple'],axis=1)

    # change now to target folder to store csv
    os.chdir(FILE_PATH_CSV)
    # write the current pandas dataframe of track x to csv
    print('write track to csv..',end='')
    tmp_df.to_csv(f+'.csv',index=None)
    print('done..')
    # and change back to gpx folder
    os.chdir(FILE_PATH_GPX)

    # finally copy temporay pandas data frame to dictionary (each value of dictionary helds the data of each track)
    track_dict.update({no: tmp_df})


    # track statistics --------------------------------------------------------------------------------------------
    # make some statistics for the track summary
    tr_name = f
    tr_cum_eval = round( float(tmp_df.tail(1)['cum_elevation [m]']),2)
    tr_highest_point = round((tmp_df['elevation [m]'].max()),2)
    tr_lowest_point = round((tmp_df['elevation [m]'].min()), 2)
    tr_duration = tmp_df.tail(1)['dt_duration [s]'].any()
    tr_distance = round(float(tmp_df.tail(1)['distance from start [m]']),2)
    tr_gradient = round(tr_cum_eval/tr_distance*100,2)

    # create the actual date for recording/storing info in cvs file
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d")

    # make new row for pandas dataframe with values calculated above
    new_row = {'tr_name':f,
               'tr_cum_eval':tr_cum_eval,
               'tr_highest_point':tr_highest_point,
               'tr_lowest_point':tr_lowest_point,
               'tr_duration':tr_duration,
               'tr_distance':tr_distance,
               'tr_gradient':tr_gradient,
               'tr_import_datetime':date_time}

    # tracks_sum_pd contains the previously read tracks, also from older imports, so new ones are appended to the back
    tracks_sum_pd = tracks_sum_pd.append(new_row, ignore_index=True)
    # Here the tracks read in the session are saved and later provided as csv for further import into the
    # Postgres database
    tracks_to_be_imported_pd = tracks_to_be_imported_pd.append(new_row, ignore_index=True)

    # reset all lists for next loop
    lat, lon, elev, cum_elevation, dur, times, dist_per_point, s, distance, speed, dur_s, angle = \
        [], [], [], [], [], [], [], [], [], [], [], []
    # reset pandas data frame as well as data per track for next loop
    tmp_df = pd.DataFrame(columns=[])

# reove the day value in column and convert to string - that works also with later import to postgre
tracks_sum_pd['tr_duration'] = tracks_sum_pd['tr_duration'].astype(str).map(lambda x:x[7:])
tracks_to_be_imported_pd['tr_duration'] = tracks_to_be_imported_pd['tr_duration'].astype(str).map(lambda x:x[7:])

# add the newly recorded tracks to entire csv file and include the index as separate column
tracks_sum_pd.to_csv(FILE_STATISTICS,index=True,index_label='tr_id')

# add the newly recorded tracks from today to own file
tracks_to_be_imported_pd.to_csv('tracks_to_be_imported.csv',index=True,index_label='tr_id')

