import datetime
from weatherapi.weatherapi_client import WeatherapiClient

def f_Init_wheather_api():
    key = 'a3f05e0ceb88477e86793853221306'
    client = WeatherapiClient(key)
    return client.ap_is

def f_get_wheather_data(lon,lat,dt,hour):
    w_api = f_Init_wheather_api()

    coor = str(lat) +',' + str(lon)

    result = w_api.get_history_weather(q=coor,dt=dt,hour=hour)
    return result

#result = ap_is_controller.get_realtime_weather(q, lang)

if __name__ == '__main__':
    lon = 9.65029595654768
    lat = 30.349699592604523

    dt = datetime.date(2022,6,18)
    hour = 12

    data = f_get_wheather_data(lon = lon, lat=lat,dt=dt,hour=hour)