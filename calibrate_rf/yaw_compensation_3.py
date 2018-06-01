import math
import numpy as np
#from __future__ import division# for float division 




def yaw_compensation(self, delta_theta):
    """
    Steps: 
    1. Get start point(x1, y1)
    2. Change yaw (delta_theta)
    3. Get end point(x2, y2)
    4. Calculate(x_delta, y_delta), calculate center (center_x, center_y)
    5. Move center along x and y by adding (x_delta, y_delta) to center. 
    
    """
    #x1, y1, zc, yaw1, pitch, roll 
    leftpos = self.LEFT.PositionCurrentGet(returntype='6dof')
    x1 = leftpos.x
    y1 = leftpos.y
    yaw1 = leftpos.yaw
    """
    only change yaw angle and maintain other parameters the same. Not sure about the function
    """
    self.LEFT.MoveRelative6DOF(0.0, 0.0, 0.0, yaw1=delta_theta, pitch=0.0, roll=0.0)
    #x2, y2, zc, yaw2, pitch, roll 
    leftpos2 = self.LEFT.PositionCurrentGet()
    x2 = leftpos2.x
    y2 = leftpos2.y
    yaw2 = leftpos2.yaw
    x_delta = x2 - x1 # no absolute, with the same order as start - end
    y_delta = y2 - y1
    xm = (x1+x2)/2
    ym = (y1+y2)/2
    """
    Analytic geometry part: 
    1. Solving binary quadratic form:
                |point1, center| = r ................................ I
                arctan(vertical_line/.5*secant) = .5*delta_theta .... II
    2. Then get the line passing through center: y = kx + B.
    3. Substitution this line to I
    4. Choose the proper point out of 2 roots as the centre coordinator.
    """
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    R = (secant/2) / math.sin(np.absolute(yaw1-yaw2)/2)
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    A = (1/4)*(secant**2/(math.tan((yaw1-yaw2)/2))**2)
    B = (A - R**2 - (xm**2+ym**2-x1**2-y1**2))/(2*y1 - 2*ym)
    k = (xm-x1)/(y1 - ym)
    criteria = (2*(k*B - k*y1 -x1))**2 - 4*(1+k**2)*((B-y1)**2 +x1**2-R**2)# test if it has real roots
    center_x1 = (-2*(k*B-k*y1-x1) + np.sqrt(criteria))/(2*(1+k**2)) 
    center_x2 = (-2*(k*B-k*y1-x1) - np.sqrt(criteria))/(2*(1+k**2)) 
    center_y1 = k*center_x1 + B
    center_y2 = k*center_x2 + B      
    if (y1-center_x1)/(x1-center_x1) == math.tan(yaw1):
        center_x = center_x1
        center_y = center_y1
    else:
        center_x = center_x2
        center_y = center_y2
        center_start = (center_x, center_y)
    center_end = (center_x + x_delta, center_y + y_delta, zc)
    self.LEFT.MoveRelative(center_end)
    return (center_start, center_end)

def __calibrate_yaw_factor__(self):
    """
    same as __calibrate_yaw__, but:
    -when commanding a fiber stage movement using MoveRelative6DOF we
        don't specify angles but linear excursions of the actuators
        mounted on the rotation stages
    -we don't know a priori what excursion we need to get 1 degree rotation
    -so we need to calibrate to figure out the factor that converts
        excursions in mm to angles in radians
    """
	"""
	presume that the first position is parallel with the x-axis!!! 
	Still finding more general algorithm. However, if we want to know the factor, we must know the angle. u is only for helping figure out factor.
	Thus, we only know the position of each position. It is impossible to get the centre, R or angle only given position.
	"""
	"""
	0 position with center defines the line which is parallel to the x-axis. Thus we can find center following after R.
	Need the experiment to find the accuracy.
	"""
	u0 = 7.438 
	x0 = -10.921
	y0 = 2.066 # 2.075
	leftpos = self.LEFT.PositionCurrentGet(returntype='6dof')# this should be another position given a new u
    x1 = leftpos.x
    y1 = leftpos.y
    u1 = leftpos.yaw
	print x1, y1, u1
	#x10 = (x0+x1)/2.0
	y10 = (y0+y1)/2.0
	#u10 = (u1+u0)/2.0
	delta_u = u1-u0
	delta_y = y10-y0
	secant = np.sqrt((x1-x0)**2+(y1-y0)**2)
	delta_theta = 2.0*np.arccos((2.0*delta_y/secant))
	factor = delta_theta/delta_u
	R = (secant/2.0)/np.sin(delta_theta/2.0)
	xc = x1 - R
	yc = y0
	center = np.array([xc, yc])
