import datetime
import sys
import gpxpy.gpx
import pandas as pd
from datetime import timedelta
import os
from tracks_aux import f_CalcAngleDeg,f_FindValuesCloseToMultiple,f_CalWpDistance
from  sqlalchemy import create_engine
import psycopg2
import re
from psycopg2 import Error


# define some dictionary
track_dict = {}                     # ..for entire data of track
statistics_dict = {}
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
SECONDS_PER_HOUR =3600

# file paths's
FILE_PATH_GPX = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap'
FILE_PATH_CSV = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap\\csv'
FILE_STATISTICS = 'all_track_statistics.csv'
FILE_TO_IMPORT = 'tracks_to_be_imported.csv'

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
cur_elevation = []
sp_all=[]
angle_bins = [0]

connect_string = 'postgresql://postgres: arWF,GInO@localhost:5432/bicycle'

# start section local functions ----------------------------------------------------------------------------------------

def f_track_kind(f):
    ''' This function checks whether an cravel bike or a race bike was used
    Tracks with a CB are marked in the file name, the other ones are done with a race bike
    @:return string (CB = cravel bike, RB = race bike)
    @:param f: filename which has the CB characters in the file name'''
    if '_CB' in f:
        return  'CB'
    elif '_MTB' in f:
        return  'MTB'
    else:
        return 'RR'


def f_postgre_connect(constring):
    ''' this function creates a connecton for sql alchemy lib (engine) and the psycopg2 and returns the
        connections for later usage
        @:param: constring: connections string with credentials
        @:returns c1: connection via sqlalchemy, c2: connection via psycopg2'''

    # establish connection for sqlalchemy
    c1 = create_engine(constring).connect()
    # establish connecton for psycopg2
    c2 = psycopg2.connect(constring)
    # enable autocommit
    c2.autocommit = True
    # and return the connections for later usage
    return c1,c2

def f_get_last_id(db,id):
    ''' This funciton returns the last index of a table. This is need because
    the following records are appended
    @:return id: last index '''

    # define SQL command to get the last id of the table
    max_track_id_sql = "SELECT MAX("+id+") FROM "+db
    # execute the SQL command
    id = pd.read_sql(max_track_id_sql, con=conn_psycopg2)['max'][0]
    # and return the last index found in the database
    return id


def f_Calc_id_range():
    ''' This function returns the range of indices, which need to be considered later in the data frame
        to be written in the data base
        the id starts counting from 0
        @:return: idx_range: list of values which will be mapped later as track_id '''

    # get the last index of the data base
    idx_last = f_get_last_id('statistics','track_id')

    # depending on an empty feedback the start value need to be calculated
    if not idx_last:
        # empty database -> hence id starts from 0
        idx_start = 0
    else:
        # records in db, hence start with the last value plus 1
        idx_start = idx_last+1

    # calculate range of new id's
    idx_range = list(range(idx_start,idx_start+ len(f_list)))

    # and return as list
    return idx_range


def f_angel_to_bin():
    for i in range(0, 360, 45):
        angle_bins.append(i + 22.5)
    # loop does not include the last value, hence it is added at a last step
    angle_bins.append(360.0)


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
            gradient_wp.append(0.0)
            time_delta_wp.append(0)
            speed_wp.append(0)
        else:
            # get the coordinates from current point and point before and calculate the distance as well as angel
            # between the two way points
            p1 = tuple(tmp_df.loc[idx, 'lon':'lat'])
            p0 = tuple(tmp_df.loc[idx - 1, 'lon':'lat'])
            # add the calculated angle to list
            angle.append(f_CalcAngleDeg(p0, p1))
            dist_wp.append(f_CalWpDistance(p0,p1))

            # calculate the difference of elevation between two way points
            delta = tmp_df.loc[idx,'elevation_wp'] - tmp_df.loc[idx-1,'elevation_wp']
            elevation_wp.append(round(delta,1))

            # calculate th gradient between two way points
            delta = (elevation_wp[-1]/dist_wp[-1])*100
            gradient_wp.append( round(delta,2) )

            # calculate the time difference between two waypoints
            h1 = tmp_df.loc[idx, 'times_wp'].hour
            m1 = tmp_df.loc[idx, 'times_wp'].minute
            s1 = tmp_df.loc[idx, 'times_wp'].second
            t1 = timedelta(hours=h1,minutes=m1,seconds=s1)
            h0 = tmp_df.loc[idx-1, 'times_wp'].hour
            m0 = tmp_df.loc[idx-1, 'times_wp'].minute
            s0 = tmp_df.loc[idx-1, 'times_wp'].second
            t0 = timedelta(hours=h0, minutes=m0, seconds=s0)
            time_delta_wp.append((t1-t0).total_seconds())

            # calculate the average speed between two waypoints
            speed_wp.append(round((dist_wp[-1]/time_delta_wp[-1]*3.6),1 ))


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

