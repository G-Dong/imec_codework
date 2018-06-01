#from __future__ import division# for float division
import math
import numpy as np
import scipy.optimize as optimize 
import matplotlib.pyplot as plt



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
    R = (secant/2.0) / math.sin(np.absolute(yaw1-yaw2)/2.0)
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    A = (1/4.0)*(secant**2/(math.tan((yaw1-yaw2)/2.0))**2)
    B = (A - R**2 - (xm**2+ym**2-x1**2-y1**2))/(2.0*y1 - 2.0*ym)
    k = (xm-x1)/(y1 - ym)
    criteria = (2.0*(k*B - k*y1 -x1))**2 - 4.0*(1+k**2)*((B-y1)**2 +x1**2-R**2)# test if it has real roots
    center_x1 = (-2.0*(k*B-k*y1-x1) + np.sqrt(criteria))/(2.0*(1+k**2)) 
    center_x2 = (-2.0*(k*B-k*y1-x1) - np.sqrt(criteria))/(2.0*(1+k**2)) 
    center_y1 = k*center_x1 + B
    center_y2 = k*center_x2 + B      
    if (y1-center_x1)/(x1-center_x1) == math.tan(yaw1):
        center_x = center_x1
        center_y = center_y1
    else:
        center_x = center_x2
        center_y = center_y2
        center_start = (center_x, center_y)
    center_end = (center_x + x_delta, center_y + y_delta, 0.0)
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
    u0 = 0.0
    print "Please align the left fiber to a grating of your choice..."
    print "Press esc when done."
    self.__array_navigator__()
    #read position of the left fiber:
    leftpos = self.A.LEFT.PositionCurrentGet(returntype='6dof')
    print leftpos
    x1 = leftpos.x
    y1 = leftpos.y
    u1 = leftpos.yaw
    delta_theta = 0.1*u1
    #then change yaw by a certain amount:
    """
    only change yaw angle and maintain other parameters the same. Not sure about the function
    """
    self.A.LEFT.MoveRelative6DOF(0.0, 0.0, 0.0, yaw=delta_theta, pitch=0.0, roll=0.0)
    print "Please align the left fiber to the same grating again..."
    print "Press esc when done."
    self.__array_navigator__()
    #read position of the left fiber:
    leftpos2 = self.A.LEFT.PositionCurrentGet(returntype='6dof')
    print leftpos2
    x2 = leftpos2.x
    y2 = leftpos2.y
    u2 = leftpos2.yaw
    
    """find out k, R, f"""
    k = np.sqrt((x2-x1)**2+(y2-y1)**2)
    Rf = k/(u2-u1)
    
    
    
    u1 = u1 - u0
    #u2 = u2 - u0
    x_delta = x2 - x1 # no absolute, with the same order as start - end
    y_delta = y2 - y1
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    """
    solve:
    a*x^2 + b*x + c = 0 
    with x = factor*u
    """
    a = x_delta**2 + y_delta**2
    b = -secant*x_delta
    c = (secant/2.0)**2 -y_delta**2

    yaw_1 = (-b + np.sqrt(b**2-4.0*a*c))/(2.0*a)
    yaw_2 = (-b - np.sqrt(b**2-4.0*a*c))/(2.0*a)
    if y2 > y1:
        yaw = yaw_1
    else:
        yaw = yaw_2
    factor = (yaw)/(u1)
    return factor

def __calibrate_yaw__(self):
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
    xm = (x1+x2)/2.0
    ym = (y1+y2)/2.0
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
    R = (secant/2.0) / math.sin(np.absolute(yaw1-yaw2)/2.0*self.yaw_factor)
    #self.yaw_radius = R
    secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    A = (1/4.0)*(secant**2/(math.tan((yaw1-yaw2)/2.0))**2)
    B = (A - R**2 - (xm**2+ym**2-x1**2-y1**2))/(2.0*y1 - 2.0*ym)
    k = (xm-x1)/(y1 - ym)
    criteria = (2.0*(k*B - k*y1 -x1))**2 - 4.0*(1+k**2)*((B-y1)**2 +x1**2-R**2)# test if it has real roots
    center_x1 = (-2.0*(k*B-k*y1-x1) + np.sqrt(criteria))/(2.0*(1+k**2)) 
    center_x2 = (-2.0*(k*B-k*y1-x1) - np.sqrt(criteria))/(2.0*(1+k**2)) 
    center_y1 = k*center_x1 + B
    center_y2 = k*center_x2 + B      
    if (y1-center_x1)/(x1-center_x1) == math.tan(yaw1):
        center_x = center_x1
        center_y = center_y1
    else:
        center_x = center_x2
        center_y = center_y2
    #self.yaw_center = (center_x, center_y)
    return (center_x, center_y), R

def __move_yaw__(self, delta_yaw):
    """
    Moves the yaw angle of the left fiber by the specified amount.
    """
    #calculate based on delta_yaw and self.yaw_center, self.yaw_radius
    x_delta = self.yaw_radius*(1-np.cos(delta_yaw))
    y_delta = self.yaw_radius*np.sin(delta_yaw)
    self.LEFT.MoveRelative6DOF(x_delta, y_delta, 0.0, yaw1=delta_yaw, pitch=0.0, roll=0.0)

def calculate_circle(x1,y1,x2,y2,x3,y3):   
    e = 2.0 * (x2 - x1)
    f = 2.0 * (y2 - y1)
    g = x2*x2 - x1*x1 + y2*y2 - y1*y1
    a = 2.0 * (x3 - x2)
    b = 2.0 * (y3 - y2)
    c = x3*x3 - x2*x2 + y3*y3 - y2*y2
    xc = (g*b - c*f) / (e*b - a*f)
    yc = (a*g - c*e) / (a*f - b*e)
    R = np.sqrt((xc-x1)**2.0+(yc-y1)**2.0)
    return (xc, yc, R)

