import gpxpy
import gpxpy.gpx
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pylab import figure
from datetime import timedelta
from statistics import mean
from itertools import permutations
from tracks_aux import f_CalcAngleDeg

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

SPEED_THRESH=2

# store the intermediate results in lists
lat=[]
lon=[]
elev=[]
sp=[]
times=[]
speed=[]
points=[]
dist_per_point=[]
distance=[]
cum_elevation=[]
speed_filt=[]
dur=[]
dur_s=[]
angle=[]

# pandas dataframe for storing all lists
points_df=pd.DataFrame(columns=[])

# Parsing an existing file:
# -------------------------
#track_name='2021-04-28_357176050_4 Hügel-Tour'
track_name='2021-07-20_425763376_Aalen - Jagstzell - Bopfingen - 100km'
#gpx_file = open('Fahrrad_Tour_zur_Burg_Katzenstein.gpx', 'r')
#gpx_file = open('2021-07-03_409058828_Von Aalen nach Mantelhof.gpx')
#gpx_file = open('2021-06-26_401888588_Südtour über Wental.gpx')
#gpx_file = open('2021-05-09_364455285_Rennrad Tour 60_1000.gpx')
gpx_file = open(track_name+'.gpx')
gpx = gpxpy.parse(gpx_file)

# loop of gpx file and each entry
for track in gpx.tracks:
    for segment in track.segments:

        # read each point with data of lateral, longitudinal, elevation and time
        for point_nr,point in enumerate(segment.points):
            points.append(point)
            lat.append(point.latitude)
            lon.append(point.longitude)
            elev.append(point.elevation)
            times.append(point.time.time())

            # init values for the beginning - set all values to zero
            if point_nr==0:
                speed.append(0)
                dist_per_point.append(0)
                distance.append(0)
                cum_elevation.append(0)
                speed_filt.append(0)
                dur.append(0)
                dur_s.append('00:00:00')
                angle.append(0)
            else:
                speed.append(point.speed_between(segment.points[point_nr-1]))           # speed between way points
                dist_per_point.append(point.distance_3d(segment.points[point_nr-1]))    # distance between wasy points
                distance.append(sum(dist_per_point))                                    # distance from start to qay point

                # calculate the duration from start to current point_nr
                dur.append( timedelta(hours=times[point_nr].hour,
                                      minutes=times[point_nr].minute,
                                      seconds=times[point_nr].second) -

                            timedelta(hours=times[0].hour,
                                      minutes=times[0].minute,
                                      seconds=times[0].second) )

                p_cur = (points[point_nr].longitude,points[point_nr].latitude)
                p_old =(points[point_nr-1].longitude,points[point_nr-1].latitude)

                angle.append(f_CalcAngleDeg(p_cur,p_old))


                # filter speed and store it in list
                last_speed_filt = speed_filt[-1]
                if (speed[point_nr]-last_speed_filt) > SPEED_THRESH:
                    speed_filt.append((last_speed_filt+last_speed_filt+SPEED_THRESH)/2)
                elif (last_speed_filt-speed[point_nr]) > SPEED_THRESH:
                    speed_filt.append((last_speed_filt+(last_speed_filt-SPEED_THRESH))/2)
                else:
                    speed_filt.append((last_speed_filt+speed[point_nr])/2)

                # check whether hight has increased
                if point.elevation > segment.points[point_nr-1].elevation:

                    # calculate the increas between the last two way points
                    inc=point.elevation - segment.points[point_nr - 1].elevation

                    # get the last value
                    last_value=cum_elevation[-1]

                    # add increase of hight plus the reached hight at that waypoint
                    cum_elevation.append(last_value+inc)


                else:
                    # get the last element and maintain it
                    cum_height=cum_elevation[-1]
                    cum_elevation.append(cum_height)

            dur_s=[str(s) for s in dur]


max_h_idx=elev.index(max(elev))
min_h_idx=elev.index(min(elev))

max_v_idx=speed_filt.index(max(speed_filt))

points_df['lateral']=lat
points_df['longitudinal']=lon
points_df['elevation [m]']=elev
points_df['cum_elevation [m]']=cum_elevation
points_df['times [h/m/s]']=times
points_df['duration [s]']=dur
points_df['speed [km/h]']=[s*3.6 for s in speed]
points_df['filt speed [km/h]']=[s*3.6 for s in speed_filt]
points_df['distance betweeen points [m]']=dist_per_point
points_df['distance from start [m]']=distance
points_df['angle']=angle



# display track in 3D
fig = figure(0)
ax = Axes3D(fig)
ax.set_xlabel('lon [°]')
ax.set_ylabel('lat [°]')
ax.set_zlabel('hight [m]')
ax.text(mean(lon),mean(lat), max(elev)+50, track_name, color='red')

ax.text(lon[0],lat[0],elev[0],'start')
ax.text(lon[-1],lat[-1],elev[-1],'end')

ax.scatter(lon[max_h_idx],lat[max_h_idx],elev[max_h_idx],c='r')
ax.text(lon[max_h_idx],lat[max_h_idx],elev[max_h_idx],'%s' %('highest point [m]: '+str(round(elev[max_h_idx],1))))

ax.scatter(lon[min_h_idx],lat[min_h_idx],elev[min_h_idx],c='g')
ax.text(lon[min_h_idx],lat[min_h_idx],elev[min_h_idx],'%s' %('lowest point [m]: '+str(round(elev[min_h_idx],1))))

ax.scatter(lon[max_v_idx],lat[max_v_idx],elev[max_v_idx],c='blue')
ax.text(lon[max_v_idx],lat[max_v_idx],elev[max_v_idx],'%s' %('highest speed [km/h]: '+str(round(speed_filt[max_v_idx]*3.6,1))))

ax.set_zlim(min(elev),max(elev)+50)
ax.plot(lon,lat,elev,c='black')


plt.figure(1)
plt.plot(dur_s,points_df['filt speed [km/h]'])
plt.plot(dur_s,points_df['speed [km/h]'])
plt.plot(dur_s,points_df['elevation [m]'])
plt.plot(dur_s,points_df['cum_elevation [m]'])
plt.xticks(dur_s[::50],rotation=45)
plt.grid(True)
plt.show()

plt.figure(2)
plt.title('original tracks')
plt.ylabel('lateral')
plt.xlabel('longitudinal')
plt.scatter(lon, lat, c='red', s=2)
#plt.legend(loc='upper left', markerscale=6)
plt.show()
