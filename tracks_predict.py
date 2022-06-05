import pandas as pd
import os
from collections import deque

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

FILE_PATH_GPX = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap'
FILE_PATH_CSV = 'C:\\Users\\arwe4\\OX Drive (2)\\My files\\gpx\\overlap\\csv'

os.chdir(FILE_PATH_CSV)

values = deque([-1,-0.5,0,0.5,1,0.5,0,-0.5])
wd_l = ['N','NO','O','SO','S','SW','W','NW']
wd_values_dict={}

for i,wd in enumerate(wd_l):
    if i==0:
        wd_values_dict.update({wd: list(values)})
    else:
        values.rotate(1)
        wd_values_dict.update({wd:list(values)})

wd_values_pd = pd.DataFrame(wd_values_dict,index=wd_l)



#ädf = pd.read_csv('2018-07-22_48062803_Aalen - Affalteried - Waiblingen (GUZ).gpx.csv')