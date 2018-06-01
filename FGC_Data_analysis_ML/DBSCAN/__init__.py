from __future__ import division
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn import svm
from sklearn import cluster, datasets
from sklearn.cluster import DBSCAN
import csv
import numpy as np
from numpy import genfromtxt
import scipy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pylab

all_data = genfromtxt('C:\Users\dong87\Desktop\AI\TrendChart_FGC_edited.csv', delimiter = ',', dtype="|U50")
print ('All data shape is: %s\n'%[np.shape(all_data)])
"""
row:   0{i mod(3) == o}               1               2
name:  FtW IL [dB]                    Peak WL [nm]    FtW 1dB BW [nm]

target value col: V (21 begin with 0)

col: 5, experiment stage name.
        'FGCCTE_FC1DC_626_313' the standard data
        'FGCCTE_FCWFC1DC_630_378' and others: under valuation data. 
"""


"""
all parameters: 
"""
(row_all, col_all) = np.shape(all_data)
target_value = 21
stage_name_col = 3
data_number_each_group = 3
data_3para_all = np.zeros((int(row_all/data_number_each_group), stage_name_col + 1))
data_626 = np.zeros((row_all, data_number_each_group+1))
data_other = np.zeros((row_all, data_number_each_group+1))
data_630 = np.zeros((row_all, data_number_each_group+1))
data_489 = np.zeros((row_all, data_number_each_group+1))
data_500 = np.zeros((row_all, data_number_each_group+1))
data_600 = np.zeros((row_all, data_number_each_group+1))

"""
set 626 as 1 and others are 0
"""
for i in range(row_all):
    if all_data[i, 5] == 'FGCCTE_FC1DC_626_313':
        all_data[i, 5] = 626
    if all_data[i, 5] == 'FGCCTE_FCWFC1DC_630_378':
        all_data[i, 5] = 630
    if all_data[i, 5] == 'FGCOTE_FC1DC_489_245':
        all_data[i, 5] = 489               
    if all_data[i, 5] == 'FGCOTE_FCWFC1DC_500_325':
        all_data[i, 5] = 500 
    if all_data[i, 5] == 'FGCC_FC2DC_600_390':
        all_data[i, 5] = 600 
"""
extract 3 parameters in data_all:
"""
for i in range(row_all):
    data_3para_all[int(i/3), int(i % 3)] = all_data[i, target_value]
    if i % 3 == 0:
        data_3para_all[int(i/3), stage_name_col] = all_data[i, 5]
(row, col) = np.shape(data_3para_all)
print('3 parameter matrix has size: %s with 0~2 columns value and 3 columns refers to stage (626:1, others:0)\n' %[np.shape(data_3para_all)])

"""
find the shape of 626 data and other data
"""
count_626 = 0
count_other = 0
count_630 = 0
count_489 = 0
count_500 = 0
count_600 = 0
for i in range(row):
    if data_3para_all[i, 3] == 626:
        count_626 += 1
    else:
        count_other += 1
    if data_3para_all[i, 3] == 630:
        count_630 += 1
    if data_3para_all[i, 3] == 489:
        count_489 += 1    
    if data_3para_all[i, 3] == 500:
        count_500 += 1  
    if data_3para_all[i, 3] == 600:
        count_600 += 1          
print ('626 stage has %d groups data and other stages have groups %d data\n'%(count_626, count_other))
"""
extract 626 stage data and others
"""
for i in range (row):
    if data_3para_all[i, 3] == 626:
        data_626[i, :] = data_3para_all[i, :]
    else:
        data_other[i, :] = data_3para_all[i, :]
    if data_3para_all[i, 3] == 630:
        data_630[i, :] = data_3para_all[i, :]    
    if data_3para_all[i, 3] == 489:
        data_489[i, :] = data_3para_all[i, :]    
    if data_3para_all[i, 3] == 500:
        data_500[i, :] = data_3para_all[i, :]    
    if data_3para_all[i, 3] == 600:
        data_600[i, :] = data_3para_all[i, :]     
    

"""
delete all 0 rows
"""
data_626 = data_626[~(data_626==0).all(1)]
data_other = data_other[~(data_other==0).all(1)]
data_630 = data_630[~(data_630==0).all(1)]
data_489 = data_489[~(data_489==0).all(1)]
data_500 = data_500[~(data_500==0).all(1)]
data_600 = data_600[~(data_600==0).all(1)]
print(count_other == count_630 + count_489 + count_500 + count_600)
print(np.shape(data_other)[0], np.shape(data_630)[0], np.shape(data_489)[0], np.shape(data_500)[0], np.shape(data_600)[0])

"""
Apply DBSCAN
"""


x_FGC = data_3para_all



