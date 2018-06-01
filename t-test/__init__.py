"""
This is the 2-sample t-test which is used for compare certain feature's influence. No module and no matrix version. Used in SPDZ2 2 party
communication system
"""
program.bit_length = 80
print"program.bit_length: ", program.bit_length
program.security = 40# The value in GC = 2^40
import sys
sys.setrecursionlimit(10000000)

def load_int(X, num):
    X_amp = Array((num,sfix))
    for i in range(num):
        d = sfix(); d.load_int(Y[i])
        Y_amp[i] = d
    return Y_amp

def get_real_data(X_amp, num, amp_ratio):
    X =Array(num, sfix)
    for i in range(n):
        X[i] = X_amp[i]/amp_ratio
    return X


def mean(x, num_data):
    """
    num_data = np.shape(x)
    """
    sum = sfix(0)
    mean = sfix(0)
    for i in range(num_data):
        sum = sum + x[i]
    mean = sum/num_data
    return mean 
def variance(x, num_data):
    """
    standard deviation
    """
    sum = sfix(0)
    mean = sfix(0)
    std = sfix(0)
    mean = mean(x, num_data)
    for i in range(num_data):
        sum = sum + (x[i] - mean)^2
    std = (sum/num_data)^0.5
    return std
def df(type, num_1, num_2, std_1, std_2):
    """
    degree of freedom, only needed when variance of two-party are un-equal
    type should distinguish the string 'equal_variance'
    """
    df = sfix(0)
    if type == 'equal_variance':
        df = (num_1 + num_2) - 2
    else:
        df = (std_1^2/num_1 + std_2^2/num_2)^2/(std_1^2/num_1)^2/((num_1 - 1) + (std_2^2/num_2)^2/(num_2 - 1))
    return df
    
def gett(type, group1, group2, num_1, num_2):
    if type == 'equal_variance':
        s_p = (((num_1 - 1)*variance(group1, num_1) + (num_2 - 1)*variance(group2, num_2))/(num_1+num_2-2))^0.5
        t = (mean(group1, num_1) - mean(group2, num_2))/(s_p*(1/num_1 + 1/num_2)^0.5)
    else:
        s_delta = (std(group1, num_1)^2/num1 + std(group2, num_2)^2/nun_2)
        t = (mean(group1, num_1) - mena(group2, num_2))/s_delta
    return t

def significant(t, p_value):
    if t > p-value:
        sig = 'True'
    else: 
        sig = 'False'
    return sig
        
if __name__ == "__main__":
    n = rows
    m = columns
    prod = n*m
    amp_ratio = 10000
    
    X_int = Array(num, sint)
    Y_int = Array(n, sint)
    for i in range(prod):
        X_1[i] = sint.get_raw_input_from(1)
        x_2[i] = sint.get_raw_input_from(2)
    """
    for i in range(n):
        y = sint.gent_raw_input+from(0)
    """
    
