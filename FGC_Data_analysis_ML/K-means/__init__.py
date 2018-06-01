from __future__ import division
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn import svm
from sklearn import cluster, datasets
import csv
import numpy as np
from numpy import genfromtxt
import scipy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pylab
"""
Parameters we used: 
column:      13(N)          14             15                 16
para_name:   FtW IL         Peak WL[nm]    FtW 1dB BW [nm]    2 sigma noise FGC [dB]

0, 2, 4, ..., 2n, rows are the data from 626_313. 
total row number: 387

160 is a break . two 630_378 together

FGCCTE_FC1DC_626_313
FGCCTE_FCWFC1DC_630_378

"""




FGCdata_all = genfromtxt('C:\Users\dong87\Documents\ML_data\Info_FGC_P151822_edited.csv', delimiter=',')

FGCdata_all_withstr = genfromtxt('C:\Users\dong87\Documents\ML_data\Info_FGC_P151822_edited.csv', delimiter=',', dtype="|U50")
(rows_all, columns_all) = np.shape(FGCdata_all)
print('The total FGC data shape is %s:'%[rows_all, columns_all])
Para_index = (13, 14, 15) # depends on the read .csv file
Para_number = np.shape(Para_index)
FGCdata = np.zeros((193, Para_number[0]))  # 193 = 160/2+(387-161)/2
FGCdata_all_4para = np.zeros((387, Para_number[0]))
for i in Para_index:
    FGCdata_all_4para[:, i-13] = FGCdata_all[:, i]                             
for i in range (160):
    if i % 2 == 0:
        for j in Para_index:
            FGCdata[int(i/2), j-13] = FGCdata_all[i, j]
for i in range (161, 386):
    if i % 2 == 1:
        for j in Para_index:
            FGCdata[int(i/2), j-13] = FGCdata_all[i, j]         



(rows, columns) = np.shape(FGCdata)
#print(FGCdata)
print('The shape of useful FGC data is %s with the 13, 14, 15 and 16 column' %[rows, columns])
"""
Find the statistical parameters of 4 columns: std or average
"""
std =np.std(FGCdata, axis = 0)   # 0 for the std for each columns
print('The standard deviation of FGCdata is %s' %std)
avg = np.average(FGCdata, axis = 0)
print('The average of FGC data is [ IL: %5.3f(dB)  Peak WL:%5.3f(nm)  1dB BW: %5.3f(nm) ]' %(avg[0],avg[1], avg[2]))
# relative standard deviation = std/avg 
rsd = scipy.stats.variation(FGCdata, axis = 0)
print('The relative standard deviation of FGCdata is %s' %np.abs(rsd))

"""
Apply K-means
"""


x_FGC = FGCdata_all_4para


k_means = cluster.KMeans(n_clusters=2)
k_means.fit(x_FGC) 

FGCdata_all_labels = k_means.labels_[::1]

count = 0
size_FGCdata_all_labels = np.shape(FGCdata_all_labels)[0]
print(np.shape(FGCdata_all_labels)[0])
for i in range(size_FGCdata_all_labels):
    if FGCdata_all_labels[i] == 0:
        count = count + 1
list_class1 = np.zeros((count,1))
count = -1
for i in range(size_FGCdata_all_labels):       
    if FGCdata_all_labels[i] == 0:   
        count = count + 1
        list_class1[count,0] = i

FGCdata_all_withlb = np.zeros((np.shape(FGCdata)[0], np.shape(FGCdata)[1]+1))

for i in range(np.shape(FGCdata)[0]):
    for j in range(np.shape(FGCdata)[1]):
        FGCdata_all_withlb[i,j] = FGCdata[i,j]
for i in range(np.shape(FGCdata)[0]):
    FGCdata_all_withlb[i, np.shape(FGCdata)[1]] = FGCdata_all_labels[i]        
    
print(FGCdata_all_withlb)  

labels_rawdata = np.zeros((np.shape(FGCdata)[0], 1))

