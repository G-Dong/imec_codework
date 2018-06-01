import numpy as np

"""
6 degree, given the labels as Gaussian distribution value.

total matrix size: 
"""
def generate_single_chronosome(freedom, num_data, range_plane, range_angle):
    """
    [X, Y, Z, theta_x, theta_y, theta_yaw]
    The plane resolution is 1 um, angle resolution is 0.1 degree,
    left limit = 0
    """
    ini_po = np.zeros((freedom))
#  index = np.zeros((1, freedom))
    plane_pool = np.zeros((range_plane))
    angle_pool = np.zeros((range_angle))
    """
    build up the raw data of plane freedom and angle freedom
    """
    
    for i in range(range_plane):
        plane_pool[i] = i - range_plane/2
    for i in range(range_angle):
        angle_pool[i] = i - range_angle/2   
        
    """
    generate random index to choose the value as initial_state
    """    
    for i in range (freedom/2):    
#         index[0, i] = np.random.rand(1, freedom)[0, i] * range_plane
#         index[0, i + freedom/2] = np.random.rand(1, freedom)[0, i + freedom/2] * range_angle
        ini_po[i] = np.random.choice(plane_pool, replace=True)
        ini_po[i + freedom/2] = np.random.choice(angle_pool, replace=True)
    """
    get index of plane pool is used in plane,
        index of angle pool is used in angle.
    
    for i in range(freedom/2):
        ini_po[0, i] = plane_pool[int(index[0, i]), 0]
        ini_po[0, i + freedom/2] = angle_pool[int(index[0, i + freedom/2]), 0] 
        """
    return(ini_po)

def Data_generation (freedom, num_data, range_plane, range_angle):
    """
    simulated data, initial data + gaussian as label
    """
    mu, sigma = 0, 1
    s =  np.random.normal(mu, sigma, (num_data,1))
    #print (s)
    data = np.zeros((num_data, freedom))
    for i in range (num_data):
        temp = generate_single_chronosome(freedom, num_data, range_plane, range_angle)
        for j in range (freedom):
            data[i, j] = temp[j]  
    data_lb = np.zeros((num_data, freedom + 1))
    for i in range (num_data):
        for j in range (freedom):
            data_lb[i, j] = data[i, j]
        np.round (data_lb)
    for i in range (num_data):
        data_lb[i, freedom] = s[i]* 50
    """
    round in order to get the int. 
    """
    return(np.round(data_lb), np.round(data_lb)[:, freedom ])

def initial_state(data, freedom,num_data):
    parent_0 = np.zeros(freedom)
    parent_1 = np.zeros(freedom)
    index = np.round(np.random.rand(1)*num_data)
    for i in range(freedom):
        parent_0[i] = data[int(index)-1, i] ## avoid overflow
    index = np.round(np.random.rand(1)*num_data)
    for i in range(freedom):
        parent_1[i] = data[int(index)-1, i]
    return (parent_0, parent_1)

def cross_over(freedom, parent_0, parent_1):
    """
    randomly decide which gene in the chorosomes to cross-over
    """
#     parent_0_prime = np.zeros((1, freedom))
#     parent_1_prime = np.zeros((1, freedom))
# for i in range(freedom):
    parent_0_prime = parent_0
    parent_1_prime = parent_1
    cross_index = int(np.round(np.random.rand(1,)*freedom))

    temp = parent_0_prime[cross_index-1]
    parent_0_prime[cross_index-1] = parent_1_prime[cross_index-1]
    parent_1_prime[cross_index-1] = temp
    
    return(parent_0_prime, parent_1_prime)
"""
This print has weried behavior
"""
def mutation(chromosome, sigma, num_mutation):
    chromosome_new = np.zeros(np.shape(chromosome))
    sigma_gauss = 1
    mu = 0
    for i in range(num_mutation):
        chromosome_new[i] = chromosome[i] + np.round(sigma*(sigma_gauss * np.random.randn(1) + mu)) # randn: normal distribution with(0,1)
        ##Gaussian distribution mu = mean = 0 sigma = variation = 1   
        print(np.round(sigma*(sigma_gauss * np.random.randn(1) + mu)))    

    return (chromosome_new)

