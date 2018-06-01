"""
file_address = 'C:/Users/dong87/Documents/ML_data/all_data/data_600.csv'
"""

from __future__ import division
import pandas as pd
from sklearn.cluster import AffinityPropagation
from sklearn import cluster, datasets
from sklearn.cluster import DBSCAN
import csv
import numpy as np
from numpy import genfromtxt
import scipy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
import pylab
"""
row:   0{i mod(3) == o}               1               2
name:  FtW IL [dB]                    Peak WL [nm]    FtW 1dB BW [nm]
"""
file_address_630 = 'C:/Users/dong87/Documents/ML_data/all_data/data_630.csv'
data_630 = genfromtxt(file_address_630, delimiter=',')
file_address_626 = 'C:/Users/dong87/Documents/ML_data/all_data/data_626.csv'
data_626 = genfromtxt(file_address_626, delimiter=',')
file_address_all = 'C:/Users/dong87/Documents/ML_data/all_data/all_data.csv'
data_3para_all = genfromtxt(file_address_all, delimiter=',')
file_address_489 = 'C:/Users/dong87/Documents/ML_data/all_data/data_489.csv'
data_489 = genfromtxt(file_address_489, delimiter=',')
data_630 = data_630[~(data_630==0).all(1)]
data_626 = data_626[~(data_626==0).all(1)]
data_489 = data_489[~(data_489==0).all(1)]
print('626 data has shape %s'%[np.shape(data_626)])
print('630 data has shape %s'%[np.shape(data_630)])
(row, col) = np.shape(data_3para_all)

"""
apply 3-sigma filter
"""
sigma_IL = np.std(data_626, 0)
mean_IL = np.mean(data_626, 0)
rsd = np.zeros(np.shape(sigma_IL))
for i in range(3):
    rsd[i] = sigma_IL[i]/mean_IL[i]
print(rsd) 
    

print(mean_IL - 2 * sigma_IL, mean_IL + 2*sigma_IL)
IL_good = np.zeros((row, 1))
Peak_good = np.zeros((row, 1))
Ftw_good = np.zeros((row, 1)) 
all_good = np.zeros((row, np.shape(data_3para_all)[1]))
n_sigma = 3 # n sigma
for i in range(row):
    if data_3para_all[i, 0] > mean_IL[0] - n_sigma * sigma_IL[0] and data_3para_all[i, 0] < mean_IL[0] + n_sigma * sigma_IL[0]:
        IL_good[i,0] = data_3para_all[i, 0]
    if data_3para_all[i, 1] > mean_IL[1] - n_sigma * sigma_IL[1] and data_3para_all[i, 1] < mean_IL[1] + n_sigma * sigma_IL[1]:
        Peak_good[i, 0] = data_3para_all[i, 1]
    if data_3para_all[i, 2] > mean_IL[2] - n_sigma * sigma_IL[2] and data_3para_all[i, 2] < mean_IL[1] + n_sigma * sigma_IL[2]:
        Peak_good[i, 0] = data_3para_all[i, 2]
IL_good = IL_good[~(IL_good==0).all(1)]
Peak_good = Peak_good[~(Peak_good==0).all(1)]
Ftw_good = Ftw_good[~(Ftw_good==0).all(1)]
for i in range(row):
    if (data_3para_all[i, 0] > mean_IL[0] - 2 * sigma_IL[0] and data_3para_all[i, 0] < mean_IL[0] + 2 * sigma_IL[0] and 
        data_3para_all[i, 1] > mean_IL[1] - 2 * sigma_IL[1] and data_3para_all[i, 1] < mean_IL[1] + 2 * sigma_IL[1] and 
        data_3para_all[i, 2] > mean_IL[2] - 2 * sigma_IL[2] and data_3para_all[i, 2] < mean_IL[1] + 2 * sigma_IL[2]):
        all_good[i,:] = data_3para_all[i, :]
all_good = all_good[~(all_good==0).all(1)]
size_all_good = np.shape(all_good)
print('The shape of data falling into 3-sigma is %s'%[np.shape(all_good)])

"""
apply DBSCAN on 626 + 630
"""
data_626_630 = np.zeros((np.shape(data_626)[0] + np.shape(data_630)[0], np.shape(data_630)[1]))
print(np.shape(data_626_630))
for i in range (np.shape(data_626)[0]):
    data_626_630[i, :] = data_626[i, :]
for i in range(np.shape(data_626)[0], np.shape(data_626)[0] + np.shape(data_630)[0]):
    data_626_630[i, :] = data_630[i - np.shape(data_626)[0] , :]





"""
add weight
"""
    
weight_IL = 10
weight_BW = 10
weight_WL = 1
data_630_626_weighted = np.zeros(np.shape(data_626_630))
for i in range (np.shape(data_626_630)[0]): 
    data_630_626_weighted[i, 0] = data_626_630[i, 0]*weight_IL
    data_630_626_weighted[i, 1] = data_626_630[i, 1]*weight_WL
    data_630_626_weighted[i, 2] = data_626_630[i, 2]*weight_BW

data_all_good_weighted = np.zeros(np.shape(all_good))
for i in range (np.shape(all_good)[0]): 
    data_all_good_weighted[i, 0] = all_good[i, 0]*weight_IL
    data_all_good_weighted[i, 1] = all_good[i, 1]*weight_WL
    data_all_good_weighted[i, 2] = all_good[i, 2]*weight_BW
    
    
    
X = data_630_626_weighted     
    
    
x_FGC = X


eps = 10
min_samples = 100
db = DBSCAN(eps= eps, min_samples=min_samples).fit(x_FGC) 
core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
core_samples_mask[db.core_sample_indices_] = True
FGCdata_all_labels = db.labels_
size_FGCdata_all_labels = np.shape(FGCdata_all_labels)[0]
n_clusters_ = len(set(FGCdata_all_labels)) - (1 if -1 in FGCdata_all_labels else 0)