for i in range(np.shape(FGCdata)[0]):
    if FGCdata_all_withstr[i, 4] == 'FGCCTE_FC1DC_626_313':
        labels_rawdata[i,0] = 0
    if FGCdata_all_withstr[i, 4] == 'FGCCTE_FCWFC1DC_630_378':
        labels_rawdata[i,0] = 1 ## because only two class here
print('the raw data label is %s'%labels_rawdata)

count_313 = 0
count_378 = 0
for i in range(np.shape(FGCdata)[0]):
    if labels_rawdata[i] == 0:
        count_313 += 1
    if labels_rawdata[i] == 1:
        count_378 += 1
num_FGCCTE_FC1DC_626_313 = count_313
num_FGCCTE_FCWFC1DC_630_378 = count_378

count = 0
for i in range(np.shape(labels_rawdata)[0]):
    if labels_rawdata[i] == FGCdata_all_labels[i]:
        count += 1
total_match = count
count = 0
for i in range(np.shape(labels_rawdata)[0]):
    if labels_rawdata[i] == FGCdata_all_labels[i] == 0:
        count += 1
match_FGCCTE_FC1DC_626_313 = count
count = 0
for i in range(np.shape(labels_rawdata)[0]):
    if labels_rawdata[i] == FGCdata_all_labels[i] == 1:
        count += 1
match_FGCCTE_FCWFC1DC_630_378 = count
print(np.shape(FGCdata))
print(total_match, match_FGCCTE_FC1DC_626_313, match_FGCCTE_FCWFC1DC_630_378  )
print('The total match ratio is %5.3f'%(total_match/np.shape(labels_rawdata)[0]))
print('FGCCTE_FC1DC_626_313 match ratio is %5.3f'%(match_FGCCTE_FC1DC_626_313/num_FGCCTE_FC1DC_626_313))
print('FGCCTE_FCWFC1DC_630_378 match ratio is %5.3f'%(match_FGCCTE_FCWFC1DC_630_378/num_FGCCTE_FCWFC1DC_630_378))
# plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

#for c, m in [('r', 'o'), ('b', '^')]:
"""
# define color code in the label
color label: b: blue, g: green, r: red, c: cyan, m: magenta, y: yellow, k: black, w: white
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
    if FGCdata_all_labels[i] == 6:
        label_color_code[i] = 'k'
for i in range (size_FGCdata_all_labels):
    xs = FGCdata_all_4para[i,0]
    ys = FGCdata_all_4para[i,1]
    zs = FGCdata_all_4para[i,2]
    c = label_color_code[i]
    ax.scatter(xs, ys, zs, c=c)

ax.set_xlabel('IL')
ax.set_ylabel('Peak WL')
ax.set_zlabel('1dB BW')
plt.show()
"""
colors = [int(i % 23) for i in FGCdata_all_labels]
pylab.scatter(FGCdata_all_4para[0],FGCdata_all_4para[1], FGCdata_all_4para[2], c=colors)
plt.show()
"""

""" 
count = 0
for i in range(4898):
    if wine_all[i, 11] == 5 or wine_all[i, 11] == 6:
#         wine[i, :] = wine_all[i,:]
        count = count + 1
# print(count)

row = count
wine = np.zeros((row, 12)) 

count = 0
for i in range(4898):
    if wine_all[i, 11] == 5 or wine_all[i, 11] == 6:
        wine[count, :] = wine_all[i,:]   
        count = count + 1    

for i in range(row):
    if wine[i, 11] == 6:
        wine[i, 11] = 1
    if wine[i, 11] == 5:
        wine[i, 11] =0
 
#print(np.shape(wine)) # (3655, 12)
#print(wine)


x_train = np.zeros((2000, 11))
y_train = np.zeros((2000, 1))

x_validation = np.zeros((1000, 11))
y_validation = np.zeros((1000, 1))
y_valipredict = np.zeros((1000, 1))

x_test = np.zeros((655, 11))
y_test = np.zeros((655, 1))
y_testpredict = np.zeros((655, 1))
for i in range(2000):
    for j in range(11):
        x_train[i,j] = wine[i, j]
