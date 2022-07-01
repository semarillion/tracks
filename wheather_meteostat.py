# Import Meteostat library and dependencies
from datetime import datetime
from meteostat import Hourly, Point


def f_get_wheather_data(hour,date,lon,lat):
    y = date.year
    m = date.month
    d = date.day
    start_datetime = datetime(y,m,d,0,0)
    end_datetime = datetime(y,m,d,23,59)

    hour_idx = str(datetime(y,m,d,hour,0,0))
    #print(hour_idx)


    # Get hourly data
    p = Point(lat,lon)
    data = Hourly(p, start=start_datetime, end=end_datetime)
    data_day = data.fetch()

    data_hour = data_day.loc[hour_idx,:]

    return data_hour



if __name__ == '__main__':
    h=15
    date = datetime(2022,1,20,15,37)
    lon = 10.404413457671106
    lat = 47.51555393850937


    a = f_get_wheather_data(hour=h,date=date,lon=lon,lat=lat)
