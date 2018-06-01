import numpy as np

def similar_triangle(no):
	y10 = np.zeros(no)
	delta_y = np.zeros(no)
	secant = np.zeros(no)
	delta_theta =np.zeros(no)
	factor = np.zeros(no)
	bot = np.zeros(no)# R = bot + delta_x
	R = np.zeros(no)
	delta_u = np.zeros(no)

	for i in range(no):
		y10[i] = (y0+y1[i])/2.0
		#u10 = (u1+u0)/2.0
		delta_u[i] = -(u1[i]-u0)# u0 is the maximam value.
		delta_y[i] = (y1[i] - y0)/2 # if positive, two functions get the same result.
		#secant[i] = np.abs(np.sqrt((x1[i]-x0)**2+(y1[i]-y0)**2))
		secant[i] = np.sqrt((x1[i]-x0)**2+(y1[i]-y0)**2)
		#print ('%1.8f'%secant[i])
		#print(delta_y[i])
		#print(2.0*delta_y[i]/secant[i])
		delta_theta[i] = 2.0*np.arccos(2.0*delta_y[i]/secant[i])
		factor[i] = delta_theta[i]/delta_u[i]
		#print secant[i]
		#print (np.sin(delta_theta[i]/2.0))
		#print(delta_theta[i])
		#R[i] = (secant[i]/2.0)/np.sin(delta_theta[i]/2.0)
		R[i] = (y1[i] - y0)/np.sin(delta_theta[i])
	return(delta_theta, R, factor, secant)
	#print (delta_theta, R, factor, secant)


def Pythagorean(no):
	delta_y = np.zeros(no)
	secant = np.zeros(no)
	delta_theta =np.zeros(no)
	factor = np.zeros(no)
	bot = np.zeros(no)# R = bot + delta_x
	delta_x = np.zeros(no)
	R = np.zeros(no)
	delta_u = np.zeros(no)
	for i in range (no):
		delta_u[i] = -(u1[i]-u0)
		delta_y[i] = (y1[i] - y0)#positive or negative gets the same result.
		delta_x[i] = x0-x1[i]
		bot[i] = R[i] -(x0-x1[i])
		secant[i] = np.abs(np.sqrt((x1[i]-x0)**2+(y1[i]-y0)**2))
		R[i] = secant[i]**2/(2*delta_x[i])
		delta_theta[i] = np.arcsin(delta_y[i]/R[i])
		factor[i] = delta_theta[i]/delta_u[i]
	return(delta_theta, R, factor, secant)
	
if __name__ == '__main__':
	u0 = 7.275 
	x0 = -11.304895
	y0 = -0.056506
	# 2.075
	#leftpos = self.LEFT.PositionCurrentGet(returntype='6dof') #this should be another position given a new u
	u1 = np.array([
	6.00000,
	5.5,
	5.0,
	4.5
	])
	x1 = np.array([
	-11.347025,
	-11.38847333,
	-11.43917,
	-11.50210333
	])
	y1 =np.array([
	1.779836667,
	2.490611667,
	3.19978,
	3.898571667
	])
	no= np.shape(u1)[0]


	#print x1, y1, u1	
	#x10 = (x0+x1)/2.0
	result_2 = Pythagorean(no)
	result_1 = similar_triangle(no)
	print('Results from similar_triangle are:')
	print ('delta_theta is:\n%s'%result_1[0])
	print ('radius is: \n%s and its average is%f'%(result_1[1],np.average(result_1[1])))
	print ('factor is: \n%s and its average is%f'%(result_1[2], np.average(result_1[2])))
	print ('scant is: \n%s'%result_1[3])
	print('Results from Pythagorean are:')
	print ('delta_theta is:\n%s'%result_2[0])
	print ('radius is: \n%s and its average is%f'%(result_2[1],np.average(result_2[1])))
	print ('factor is: \n%s and its average is%f'%(result_2[2], np.average(result_2[2])))
	print ('scant is: \n%s'%result_2[3])





#delta_y_new = R*np.sin(factor*(u2-u1))
#delta_x_new = R*(1-np.cos(factor*(u2-u1)))