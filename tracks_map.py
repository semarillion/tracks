import gpxpy
import gpxpy.gpx
import folium

gpx_file = open('2021-04-28_357176050_4 Hügel-Tour.gpx', 'r')

gpx = gpxpy.parse(gpx_file)
points = []
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            points.append(tuple([point.latitude, point.longitude]))
print(points)
ave_lat = sum(p[0] for p in points)/len(points)
ave_lon = sum(p[1] for p in points)/len(points)



#add a markers
#for each in points:
#    folium.Marker(each).add_to(my_map)
marker_start = points[0]
marker_end = points[-1]

# Load map centred on average coordinates
my_map = folium.Map(location=[ave_lat, ave_lon], zoom_start=14,tiles='Stamen Terrain')
folium.Marker(location=marker_start,
              icon=folium.Icon(color='green',icon='plus')).add_to(my_map)
folium.Marker(location=marker_end,
              icon=folium.Icon(color='red',icon='plus')).add_to(my_map)
folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(my_map)


my_map.save("./gpx_berlin_withmarker.png")


