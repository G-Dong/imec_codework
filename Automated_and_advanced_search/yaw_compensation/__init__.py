"""
Version I: One step move center
rough function, only check the algorithm. needed to be generalized with real details.
NEED TO REMEMBER: deltax and one initial point.

parameters
deltax: the x length from rotation center to the fiber-end in the y-projection image
delta_thetaz: the rotated yaw angle
secant: The secant length between two points in the z-projection image

MAIN QUESTION:
1.The yaw angle range and direction.
2.Primary point of Descartes coordinate system 

"""
from __future__ import division
import numpy as np
#from numpy import float64
import math

class yaw_compensation:
    def find_R(self, point1, point2):
        """
        put parameters in the array in such an order: (x, y, yaw_angle)
        presume:
        1.array 1 as initial and array 2 as raw-changed, these two can be randomly chosen.
        2.the rotation point is not the primary point (0,0)
        3.thetaz is smaller than math.pi/4. if the rotation center lies on the right side of secant, we can make it as math.pi - yaw.
        """
 
        self.point1 = point1
        self.point2 = point2 
     
        secant = np.sqrt((self.point1[0]-self.point2[0])**2 + (self.point1[1]-self.point2[1])**2)
        self.R = (secant/2) / math.sin(np.absolute(self.point1[2]-self.point2[2])/2)
        
        #deltax = np.absolute(y2-y1)/math.tan(np.absolute(thetaz1-thetaz2)) + np.absolute(x2-x1)
        """
        latex format function: \Delta x = \frac{\mid y_2 - y_1\mid}{tan(\mid\theta_2 - \theta_1\mid)} + \mid x_2 - x_1\mid
        """
        return self.R
    def find_center(self, point1, point2):
        """
        The only function which needs the value of yaw angle of one point
        A and B are only two parameters in the calculation
        """
        self. point1 = point1
        self. point2 = point2
        x1 = self.point1[0]
        x2 = self.point2[0]
        y1 = self.point1[1]
        y2 = self.point2[1]
#  (self.xc, self.yc) = (0, 0)
        self.xm = (x1+x2)/2
        self.ym = (y1+y2)/2
        
        secant = np.sqrt((x1-x2)**2 + (y1-y2)**2)
        A = (1/4)*(secant**2/(math.tan((point1[2]-point2[2])/2))**2)
        B = (A - self.R**2 - (self.xm**2+self.ym**2-x1**2-y1**2))/(2*y1 - 2*self.ym)
        k = (self.xm-x1)/(y1 - self.ym)
        criteria = (2*(k*B - k*y1 -x1))**2 - 4*(1+k**2)*((B-y1)**2 +x1**2-self.R**2)
        print(criteria)
        xc1 = (-2*(k*B-k*y1-x1) + np.sqrt(criteria))/(2*(1+k**2)) 
        xc2 = (-2*(k*B-k*y1-x1) - np.sqrt(criteria))/(2*(1+k**2)) 
        yc1 = k*xc1 + B
        yc2 = k*xc2 + B
#  self.point = point
         
        self.center1 = (xc1, yc1)
        self.center2 = (xc2, yc2)
     
        return (self.center1, self.center2)
        
    def compensate(self, delta_thetaz, R):
        """
        array can only be [x, y]. yaw angle is not relative 
        """
        self.delta_thetaz = delta_thetaz
        #self.deltax = deltax
        array_new = np.zeros(2)

        secant = 2 * self.R * math.sin(self.delta_thetaz/2)
        
        array_new[0] = self.point1[0] + np.sqrt(secant*secant - (self.R*math.sin(self.delta_thetaz))*(self.R*math.sin(self.delta_thetaz)))
        array_new[1] = self.point1[1] - self.R*math.sin(self.delta_thetaz)
        return array_new

if __name__ == "__main__":
    """
    find deltax 
    """
    x_1 = 2
    y_1 = 0
    x_2 = 1 
    y_2 = np.sqrt(3)
    thetaz1 = 0 
    thetaz2 = math.pi/3
    point1 = [x_1, y_1, thetaz1]
    point2 = [x_2, y_2, thetaz2]
    point = [5, 1.414, math.pi/7]
    delta_thetaz = np.absolute(point[2]-point1[2])
    
    yc = yaw_compensation()
    
    R = yc.find_R(point1, point2)
    print R

    print yc.find_center(point1, point2)

    print yc.compensate(delta_thetaz, R)

    