f_angel_to_bin()

# get list of available gpx files on local drive and output them on console
f_list=[file for file in os.listdir() if '.gpx' in file]#
print('\nfound tracks on local computer..')
print(*f_list,sep='\n')

#establish connection to data base
conn_sqlal,conn_psycopg2 = f_postgre_connect(connect_string)

tmp_l=[]
for track in f_list:
    sql = 'SELECT tr_name FROM statistics WHERE tr_name in (\''+track+'\')'
    if pd.read_sql(sql, con=conn_psycopg2)['tr_name'].any() == False:
        tmp_l.append(track)

    else:
        continue

if not tmp_l:
    print('\n\nTracks alread in db - nothing to import')
    sys.exit()
else:
    f_list = tmp_l.copy()
    print('\n\nTracks to be imported..')
    print(*f_list, sep='\n')

# start reading files from disk to import to data base
print('\nreading files...')
for no,f in enumerate(f_list):
    print('\n',f)
    gpx_file = open(f)
    gpx = gpxpy.parse(gpx_file)

    # now iterate over the entire track data and extract multiple information
    for track in gpx.tracks:
        for segment in track.segments:

            # read each point with data of lateral, longitudinal, elevation and time
            for point_nr, point in enumerate(segment.points):
                points.append(point)
                lat.append(point.latitude)
                lon.append(point.longitude)
                elev.append(point.elevation)
                cur_elevation.append(round(point.elevation,0))
                times.append(point.time.time())

                # init values for the beginning - set all values to zero
                if point_nr == 0:
                    dist_per_point.append(0)
                    distance.append(0)
                    cum_elevation.append(0)
                    dur.append(datetime.time(0,0,0))
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
    tmp_df['lon'] = lon
    tmp_df['lat'] = lat
    tmp_df['cur_elevation'] = cur_elevation
    tmp_df['elevation_wp'] = elev
    tmp_df['cum_elevation'] = cum_elevation
    tmp_df['times_wp'] = times
    tmp_df['dt_duration_wp'] = dur
    tmp_df['distance_from_start_m'] = distance

    # now generate a column in pandas data frame which indicates a mulitiple of DISTANCE (just to reduce the data)
    # e.g. a 1 indicates that it is a multiple of DISTANCE
    tmp_df['match multiple'] = f_FindValuesCloseToMultiple(tmp_df['distance_from_start_m'].tolist(), DISTANCE)
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
    tmp_df['speed_wp_km']=f_CalculateData(tmp_df)

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
    # drop also lines where the wp_speed is calculated as Nan due to the fact that a break of the trip
    # leads to a division by 0 which leads at the end to NaN, hence these lines are dropped
    tmp_df.dropna(axis=0, how='any',inplace=True)

    # change now to target folder to store csv
    #os.chdir(FILE_PATH_CSV)
    # write the current pandas dataframe of track x to csv
    #print('write track to csv..',end='')
    #tmp_df.to_csv(f+'.csv',index=None)
    print('done..')
    # and change back to gpx folder
    #os.chdir(FILE_PATH_GPX)

    # track statistics --------------------------------------------------------------------------------------------
    # make some statistics for the track summary
    tr_name = f
    tr_kind = f_track_kind(f)
    tr_cum_eval = int(round( float(tmp_df.tail(1)['cum_elevation'])))
    tr_highest_point = tmp_df['cur_elevation'].max()
    tr_lowest_point = tmp_df['cur_elevation'].min()
    tr_duration = tmp_df.tail(1)['dt_duration_wp'].any()
    tr_distance = round(float(tmp_df.tail(1)['distance_from_start_m'])/1000,1)
    tr_gradient = round((tr_cum_eval/tr_distance*100)/1000,3)
    tr_max_speed = round(tmp_df['speed_wp_km'].max(),1)
    tr_average_speed = round((tr_distance)/(tr_duration.seconds/SECONDS_PER_HOUR),1)
    tr_import_date_time = datetime.datetime.now().strftime("%Y-%m-%d")
    tr_date = re.match('\d{4}-\d{2}-\d{2}',f)[0]

    # make new row for pandas dataframe with values calculated above
    new_row = {'tr_name':f,
               'tr_kind':tr_kind,
               'tr_cum_eval':tr_cum_eval,
               'tr_highest_point':tr_highest_point,
               'tr_lowest_point':tr_lowest_point,
               'tr_duration':tr_duration,
               'tr_distance':tr_distance,
               'tr_gradient':tr_gradient,
               'tr_max_speed': tr_max_speed,
               'tr_average_speed':tr_average_speed,
               'tr_import_datetime':tr_import_date_time,
               'tr_date':tr_date}


    # tracks_sum_pd contains the previously read tracks, also from older imports, so new ones are appended to the back
    tracks_sum_pd= tracks_sum_pd.append(new_row, ignore_index=True)

    # copy detailed track info to dictionary (each value of dictionary helds the data of each track)
    track_dict.update({no: tmp_df})

    # reset all lists for next loop
    lat, lon, elev, cur_elevation, cum_elevation, dur, times, dist_per_point, s, distance, speed, dur_s, angle = \
        [], [], [], [], [], [], [], [], [], [], [], [], []
    # reset pandas data frame as well as data per track for next loop
    tmp_df = pd.DataFrame(columns=[])

