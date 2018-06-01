import numpy as np
R = 82.6285
factor = 25.1151



delta_y_new = R*np.sin(factor*(u2-u1))
delta_x_new = R*(1-np.cos(factor*(u2-u1)))