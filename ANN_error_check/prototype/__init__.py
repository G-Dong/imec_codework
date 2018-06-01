from __future__ import division
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn import svm
import csv
import numpy as np
from numpy import genfromtxt



wine_all = genfromtxt('C:\Users\dong87\Downloads\winequality_data(1)\winequality-white - edited.csv', delimiter=',')

print('The total sample shape is: \n')
print(np.shape(wine_all))
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
"""
balanced class_weigegt assign different weight to the  samples   
c for bounder smooth 
gamma = 'auto' means 1/n_features 
shrinking increase the running speed.
"""
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