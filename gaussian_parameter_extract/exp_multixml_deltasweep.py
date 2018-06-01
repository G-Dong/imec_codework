import pylab as plb
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
import numpy as np
from lmfit.models import GaussianModel, ConstantModel
from lxml import objectify as obj
#from Measurements.Analyses.ProcessFunctions.auxiliary import xml_to_array
import os
import xml.etree.ElementTree as ET 





# Define model function to be used to fit to the data above:
def readxml(inputxml):
    t = str.split(inputxml.text, ',')
    output_temp = []
    for number in t:
        output_temp.append(float(number))
    #print x_raw_temp
    output = np.array(output_temp)
    return output

def gauss(x, *p):
    A, mu, sigma, delta, voff = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2)) + A*np.exp(-(x-mu-delta)**2/(2.*sigma**2)) + voff

def gaussianfitting(x_raw, y_raw, wlbandw):
					#limit wavelength window
    peak = np.max(y_raw)
    idx = np.argwhere(y_raw > peak - 3.0)
    x_raw_fit = x_raw[idx][:,0]
    y_raw_fit = y_raw[idx][:,0]
    # p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
    p0 = np.array([20.0, 1550.0, 60.0, 20.0, 100.0])
    #bnd = np.array([5.0, 10.0, 20.0, 20.0, 1000.0])
    bnd = np.array([5.0, 10+wlbandw, 20.0, 20.0, 1000.0])
    coeff, var_matrix = curve_fit(gauss, x_raw_fit, y_raw_fit, p0=p0, method='trf', bounds=(p0-bnd, p0+bnd))
	# Get the fitted curve
    hist_fit = gauss(x_raw_fit, *coeff)
    return coeff[3]
	
if __name__ == "__main__":
    path = 'C://Users/dong87/Desktop/gaussian fitting/20180504pitchsweep/111518_pitchsweep_10degree_6_85'
    for filename in os.listdir(path):
        if filename.endswith('.xml'):
            fullname = os.path.join(path, filename)
            #read data from xml file
            with open(fullname, 'r') as f:
                ObjectData = obj.fromstring(f.read())
                dataxml = ObjectData.OpticalMeasurements.LossMeasurement.WaveguideLossMeasurement.PortLossMeasurement.MeasurementResult
                #x_raw = xml_to_array(dataxml.PortLossMeasurement.MeasurementResult[0].L)
                x_raw = dataxml.L
                # y_raw = xml_to_array(dataxml.PortLossMeasurement.MeasurementResult[0].IL) 
                y_raw = dataxml.IL
            x_raw = readxml(x_raw)
            y_raw = readxml(y_raw)
        #print y_raw_temp
        #print(x_raw)
            wlbandw = 400
            DELTA = np.zeros(wlbandw)
            for i in range(wlbandw):
                DELTA[i] = gaussianfitting(x_raw, y_raw, i)	
            print(DELTA)
            x_axis = np.zeros(wlbandw)
            for i in range(wlbandw):
                x_axis[i] = 10 + i
            figurename = fullname[fullname.find('/P151822'):-4]
            plt.plot(DELTA, label = 'trends of delta with the variance of allowed bandwidth' )
            plb.savefig(figurename)
            plt.show()
	