# reorder the columns
tracks_sum_pd = tracks_sum_pd[
         [ 'tr_kind','tr_date','tr_distance', 'tr_duration', 'tr_average_speed', 'tr_max_speed', 'tr_lowest_point',
           'tr_highest_point','tr_cum_eval', 'tr_gradient', 'tr_import_datetime', 'tr_name']]

# remove the day value in column and convert to string - that works also with later import to postgre
tracks_sum_pd['tr_duration'] = tracks_sum_pd['tr_duration'].astype(str).map(lambda x:x[7:])
# tracks_to_be_imported_pd['tr_duration'] = tracks_to_be_imported_pd['tr_duration'].astype(str).map(lambda x:x[7:])

# calc the new id range, based on the latest value of the track_id and the amount tracks to be appended
track_id_range_l = f_Calc_id_range()

# add the track_id to dataframe of statistics
tracks_sum_pd['track_id']=track_id_range_l
# and write the dataframe to database
tracks_sum_pd.to_sql('statistics',con = conn_sqlal,index=False,if_exists='append')

# now update the data frames with way points for each individual track with way_point id and track_id
for i in range(0,len(f_list)):
    # here, the individial index for each way point is calculated based on the way points which are
    # already in the data base
    if not f_get_last_id(db='way_points',id='way_point_id'):
        # if the table does not have any record start with 0
        start_idx = 0
    else:
        # if there are way points in the table take the index of the last one plus 1
        start_idx = 1 + f_get_last_id(db='way_points',id='way_point_id')
    # calculate foreign key (track_id)
    track_dict[i]['track_id'] = track_id_range_l[i]
    # calculate the the individual way point id, based on the previous track and the lenght of the current track
    track_dict[i]['way_point_id'] = list(range(start_idx, start_idx+len(track_dict[i])))
    # append the data to the database
    track_dict[i].to_sql('way_points', con=conn_sqlal, index=False, if_exists='append')