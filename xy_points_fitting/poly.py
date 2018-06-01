import  numpy as np
import matplotlib.pyplot as plt
from scipy import asarray as ar,exp
X = ar([-9.216, -9.172, -9.166, -9.168, -9.233, -9.315])
Y = [4.599, 3.186, 2.440, 1.742, 0.2852, 6.0136]
U = ar([5.85, 6.85, 7.35, 7.85, 8.85, 4.85])
i, j = 0, 5
validation_idx = 3
coef_X = np.polyfit(U[i:j], X[i:j] ,  2)#r^{2}-2rr_{0}\cos(\theta -\varphi )+r_{0}^{2}=a^{2}
#coef_Y = np.polyfit(U[i:j],  Y[i:j], 2)
ffit_X = np.poly1d(coef_X)
#ffit_Y = np.poly1d(coef_Y)

error = ffit_X(U[validation_idx]) - X[validation_idx]
print ('the error of polyfit is %.5f'%error)
U_new = np.linspace(4, 10, num=len(U)*10)
fig1 = plt.figure()                                                                                       
ax1 = fig1.add_subplot(111)                                                                                   
ax1.scatter(U, X, color='darkorange', label='data', facecolors='None')                                                                     
ax1.plot(U_new, ffit_X(U_new))  
#ax1.scatter(U, Y, color='darkorange', label='data', facecolors='None')                                                                     
#ax1.plot(U_new, ffit_Y(U_new))                                                             
plt.show()

