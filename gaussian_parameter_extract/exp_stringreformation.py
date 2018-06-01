import numpy as np
# unit mm
r = 33# unit = mm
x = np.array([0.01,
0.02,
0.03,
0.04,
0.05,
0.06,
0.07,
0.08,
0.09,
0.1,
0.11,
0.12,
0.13,
0.14,
0.15,
0.16
])
y = 0
for i in range(len(x)-1):
    y = 1000*r*(x[i] - np.sin(x[i]))## in micro
    print y