def predict_dx_dy(x1, y1, dt, xc, yc, R):
    beta = np.arcsin((x1-xc)/R)
    dx = 2*R*np.sin(dt/2)*np.sin(np.pi/2-dt/2-beta)
    dy = 2*R*np.sin(dt/2)*np.cos(np.pi/2-dt/2-beta)
    return dx, dy
    
def circle_centre_residuals(circle, xi, yi, R):
    xc, yc = circle
    return np.sqrt((np.array(xi) - xc)**2 + (np.array(yi) - yc)**2) - R
    
def circle_radius(xi, yi, ui):
    #calculate circle radius based on coordinates of three points on circle
    #Arguments:
    #xi: x-ccordinates of 3 points on circle
    #yi: y-coordinates of 3 points on circle
    #ui: position of yaw actuator in the three points
    f = 2*np.pi/0.8/180
    R = 0
    N = 0
    for x in range(len(xi)-1):
        for y in range(x):
            k = np.sqrt((xi[x]-xi[y])**2 + (yi[x]-yi[y])**2)
            u = ui[x] - ui[y]
            t = u*f
            R += k/2/np.sin(t/2)
            N += 1
    return R/N

if __name__ == "__main__":
       
    #xi = [-9.216, -9.172, -9.166, -9.168, -9.233, -9.315]
    #yi = [4.599, 3.186, 2.440, 1.742, 0.2852, 6.0136]
    #ui = [5.85, 6.85, 7.35, 7.85, 8.85, 4.85]
    
    xi = [-9.216, -9.166, -9.168, -9.233, -9.315]
    yi = [4.599, 2.440, 1.742, 0.2852, 6.0136]
    ui = [5.85, 7.35, 7.85, 8.85, 4.85]
    
    #first we calculate radius:
    R = circle_radius(xi, yi, ui)
    print 'Radius guess: R=%.3fmm' % R
    #then fit circle to find centre:
    circle_guess = (xi[0]-R, yi[0])
    kd,cov = optimize.leastsq(circle_centre_residuals,circle_guess,args=(xi,yi,R))
    xc,yc = kd
    print 'Fitted circle: (xc=%.3f, yc=%.3f)' % (xc, yc)
    
    idx = 1
    du = ui[idx] - ui[0] #mm
    f = 2*np.pi/0.8/180
    dt = du*f
    dx, dy = predict_dx_dy(xi[0], yi[0], dt, xc, yc, R)
    print 'Predicted corrections for theta%0.2fmm: dx=%.3fmm, dy=%.3fmm' % (du, dx,dy)
    print 'Measured corrections: dx=%.3fmm, dy=%.3fmm' % (xi[idx]-xi[0],yi[idx]-yi[0])
    
    
    if 0:
        xc,yc,R = calculate_circle(xi[0], yi[0], xi[1], yi[1], xi[2], yi[2])
        print '(x-%.3f)^2+(y-%.3f)^2 = %.3f^2' % (xc, yc, R)

    
    
    #http://paulbourke.net/geometry/circlesphere/
    if 0:
        ma = (yi[1]-yi[0])/(xi[1]-xi[0])
        mb = (yi[2]-yi[1])/(xi[2]-xi[1])
        teller = ma*mb*(yi[0]-yi[2]) + mb*(xi[0]+xi[1]) + ma*(xi[1]+xi[2])
        x = teller/2.0/(mb-ma)
        y = -1/mb*(x - (xi[1]+xi[2])/2) + (yi[1]+yi[2])/2
        R = np.sqrt((x-xi[0])**2 + (y-yi[0])**2)
        print x, y, R
    
    #https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
    if 0:
        p,t = xi[0], yi[0]
        q,u = xi[1], yi[1]
        s,z = xi[2], yi[2]
        A=((u-t)*z^2+(-u^2+t^2-q^2+p^2)*z+t*u^2+(-t^2+s^2-p^2)*u+(q^2-s^2)*t)/((q-p)*z+(p-s)*u+(s-q)*t)
        B=-((q-p)*z^2+(p-s)*u^2+(s-q)*t^2+(q-p)*s^2+(p^2-q^2)*s+p*q^2-p^2*q)/((q-p)*z+(p-s)*u+(s-q)*t)
        C=-((p*u-q*t)*z^2+(-p*u^2+q*t^2-p*q^2+p^2*q)*z+s*t*u^2+(-s*t^2+p*s^2-p^2*s)*u+(q^2*s-q*s^2)*t)/((q-p)*z+(p-s)*u+(s-q)*t)    
    #https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
    if 0:
        x,y,z = xi[0]+1j*yi[0], xi[1]+1j*yi[1], xi[2]+1j*yi[2] 
        w = z-x
        w /= y-x
        c = (x-y)*(w-abs(w)**2)/2j/w.imag-x
        print '(x%+.3f)^2+(y%+.3f)^2 = %.3f^2' % (c.real, c.imag, abs(c+x))
        xc = -c.real
        yc = -c.imag
        R = abs(c+x)
    
    
    #To draw a circle in matplotlib, first you need to declare an artist
    circle = plt.Circle((xc,yc), R)
    #you then have to add that artist to an instance of axes:
    fig, ax = plt.subplots()
    ax.plot(xi, yi, '^')
    #ax.hold(True)
    ax.add_artist(circle)
    #then you can draw it safely.
    plt.show()
    
    
    

    
    
    
    
    
    