def calculate_fitness(num_data, freedom, data, parent_0, parent_1):
    """
    This is definitely faaaaaake algorithm, but we need to simulate the optical power.
    
    We need the other algorithm to find the real fitness. Or the fitness should be given. 
    """
    fitness_0 = 0
    fitness_1 = 0
    for i in range (num_data):
        for j in range (freedom):
#             print (data[i, j], parent_0[j]) 
            if (data[i, j] - parent_0[j]).all == 0:
                fitness_0 = data[i, freedom]
            if (data[i, j] - parent_0[j]).all == 0:
                fitness_1 = data[i, freedom+1]
    return (fitness_0, fitness_1)

def replacement(data, parent_0, parent_1, child_0, child_1):
    freedom = 6
    p0 = calculate_fitness(num_data, freedom, data, parent_0, parent_1)[0]
    p1 = calculate_fitness(num_data, freedom, data, parent_0, parent_1)[1]
    c0 = calculate_fitness(num_data, freedom, data, child_0, child_1)[0]
    c1 = calculate_fitness(num_data, freedom, data, child_0, child_1)[1]
    """
    sort the finess and get the first two as new parents
    """
    sort = np.zeros((1, 4))
    sort[0, 0] = p0
    sort[0, 1] = p1
    sort[0, 2] = c0
    sort[0, 3] = c1
    for i in range(np.shape(sort)[1]):
        for j in range(np.shape(sort)[1]):
            if sort[0, j] < sort[0, i]:
                temp = sort[0, j] 
                sort[0, j] = sort[0, i]
                sort[0, i] = temp
        
        
        if sort[0, 1] == p0:
            for j in range(freedom):
                parent_1[j] = parent_0[j]
        if sort[0, 1] == c0:
            for j in range(freedom):
                parent_1[j] = child_0[j]
        if sort[0, 1] == c1:
            for j in range(freedom):
                parent_1[j] = child_1[j]  
        if sort[0, 0] == p1:
            for j in range(freedom):
                parent_0[j] = parent_1[j]
        if sort[0, 0] == c0:
            for j in range(freedom):
                parent_0[j] = child_0[j]
        if sort[0, 0] == c1:
            for j in range(freedom):
                parent_0[j] = child_1[j]   
    
    return(parent_0, parent_1, sort)

def find_biggest_gaussion(sort):
    for i in range(np.shape(sort)[0]):
        for j in range(np.shape(sort)[0]):
            if sort[j] < sort[i]:
                temp = sort[j] 
                sort[j] = sort[i]
                sort[i] = temp

    return (sort)
# print(a, b)

if __name__ == "__main__":

    freedom  = 6
    num_data = 1000
    range_plane = 100
    range_angle = 50
    sigma = 5
    (data, s) = Data_generation (freedom, num_data, range_plane, range_angle)
    Gaussian_max = find_biggest_gaussion(s)
    #print (Gaussian_max)
    #print (data)
    parent_0 = initial_state(data, freedom, num_data)[0]
    parent_1 = initial_state(data, freedom, num_data)[1]
    
    fitness = np.zeros((1, 4))
    while not fitness[0, 0] == -206:
        parent_0 = initial_state(data, freedom, num_data)[0]
        parent_1 = initial_state(data, freedom, num_data)[1]
    #print (parent_0)
        (child_0, child_1) = cross_over(freedom, parent_0, parent_1)
        child_0 = mutation(child_0, sigma, freedom)
# print(np.shape(child_0))
        child_1 = mutation(child_1, sigma, freedom)
        (parent_0, parent_1, fitness) = replacement(data, parent_0, parent_1, child_0, child_1)
        print fitness
        print (parent_0, parent_1)
    
#     print (data)
#print (initial_state(6, 100, 100, 50))
    a = Data_generation(6, 100, 100, 50)
    b = Data_generation(6, 100, 100, 50)

# print (a, b)
# print(cross_over(6, a, b))
# print(mutation(cross_over(6, a, b)[0], 10, 6))