#	print('the yaw angle is %f'%theta)
#	print('the center is %s'% center)
	return (factor, center, R)
	
	

def __calibrate_yaw_old__(self):
	"""
	Old algorithm with more general cases. But, if we nned to know the factor with given knwledge, we may not use this complex algorithm
	"""
    """
    calibrate xy compensation for yaw adjustment by asking the user
    to align left fiber to a grating, then applying a yaw offset and
    asking user to align fiber to the same grating again. 
    """
    delta_theta = 0.01
    print "Please align the left fiber to a grating of your choice..."
    print "Press esc when done."
    self.__array_navigator__()
    #read position of the left fiber:
    leftpos = self.LEFT.PositionCurrentGet(returntype='6dof')
    x1 = leftpos.x
    y1 = leftpos.y
    yaw1 = leftpos.yaw
    #then change yaw by a certain amount:
    """
    only change yaw angle and maintain other parameters the same. Not sure about the function
    """
    self.LEFT.MoveRelative6DOF(0.0, 0.0, 0.0, yaw1=delta_theta, pitch=0.0, roll=0.0)
    print "Please align the left fiber to the same grating again..."
    print "Press esc when done."
    self.__array_navigator__()
    #read position of the left fiber:
    leftpos = self.LEFT.PositionCurrentGet(returntype='6dof')
    x2 = leftpos.x
    y2 = leftpos.y
    yaw2 = leftpos.yaw
    xm = (x1+x2)/2
    ym = (y1+y2)/2
    """
    Analytic geometry part: 
    1. Solving binary quadratic form:
                |point1, center| = r ................................ I
                arctan(vertical_line/.5*secant) = .5*delta_theta .... II
    2. Then get the line passing through center: y = kx + B.
    3. Substitution this line to I
    4. Choose the proper point out of 2 roots as the center coordinator.
    """
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    R = (secant/2) / math.sin(np.absolute(yaw1-yaw2)/2)
    self.yaw_radius = R
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    A = (1/4)*(secant**2/(math.tan((yaw1-yaw2)/2))**2)
    B = (A - R**2 - (xm**2+ym**2-x1**2-y1**2))/(2*y1 - 2*ym)
    k = (xm-x1)/(y1 - ym)
    criteria = (2*(k*B - k*y1 -x1))**2 - 4*(1+k**2)*((B-y1)**2 +x1**2-R**2)# test if it has real roots
    center_x1 = (-2*(k*B-k*y1-x1) + np.sqrt(criteria))/(2*(1+k**2)) 
    center_x2 = (-2*(k*B-k*y1-x1) - np.sqrt(criteria))/(2*(1+k**2)) 
    center_y1 = k*center_x1 + B
    center_y2 = k*center_x2 + B      
    if (y1-center_x1)/(x1-center_x1) == math.tan(yaw1):
        center_x = center_x1
        center_y = center_y1
    else:
        center_x = center_x2
        center_y = center_y2
    self.yaw_center = (center_x, center_y)

def __move_yaw__(self, delta_yaw):
    """
    Moves the yaw angle of the left fiber by the specified amount.
    """
    #calculate based on delta_yaw and self.yaw_center, self.yaw_radius
    x_delta = self.yaw_radius*(1-np.cos(delta_yaw))
    y_delta = self.yaw_radius*np.sin(delta_yaw)
    self.LEFT.MoveRelative6DOF(x_delta, y_delta, 0.0, yaw1=delta_yaw, pitch=0.0, roll=0.0)