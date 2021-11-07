import math

# constants
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



if __name__ == '__main__':
    #print(f_CalcAngleDeg((0,0),(1,1)))
    print(f_CalWpDistance((10.055605, 48.835271),(10.056681, 48.835347)))