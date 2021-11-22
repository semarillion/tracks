import math
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix

#np.set_printoptions(threshold=sys.maxsize)

# constants
import pandas as pd

R = 6373.0

def f_CalcAngleDeg(point_1,point_2):
    """ calculate the angle between two points, orienation is accorinding to
    https://de.wikipedia.org/wiki/Windrichtung, that means wind from north is 0°, hence a differnet
    calculation needs to be done to calculate the angle between the two given points.

    @param point_1: first way point
    @type point_1: tuple
    @param point_2: second way point
    @type point_2: tuple
    @return: angle in degrees
    @rtype: float """

    xDiff = point_2[1]-point_1[1]
    yDiff= point_2[0]-point_1[0]

    # calculate the angle between two points
    angle = math.degrees(math.atan2(yDiff,xDiff))
    # if angle is negative correct the angle by adding an offset to the absolute value
    if angle < 0:
        angle = 360-abs(angle)

    # return the calculated angle
    return angle

def f_CalWpDistance(point_1,point_2):
    """
    This function calculates the 2d distance between two given points (lateral and logitudinal
    coordinates) taking into account the earth curvature/radius. The distance calculation does not consider
    the current elevation between to two points. The implementation follows the Haversine algorithm.
    A detailed description of the applied algorithm can be found here: https://en.wikipedia.org/wiki/Haversine_formula
    The resolution of the return value is [m]

    @param point_1: first way point
    @type point_1: tuple
    @param point_2: second way point
    @type point_2: tuple
    @return: 2d distance between two points (without considering the elevation difference)
    @rtype: float
    """
    # extract individual values of coordinates, for further calculation the values need to be in radians
    lon1 = math.radians(point_1[0])
    lon2 = math.radians(point_2[0])
    lat1 = math.radians(point_1[1])
    lat2 = math.radians(point_2[1])

    # now apply the haversine algorithm
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c * 1000

    # return the calculated distance
    return distance

def f_closestPoint(pair,multiple):
    """
    This function identifies from two two points of distance, which is closest to the fixed value.
    The fixed value is multiple -> DISTANCE
    @param pair: to distance values
    @type pair: tuple (two values)
    @param multiple: defined distance
    @type multiple: int
    @return: result of which point is closer to DISTANCE
    @rtype: float
    """
    #extract the tuple
    a,b=pair

    # based on the abs difference to a number return either a or b
    if abs(a-multiple) >= abs(b-multiple):
        return b
    else:
        return a

def f_FindValuesCloseToMultiple(list_of_disctances, multiple_of):
    ''' returns a list of TrueFalse which indicate whether distance value a multiple of "multiple_of -> DISTANCE"
        @param list_of_disctances: list of recordes distances from start
        @type list_of_disctances: list
        @param multiple_of: equal to DISTANCE
        @type multiple_of: int
        @return: list where a distance (from start) is very close to a multiple of DISTANCE
        @rtype: list
        '''

    Match=[]                                               # definition of the return value
    multiple=multiple_of                                   # save the initial value of the multiple
    Match_l=[]

    # continue as long the end of the list has not been readched
    while(multiple<=max(list_of_disctances)):
        number=0

        # iterate of the list whith a window of two elements
        for i in range(0, len(list_of_disctances) - 1):
            a,b= list_of_disctances[i:i + 2]

            # if one number is below and the other number is above the multiple
            if a < multiple and b > multiple:
                # check which number of both is closest to the mulitple
                number = f_closestPoint((a,b),multiple)
            else:
                continue

        # append the found distance (from start) to a list
        Match.append(number)

        # and update the number for the next cycle
        multiple+=multiple_of

    # create list where 1 indicates a multiple was found
    for i in list_of_disctances:
        if i in Match:
            Match_l.append(1)
        else:
            Match_l.append(0)
    Match_l[0]=1    # first ohne needs to be used allways

    return Match_l   # return the list of numbers which are close the the multiple

def f_makeQuadrant(X,bins,no_of_Tracks):
    DIM=8
    cluster_np = np.empty((0, 1))
    cluster=np.array([0,0])
    tracks=[]

    # calcuate the min and max values out of the tracks
    lat_min = X[:,1].min()
    lat_max = X[:,1].max()
    lon_min = X[:,0].min()
    lon_max = X[:,0].max()

    # calculate the delta assuming an DIM clustering
    lat_delta = (lat_max-lat_min)/DIM
    lon_delta = (lon_max-lon_min)/DIM

    # make a list of center points for lat, means, the caluclated point is the center of each quadrant
    lat_center_cluster = [lat_min+lat_delta*f for f in range(1,DIM,2)]
    lat_center_cluster.sort(reverse=True)

    # make a list of center points for lon, means, the caluclated point is the center of each quadrant
    lon_center_cluster = [lon_min+lon_delta*f for f in range(1,DIM,2)]


    plt.figure()
    # build now from lat and lon (all combination) the center point of each quadrant
    for lat in lat_center_cluster:
        for lon in lon_center_cluster:
            plt.scatter(lon,lat,c='b')
            newrow = [lon,lat]
            cluster = np.vstack([cluster,newrow])


    plt.scatter(X[:, 0], X[:, 1], c='r',linewidths=0.01)
    plt.grid(visible=True,which='both')
    x_ticks = [lon_min+lon_delta*f for f in range(0,DIM+1)]
    y_ticks = [lat_min+lat_delta*f for f in range(0,DIM+1)]
    plt.xticks(x_ticks)
    plt.yticks((y_ticks))
    plt.show()


    cluster = np.delete(cluster,axis=0,obj=0)       # first line needs to be deleted because it was introduced to
                                                    # enable the vstack functions which expects an non-empty array
                                                    # !!! to be improved !!!

    # iterate now over all lon and lat values
    for x in X:
        # In the following we calculate the distance from each waypoint to the centers of all clusters.
        # The cluster number which has the shortest distance to the waypoint is stored in a numpy array
        cluster_np = np.append(cluster_np,np.array([[distance_matrix([x],cluster).argmin()]]),axis=0)

    # The numpy array of the waypoint is now extended by the information of the corresponding clusters
    X = np.append(X,cluster_np,axis=1)

    # The list that is created now contains an indicator that shows which track each point belongs to.
    # This is then added to the numpy array X.
    for i in range(1, len(bins)):
        no_wp = bins[i] - bins[i - 1]
        tracks += [i - 1] * no_wp

    # convert the list to 2d numpy array
    tracks_np = np.array(tracks).reshape(len(tracks),1)

    # now add the track information to the existing numpy array
    X = np.c_[X,tracks_np]

    for cl in range(0,DIM*2):
        X_cl = X[X[:,2]==cl]
        print(X_cl)




if __name__ == '__main__':
    #print(f_CalcAngleDeg((0,0),(1,1)))
    #print(f_CalWpDistance((10.055605, 48.835271),(10.056681, 48.835347)))

    # check f_makeQuadrant(X,bins,no_of_Tracks)
    os.chdir("C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap")
    X= np.genfromtxt('X.csv',delimiter=',')
    N0_TRACKS = 4
    bins = [0, 609, 1347, 1745, 2145]
    X=f_makeQuadrant(X,bins,no_of_Tracks=N0_TRACKS)
