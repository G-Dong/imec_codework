import numpy as np
import math


def calculate_circle(x1,y1,x2,y2,x3,y3):   
    e = 2 * (x2 - x1)
    f = 2 * (y2 - y1)
    g = x2*x2 - x1*x1 + y2*y2 - y1*y1
    a = 2 * (x3 - x2)
    b = 2 * (y3 - y2)
    c = x3*x3 - x2*x2 + y3*y3 - y2*y2
    xc = (g*b - c*f) / (e*b - a*f)
    yc = (a*g - c*e) / (a*f - b*e)
    R = np.sqrt((xc-x1)**2+(yc-y1)**2)
    return (xc, yc, R)

if __name__ == "__main__":
    x1 = 1
    y1 = -0.5
    x2 = 0.5
    y2 = -1
    x3 = 1.5
    y3 = -1
    [xc, yc, R] = calculate_circle(x1,y1,x2,y2,x3,y3)
    print [xc, yc, R]
