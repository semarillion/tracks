from dtaidistance import dtw_ndim
import numpy as np
import matplotlib.pyplot as plt

np.set_printoptions(linewidth=1100)

series1 = np.array([[0,0],  # first 2-dim point at t=0
                    [1, 1],  # second 2-dim point at t=1
                    [1, 2],
                    [2, 2],
                    [3, 2],
                    [3,3],
                    [4,3],
                    [5,2],
                    [6,2],
                    [7,1],
                    [8, 1]], dtype=np.double)

series2 = np.array([[1, 0],
                    [2, 1],
                    [2, 2],
                    [3, 3],
                    [4, 2],
                    [5, 2],
                    [5, 1],
                    [6, 1],
                    [7, 0]], dtype=np.double)


series3 = series1+0.1
series3 = np.vstack([series3,[9,0.5]])

dtw_distance_12,dtw_matrix_12 = dtw_ndim.warping_paths(series1,series2)
dtw_distance_13,dtw_matrix_13 = dtw_ndim.warping_paths(series1,series3)
dtw_distance_23,dtw_matrix_23 = dtw_ndim.warping_paths(series2,series3)

dtw_distance_12_n = round(dtw_distance_12/(len(series1)+len(series2)),4)
dtw_distance_13_n = round(dtw_distance_13/(len(series1)+len(series3)),4)
dtw_distance_23_n = round(dtw_distance_23/(len(series2)+len(series3)),4)



plt.figure()
plt.plot(series1[:,0],series1[:,1],c='b',label='series1')
plt.plot(series2[:,0],series2[:,1],c='g',label='series2')
plt.plot(series3[:,0],series3[:,1],c='r',label='series3')
plt.legend(loc='upper left', markerscale=6)

plt.show()
print('dtw_distance_12_n,dtw_distance_13_n,dtw_distance_23_n')
print(dtw_distance_12_n,dtw_distance_13_n,dtw_distance_23_n)

plt.figure()
plt.title('dtw_matrix_13')
plt.imshow(dtw_matrix_13,cmap='cool',interpolation='nearest')
plt.show()

plt.figure()
plt.title('dtw_matrix_23')
plt.imshow(dtw_matrix_23,cmap='cool',interpolation='nearest')
plt.show()

plt.figure()
plt.title('dtw_matrix_12')
plt.imshow(dtw_matrix_12,cmap='cool',interpolation='nearest')
plt.show()