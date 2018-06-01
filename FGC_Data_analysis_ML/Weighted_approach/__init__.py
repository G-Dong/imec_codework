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
from mpl_toolkits.mplot3d import Axes3D
import pylab
"""
row:   0{i mod(3) == o}               1               2
name:  FtW IL [dB]                    Peak WL [nm]    FtW 1dB BW [nm]
"""
file_address = 'C:/Users/dong87/Documents/ML_data/all_data/data_630.csv'
data_630 = genfromtxt(file_address, delimiter=',')

(row_all, col_all) = np.shape(data_630)
X = np.zeros((row_all, col_all - 1))

for i in range(col_all - 1):
    X[:, i] = data_630[:, i]
"""    
"apply affinity propagation"
print(X)
af = AffinityPropagation(preference=-300).fit(X)
cluster_centers_indices = af.cluster_centers_indices_
labels = af.labels_
n_clusters_ = len(cluster_centers_indices)

print (labels)
print('total cluster number is %d'%n_clusters_)

size_labels = np.shape(X)[0]


"apply k-means"
X = all_data_3para


k_means = cluster.KMeans(n_clusters = 2)
k_means.fit(X) 

labels = k_means.labels_[::1]
size_labels = np.shape(labels)[0]

"apply DBSCAN"
"""
"weighted on IL * 10"
weight_IL = 10
weight_BW = 1
weight_WL = 1
data_630_weighted = np.zeros(np.shape(data_630))
for i in range (np.shape(data_630)[0]): 
    data_630_weighted[i, 0] = data_630[i, 0]*weight_IL
    data_630_weighted[i, 1] = data_630[i, 1]*weight_WL
    data_630_weighted[i, 2] = data_630[i, 2]*weight_BW
X = data_630_weighted      

db = DBSCAN(eps= 11, min_samples=800).fit(X) 
"""
eps : float, optional
The maximum distance between two samples for them to be considered as in the same neighborhood.
min_samples : int, optional
The number of samples (or total weight) in a neighborhood for a point to be considered as a core point. This includes the point itself.
, sample_weight = [0.2034, 0.0041, 0.1110], the weight of each sample, NOT features.
"""
core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
core_samples_mask[db.core_sample_indices_] = True
labels = db.labels_

size_labels = np.shape(labels)[0]
"""        
plot
"""
 
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_title('weighted - DBSCAN', fontdict=None, loc='center')
#for c, m in [('r', 'o'), ('b', '^')]:
"""
# define color code in the label
#color label: b: blue, g: green, r: red, c: cyan, m: magenta, y: yellow, k: black, w: white
"""
 
label_color_code = [None]*(size_labels)
for i in range (size_labels):
    if labels[i] == 0:
        label_color_code[i] = 'r'
    if labels[i] == 1:
        label_color_code[i] = 'b'   
    if labels[i] == 2:
        label_color_code[i] = 'g' 
    if labels[i] == 3:
        label_color_code[i] = 'y'
    if labels[i] == 4:
        label_color_code[i] = 'c'
    if labels[i] == 5:
        label_color_code[i] = 'm'
    if labels[i] == -1:
        label_color_code[i] = 'k'
for i in range (size_labels):
    xs = X[i,0]
    ys = X[i,1]
    zs = X[i,2]
    c = label_color_code[i]
    ax.scatter(xs, ys, zs, c=c)
ax.set_xlim3d(-200,100)
ax.set_ylim3d(1520,1620)
ax.set_zlim3d(20,70)
ax.set_xlabel('IL')
ax.set_ylabel('Peak WL')
ax.set_zlabel('1dB BW')
plt.show()