for i in range(2000):
    y_train[i] = wine[i, 11]
    
for i in range(1000):
    for j in range(11):
        x_validation[i,j] = wine[i+2000, j]
for i in range(1000):
    y_validation[i] = wine[i+2000, 11]   
    
for i in range(655):
    for j in range(11):
        x_test[i,j] = wine[i+3000, j]
for i in range(655):
    y_test[i] = wine[i+3000, 11]   

#print (y_train)
# clf = MLPClassifier(activation = 'logistic',
#                     solver='adam', 
#                     alpha=0.0001, 
#                     hidden_layer_sizes=(1, 10), 
#                     random_state=1)
# 
# clf.fit(x_train, y_train)  

# clf = MLPClassifier(activation='logistic', alpha=1e-05, batch_size='auto',
#           beta_1=0.9, beta_2=0.999, early_stopping=False,
#           epsilon=1e-08, hidden_layer_sizes=(1, 10), learning_rate='constant',
#           learning_rate_init=0.001, max_iter=1000, momentum=0.9,
#           nesterovs_momentum=True, power_t=0.5, random_state=1, shuffle=True,
#           solver='adam', tol=0.0001, validation_fraction=0.1, verbose=False,
#           warm_start=False)
# clf.fit(x_train, y_train) 




  
clf = svm.SVC(C=1, cache_size=300, class_weight='balanced', coef0=0.0,
     decision_function_shape='ovr', degree=2, gamma='auto', kernel='poly',         
     max_iter=-1, probability=True, random_state=None, shrinking=True,                 
     tol=0.0001, verbose=False)

# balanced class_weigegt assign different weight to the  samples   
# c for bounder smooth 
# gamma = 'auto' means 1/n_features 
# shrinking increase the running speed.

clf.fit(x_train, y_train) 
  
y_temp = clf.predict(x_validation)
for i in range(1000):
    y_valipredict[i] = y_temp[i] 
#print(np.shape(y_valipredict))
#print(np.shape(y_validation))
#print(y_valipredict)
count = 0
for i in range(1000):
    if y_validation[i] != y_valipredict[i]:
        count = count + 1
        
mismatch_validation = count
mismatch_errorvalidation = (count/1000)
#print(y_valipredict)
print('the error of validation is %.3f.' %mismatch_errorvalidation)
# a = clf.get_params(deep=True)
# print(a)
#print (count)   


y_temp = clf.predict(x_test)
for i in range(655):
    y_testpredict[i] = y_temp[i] 
#print(np.shape(y_testpredict))
#print(np.shape(y_test))
# print(y_test)
count = 0
for i in range(655):
    if y_test[i] != y_testpredict[i]:
        count = count + 1
        
mismatch_test = count
mismatch_errortest = (count/655)
# print(y_testpredict)
print('the error of test is %.3f.' %mismatch_errortest)
# a = clf.get_params(deep=True)
# print(a)
#print (count)   
# total true (1)
count = 0
for i in range(655):
    if y_test[i] == 1:
        count = count +1
positive = count 

count = 0
for i in range(655):
    if y_test[i] == 0:
        count = count +1
negative = count 

count = 0
for i in range(655):
    if y_test[i] == 1 and y_testpredict[i] ==1:
        count = count +1
true_positive = count/positive 

count = 0        
for i in range(655):
    if y_test[i] == 0 and y_testpredict[i] == 0:
        count = count +1
true_negative = count/negative

count = 0
for i in range(655):
    if y_test[i] == 0 and y_testpredict[i] == 1:
        count = count + 1
false_positive = count/negative

count = 0 
for i in range(655):
    if y_test[i] == 1 and y_testpredict[i] == 0:
        count = count + 1
false_negative = count/positive

print ('the true positive is %5.3f.' % true_positive) 
print ('the true negative is %5.3f.' % true_negative) 
print ('the false positive is %5.3f.' % false_positive) 
print ('the false negative is %5.3f.' % false_negative) 
"""