db = DBSCAN(eps= 10, min_samples=5).fit(x_FGC) 
core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
core_samples_mask[db.core_sample_indices_] = True
FGCdata_all_labels = db.labels_
for i in range (1000):
    print(FGCdata_all_labels[i])

n_clusters_ = len(set(FGCdata_all_labels)) - (1 if -1 in FGCdata_all_labels else 0)
print ('total %d clusters'%n_clusters_)
count = 0

size_FGCdata_all_labels = np.shape(FGCdata_all_labels)[0]
for i in range(size_FGCdata_all_labels):
    if FGCdata_all_labels[i] == 0:
        count = count + 1
list_class1 = np.zeros((count,1))
count = -1
for i in range(size_FGCdata_all_labels):       
    if FGCdata_all_labels[i] == 0:   
        count = count + 1
        list_class1[count,0] = i

# Black removed and is used for noise instead.

"""        
plot
"""
 
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_title('all data-DBSCAN', fontdict=None, loc='center')
#for c, m in [('r', 'o'), ('b', '^')]:
"""
# define color code in the label
#color label: b: blue, g: green, r: red, c: cyan, m: magenta, y: yellow, k: black, w: white
"""
 
label_color_code = [None]*(size_FGCdata_all_labels)
for i in range (size_FGCdata_all_labels):
    if FGCdata_all_labels[i] == 0:
        label_color_code[i] = 'r'
    if FGCdata_all_labels[i] == 1:
        label_color_code[i] = 'b'   
    if FGCdata_all_labels[i] == 2:
        label_color_code[i] = 'g' 
    if FGCdata_all_labels[i] == 3:
        label_color_code[i] = 'y'
    if FGCdata_all_labels[i] == 4:
        label_color_code[i] = 'c'
    if FGCdata_all_labels[i] == 5:
        label_color_code[i] = 'm'
    if FGCdata_all_labels[i] == -1:
        label_color_code[i] = 'k'
for i in range (size_FGCdata_all_labels):
    xs = data_3para_all[i,0]
    ys = data_3para_all[i,1]
    zs = data_3para_all[i,2]
    c = label_color_code[i]
    ax.scatter(xs, ys, zs, c=c)
ax.set_xlim3d(-25,5)
ax.set_ylim3d(1300,1600)
ax.set_zlim3d(-80,70)
ax.set_xlabel('IL')
ax.set_ylabel('Peak WL')
ax.set_zlabel('1dB BW')


# """
# data_626
# """
# 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('626 data', fontdict=None, loc='center')
# for i in range (count_626):
#     xs = data_626[i,0]
#     ys = data_626[i,1]
#     zs = data_626[i,2]
#     #c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='r')
# 
# ax.set_xlim3d(-25,5)
# ax.set_ylim3d(1300,1600)
# ax.set_zlim3d(-80,60)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')
# ax.set_zlabel('1dB BW')
# """
# data_630
# """
# 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('630 data', fontdict=None, loc='center')
# for i in range (count_630):
#     xs = data_630[i,0]
#     ys = data_630[i,1]
#     zs = data_630[i,2]
#     #c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='b')
# 
# ax.set_xlim3d(-25,5)
# ax.set_ylim3d(1300,1600)
# ax.set_zlim3d(-80,60)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')
# ax.set_zlabel('1dB BW')
# """
# data_489
# """
# 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('489 data', fontdict=None, loc='center')
# temp = data_489
# for i in range (count_489):
#     xs = temp[i,0]
#     ys = temp[i,1]
#     zs = temp[i,2]
#     #c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='g')
# 
# ax.set_xlim3d(-25,5)
# ax.set_ylim3d(1300,1600)
# ax.set_zlim3d(-80,60)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')
# ax.set_zlabel('1dB BW')
# """
# data_500
# """
# 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('500 data', fontdict=None, loc='center')
# temp = data_500
# for i in range (count_500):
#     xs = temp[i,0]
#     ys = temp[i,1]
#     zs = temp[i,2]
#     #c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='y')
# 
# ax.set_xlim3d(-25,5)
# ax.set_ylim3d(1300,1600)
# ax.set_zlim3d(-80,60)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')
# ax.set_zlabel('1dB BW')
# """
# data_600
# """
# 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_title('600 data', fontdict=None, loc='center')
# temp = data_600
# for i in range (count_600):
#     xs = temp[i,0]
#     ys = temp[i,1]
#     zs = temp[i,2]
#     #c = label_color_code[i]
#     ax.scatter(xs, ys, zs, c='c')
# 
# ax.set_xlim3d(-25,5)
# ax.set_ylim3d(1300,1600)
# ax.set_zlim3d(-80,60)
# ax.set_xlabel('IL')
# ax.set_ylabel('Peak WL')

plt.show()
   
        
        
        
        