#X_withlb = np.zeros((np.shape(X)[0], np.shape(X)[1] + 1))

for i in range(size_FGCdata_all_labels):
    if FGCdata_all_labels[i] == -1:
        x_FGC[i, :] = np.zeros((1,3)) 
x_FGC = x_FGC[~(x_FGC==0).all(1)]         



print ('total %d clusters'%n_clusters_)



count_1 = 0

for i in range(np.shape(all_good)[0]):
    for j in range(np.shape(data_626_630)[0]):
        if (data_626_630[j, 0] == all_good[i, 0] and 
            data_626_630[j, 1] == all_good[i, 1] and 
            data_626_630[j, 2] == all_good[i, 2]):
            count_1 += 1 
print ('%d points in total match between DBSCAN and 3-sigma'%count_1)
count_2 = 0
for i in range(np.shape(data_626_630)[0]):
    if FGCdata_all_labels[i] == 0:
        count_2 += 1
print('%d points in DBSCAN total'%count_2)
print('%d points in 3-sigma'%np.shape(all_good)[0])

count_3 = count_1/count_2
count_4 = count_1/np.shape(all_good)[0]
print('%5.3f  accuracy (match data/DBSCAN data)'%count_3)
print('%5.3f  recall (match data/3-sigma data)'%count_4)

"""        
plot
"""
 
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_title('%5.3f recall and %5.3f accuracy with eps=%5.3f and min_sam=%d'%(count_4, count_3, eps, min_samples), fontdict=None, loc='center', y=1.1)
#for c, m in [('r', 'o'), ('b', '^')]:
"""
# define color code in the label
#color label: b: blue, g: green, r: red, c: cyan, m: magenta, y: yellow, k: black, w: white
"""
 
label_color_code = [None]*(size_FGCdata_all_labels)
for i in range (size_FGCdata_all_labels):
    """
#     oringinal color coding
#     if FGCdata_all_labels[i] == 0:
#         label_color_code[i] = 'r'
#     if FGCdata_all_labels[i] == 1:
#         label_color_code[i] = 'b'   
#     if FGCdata_all_labels[i] == 2:
#         label_color_code[i] = 'g' 
#     if FGCdata_all_labels[i] == 3:
#         label_color_code[i] = 'y'
#     if FGCdata_all_labels[i] == 4:
#         label_color_code[i] = 'c'
#     if FGCdata_all_labels[i] == 5:
#         label_color_code[i] = 'm'
#     if FGCdata_all_labels[i] == -1:
#         label_color_code[i] = 'k'
"""
    if FGCdata_all_labels[i] == 0:
        label_color_code[i] = 'r'
    if FGCdata_all_labels[i] == 1:
        label_color_code[i] = 'k'   
    if FGCdata_all_labels[i] == 2:
        label_color_code[i] = 'k' 
    if FGCdata_all_labels[i] == -1:
        label_color_code[i] = 'k' 
for i in range (size_FGCdata_all_labels):
    xs = data_630_626_weighted[i,0]
    ys = data_630_626_weighted[i,1]
    zs = data_630_626_weighted[i,2]
    c = label_color_code[i]
    ax.scatter(xs, ys, zs, c=c)
    
for i in range (size_all_good[0]):
    xs = data_all_good_weighted[i,0]
    ys = data_all_good_weighted[i,1]
    zs = data_all_good_weighted[i,2]
    c = label_color_code[i]
    ax.scatter(xs, ys, zs, c='m')
ax.set_xlim3d(-7*weight_IL,-2*weight_IL)
ax.set_ylim3d(1550*weight_WL, 1580*weight_WL)
#ax.set_zlim3d(-60*weight_BW,60*weight_BW)

ax.set_xlabel('IL')
ax.set_ylabel('Peak WL')
ax.set_zlabel('1dB BW')

red_patch = mpatches.Patch(color='r', label='Good Data form DBSCAN')
m_patch = mpatches.Patch(color='m', label='Good Data form 3-sigma')
black_patch = mpatches.Patch(color='k', label='other group')
plt.legend(bbox_to_anchor=(0.65, 1), loc=2, borderaxespad=0., handles=[m_patch, red_patch, black_patch])
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('3-sigma', fontdict=None, loc='center')
#for c, m in [('r', 'o'), ('b', '^')]:
"""
# define color code in the label
#color label: b: blue, g: green, r: red, c: cyan, m: magenta, y: yellow, k: black, w: white
"""
 
# label_color_code = [None]*(size_FGCdata_all_labels)
# for i in range (size_FGCdata_all_labels):
#     if FGCdata_all_labels[i] == 0:
#         label_color_code[i] = 'r'
#     if FGCdata_all_labels[i] == 1:
#         label_color_code[i] = 'b'   
#     if FGCdata_all_labels[i] == 2:
#         label_color_code[i] = 'g' 
#     if FGCdata_all_labels[i] == 3:
#         label_color_code[i] = 'y'
#     if FGCdata_all_labels[i] == 4:
#         label_color_code[i] = 'c'
#     if FGCdata_all_labels[i] == 5:
#         label_color_code[i] = 'm'
#     if FGCdata_all_labels[i] == -1:
#         label_color_code[i] = 'k'
# for i in range (size_all_good[0]):
#     xs = data_all_good_weighted[i,0]
#     ys = data_all_good_weighted[i,1]
#     zs = data_all_good_weighted[i,2]
#     c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='m')
# ax.set_xlim3d(-60,-25)
# ax.set_ylim3d(1600,1580)
# ax.set_zlim3d(-100,70)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')
# ax.set_zlabel('1dB BW')
plt.show()

