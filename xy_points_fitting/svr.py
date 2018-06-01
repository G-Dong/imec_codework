import numpy as np
import math
from sklearn.svm import SVR
from sklearn import grid_search
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.optimize as optimize 
from scipy import asarray as ar,exp

class xypoints_fitting(object):
    
    def __init__(self, lm = []):
        """
        training: training points
        predict: results from model
        validate: new points
        """
        self.training_X = lm
        self.training_Y = lm
        self.vali_X = lm
        self.vali_Y = lm
        self.predict_Y = lm
        self.C = 10e4
        self.gamma = 0.01
        self.epsilon = 0.001
        

    def SVRegresion(self):
        n = len(self.training_X)   #the number of data     
        X = self.training_X.reshape((n,1)) # the requirement of SVR
        Y = self.training_Y.reshape((n,)) 
        X_vali =  self.vali_X.reshape((len(self.vali_X), 1))              
        svr_rbf = SVR(kernel='rbf',  C=self.C, gamma=self.gamma, epsilon = self.epsilon)#https://en.wikipedia.org/wiki/Radial_basis_function
        self.predict_Y = svr_rbf.fit(X, Y).predict(X_vali)
        print svr_rbf.get_params(deep=True)
        return self.predict_Y
    
    def __add(self, X, Y):
        __sum = np.concatenate((X, Y))
        return __sum
    
    def calculate_error(self, X, Y):
        error = np.zeros((len(X)))
        for ele in range (np.shape(error)[0]):
            error[ele] = np.abs(X[ele]- Y[ele])
        return error
    
    def new_trainingset(self):
        self.training_X = self.__add(self.training_X, self.vali_X)
        self.training_Y = self.__add(self.training_Y, self.vali_Y)    
        return self.training_X
@staticmethod
def svc_param_selection(X, Y, nfolds):
        n = len(X)   #the number of data     
        X = X.reshape((n,1)) # the requirement of SVR
        Y = Y.reshape((n,))
        Cs = [0.1,1,1e1,1e2,1e3,1e4,1e5]
        gammas = [0.001, 0.001, 0.01, 0.1, 1]
        epsilon = [0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10]
        param_grid = {'C': Cs, 'gamma' : gammas, 'epsilon': epsilon}
        gs = grid_search.GridSearchCV(SVR(kernel='rbf'), param_grid, cv=nfolds)
        gs.fit(X, Y)
        gs.best_params_
        return gs.best_params_





X = ar([ -9.315, -9.216, -9.172, -9.166, -9.168, -9.233])
Y = ar([6.0136, 4.599, 3.186, 2.440, 1.742, 0.2852 ])
U = ar([4.85, 5.85, 6.85, 7.35, 7.85, 8.85 ])
U_vali = ar([4.85, 5.85, 6.85, 7.35, 7.85, 8.85 ])

points_amount = 7
idx = np.zeros((points_amount))
for i in range (points_amount):
    idx[i] = i
training_idx =[int(idx[0]), int(idx[1]), int(idx[2])]
vali_idx = [int(idx[3]), int(idx[4]), int(idx[5])]

a = xypoints_fitting()
a.training_X = U[training_idx]
a.training_Y = X[training_idx]
a.vali_X = U[vali_idx]
a.vali_Y = X[vali_idx]

predict_Y =  a.SVRegresion()
print a.calculate_error(predict_Y, a.vali_Y)
a.new_trainingset()


#print svc_param_selection(U, X, 2)

"""
validation_idx = 0
hyper_para = svc_param_selection(U_training, X_training, len(U_training)-1)
#X_rbf = SVRegresion(U_training, X_training, U_vali, hyper_para.get('C'),
#                                                         hyper_para.get('gamma'),
#                                                         hyper_para.get('epsilon'))

X_rbf = SVRegresion(U_training, X_training , U, C = 10e4, gamma = 0.01, epsilon = 0.001)
#error = np.abs(X[validation_idx]-x_rbf)
error = np.zeros((len(X_rbf)))
for ele in range (np.shape(error)[0]):
    error[ele] = np.abs(X[ele]- X_rbf[ele])
    
print ('the error of svr is %s'%error)
#Y_rbf = SVRegresion(U, Y)
lw = 2
plt.scatter(U, X, color='darkorange', label='data_X')
plt.scatter(U, X_rbf, color='navy', lw=lw, label='fit_X')
plt.xlabel('angle')
plt.ylabel('x-coordinator(mm)')
plt.title('Support Vector Regression')
plt.legend()
plt.show()

plt.scatter(U, error*1000, color='navy', lw=lw, label='fit_X')
for a, b in zip(U, error*1000):
    plt.text(a, b, "{0:.3f}".format(b))
plt.xlabel('angle')
plt.ylabel('error[um]')
plt.title('Support Vector Regression error')
plt.legend()
plt.show()
"""



