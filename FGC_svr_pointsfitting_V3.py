import numpy as np
import math
from sklearn.svm import SVR
from sklearn import grid_search
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.optimize as optimize
from scipy import asarray as ar, exp


class xypoints_fitting(object):

    def __init__(self, lm=[]):
        """
        training: training points, 3 points are minimum! CANNOT be less
        predict: results from model
        validate: new points
        """
        self.training_u = lm
        self.training_x = lm
        self.training_y = lm
        self.vali_u = lm
        self.vali_x = lm
        self.vali_y = lm
        self.predict_x = lm
        self.predict_y = lm
        self.C = 10e4
        self.gamma = 0.01
        self.epsilon = 0.001
        self.criteria = 0
        self.error = lm
        self.error_x = lm
        self.error_y = lm
	"""	
	def FitModel_OLD(self):
        svr_rbf = SVR(kernel='rbf',  C=self.C, gamma=self.gamma, epsilon = self.epsilon)#https://en.wikipedia.org/wiki/Radial_basis_function
        self.model = svr_rbf.fit(self.training_X, self.training_Y)
		pass 
	"""	
	def Evaluate_x(self, x):
        '''evaluate the model for a given value of the independent variable'''
        return self.model_x.predcit(x)
	def Evaluate_y(self, x):
	    return self.model_y.predict(y)	
		
    def Fitmodel(self):
        svr_rbf = SVR(kernel='rbf', C=self.C, gamma=self.gamma,
                      epsilon=self.epsilon)
        self.model_x = svr_rbf.fit(self.training_u, self.training_x)
        self.model_y = svr_rbf.fit(self.training_u, self.training_y)
        return model_x, model_y
    def SVRegresion(self):
        n = len(self.training_u)  # the number of data
        self.training_u = self.training_u.reshape((n, 1))  # the requirement of SVR
        self.training_x = self.training_x.reshape((n,))
        self.training_y = self.training_y.reshape((n,))
        self.vali_u = self.vali_u.reshape((len(self.vali_u), 1))
        svr_rbf = SVR(kernel='rbf', C=self.C, gamma=self.gamma,
                      epsilon=self.epsilon)  # https://en.wikipedia.org/wiki/Radial_basis_function
        self.predict_x = svr_rbf.fit(self.training_u, self.training_x).predict(self.vali_u)
        self.predict_y = svr_rbf.fit(self.training_u, self.training_y).predict(self.vali_u)
        print svr_rbf.get_params(deep=True)
        return self.predict_x, self.predict_y

    def Prune(self):
        self.SVRegresion()
        self.error_x = np.sum(self.calculate_error(self.vali_x, self.predict_x))
        self.error_y = np.sum(self.calculate_error(self.vali_y, self.predict_y))
        self.error = self.error_x + self.error_y
        if self.error <= self.criteria:
            print('the error is below threshold')
        else:
            training_u = self.__add(self.training_u, self.vali_u)
            training_x = self.__add(self.training_x, self.vali_x)
            training_y = self.__add(self.training_y, self.vali_y)
            self.vali_u = training_u
            error_x = np.zeros(np.shape(training_u)[0])
            error_y = np.zeros(np.shape(training_u)[0])
            error = np.zeros(np.shape(training_u)[0])

            for i in range(np.shape(training_u)[0]):
                self.training_u = np.delete(training_u, i)
                self.training_x = np.delete(training_x, i)
                self.training_y = np.delete(training_y, i)
                self.vali_u = training_u
                self.SVRegresion()
                error_x[i] = np.sum(self.calculate_error(training_x, self.predict_x))
                error_y[i] = np.sum(self.calculate_error(training_y, self.predict_y))
                error[i] = error_x[i] + error_y[i]
                print (error[i])
            print (np.argmin(error))
            self.error = error[np.argmin(error)]
            self.training_u = np.delete(self.training_u, np.argmin(error))
            self.training_x = np.delete(self.training_x, np.argmin(error))
            self.training_y = np.delete(self.training_y, np.argmin(error))
            print(error_x, error_y)
            print('we delete the %dth element' % np.argmin(error))

    def __delete(self):
        pass

    def __add(self, X, Y):
        __sum = np.concatenate((X, Y))
        return __sum

    def calculate_error(self, X, Y):
        """
        error is a string
        """
        self.error = np.zeros((len(X)))
        for ele in range(np.shape(self.error)[0]):
            self.error[ele] = np.abs(X[ele] - Y[ele])
        return self.error

    def new_trainingset(self):
        self.training_u = self.__add(self.training_u, self.vali_u)
        self.training_x = self.__add(self.training_x, self.vali_x)
        self.training_y = self.__add(self.training_y, self.vali_y)
        # return self.training_X


@staticmethod
def svc_param_selection(X, Y, nfolds):
    n = len(X)  # the number of data
    X = X.reshape((n, 1))  # the requirement of SVR
    Y = Y.reshape((n,))
    Cs = [0.1, 1, 1e1, 1e2, 1e3, 1e4, 1e5]
    gammas = [0.001, 0.001, 0.01, 0.1, 1]
    epsilon = [0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10]
    param_grid = {'C': Cs, 'gamma': gammas, 'epsilon': epsilon}
    gs = grid_search.GridSearchCV(SVR(kernel='rbf'), param_grid, cv=nfolds)
    gs.fit(X, Y)
    gs.best_params_
    return gs.best_params_


if __name__ == '__main__':

    X = ar([-9.315, -9.216, -9.172, -9.166, -9.168, -9.233])
    Y = ar([6.0136, 4.599, 3.186, 2.440, 1.742, 0.2852])
    U = ar([4.85, 5.85, 6.85, 7.35, 7.85, 8.85])
    U_vali = ar([4.85, 5.85, 6.85, 7.35, 7.85, 8.85])

    points_amount = 7
    idx = np.zeros(points_amount)
    for i in range(points_amount):
        idx[i] = i
    training_idx = [int(idx[0]), int(idx[2]), int(idx[5])]
    # vali_idx = [int(idx[3]), int(idx[4]), int(idx[5])]
    vali_idx = [int(idx[3])]
    a = xypoints_fitting()
    a.training_u = U[training_idx]
    a.training_x = X[training_idx]
    a.training_y = Y[training_idx]
    a.vali_u = U[vali_idx]
    a.vali_x = X[vali_idx]
    a.vali_y = Y[vali_idx]
    predict_x, predict_y = a.SVRegresion()

    print (a.calculate_error(predict_x, a.vali_x))
    print (a.calculate_error(predict_y, a.vali_y))
    a.Prune()
    """
    ##########
    #plotting#
    ##########
    lw = 2
    plt.scatter(U, X, color='darkorange', label='data_X')
    __sad = [int(idx[0]), int(idx[2]), int(idx[5]), int(idx[3])]
    __training_u = np.concatenate(U[training_idx], U[vali_idx])
    plt.scatter(__training_u, a.predict_x, color='navy', lw=lw, label='fit_X')
    plt.xlabel('angle')
    plt.ylabel('x-coordinator(mm)')
    plt.title('Support Vector Regression')
    plt.legend()
    plt.show()

    plt.scatter(U, a.error*1000, color='navy', lw=lw, label='fit_X')
    for a, b in zip(U, a.error*1000):
        plt.text(a, b, "{0:.3f}".format(b))
    plt.xlabel('angle')
    plt.ylabel('error[um]')
    plt.title('Support Vector Regression error')
    plt.legend()
    plt.show()
    """



