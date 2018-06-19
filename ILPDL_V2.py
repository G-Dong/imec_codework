"""Module for semi-automatic wafer-level IL/PDL measurements using fiber arrays
"""
#TODO: in __setup_base__, method select_laser: if any(x in laser.idn for x in ['81608A', ....]
#TODO: add O band laser in __setup_ILPDL__ method init_instruments
#in ILPDLSetup: in __menu__: check how to disconnect left/right XPS controller depending on setup type (obsolete code copied from local working copy)
#in ILPDLSetup: declare class attributes in __init__ (e.g. tempstorage, R_rotation_rad etc 
import os
import glob
import time
import win32com.client
from time import localtime
from time import asctime
#from time import strptime
import socket
import math
import sys
import msvcrt
import warnings
import numpy as np
import matplotlib.pyplot as plt
#from pymeasure.util.png import png
from MeasurementSetups.arraysetup import ArraySetup
from pymeasure.instruments.Keysight.IL_PDL import ILPDL
from pymeasure.auto.full.core.analog_source import analog_source_AgilentPM81634B
from pymeasure.auto.full.core.analog_source import analog_source_AgilentPM81636B
from pymeasure.instruments.Agilent.tunable_laser import Agilent8164AB
from pymeasure.instruments.Newport.AutomaticSetup import ImecAutomaticSetup, Imec300AutomaticSetup
from pymeasure.instruments.Newport.AutomaticSetup import ChuckTravelRangeError
from MeasurementSetups.DEMO import Device
from MeasurementSetups.DEMO import DeviceCatalog
from MeasurementSetups.DEMO import MeasurementSetting
from MeasurementSetups.DEMO import FibreAlignmentSetting
from MeasurementSetups.DEMO import MeasurementResult
from MeasurementSetups.DEMO import LossMeasurementSetting
from MeasurementSetups.DEMO import LossMeasurementResult
from lxml import etree
from lxml.objectify import E as Efactory
from MeasurementSetups.DEMO import __setup_base__
from TestPlanDefinitions.TestPlanDefinitions import MeasurementTree, PortCombo, TestSite, DUT, CouplerInfo, AlignmentResult, ToolInfo, OIODesign
from util.Coordinates import XY
from util.Coordinates import XYZ
from pymeasure.auto.imec.helpers.Coordinates import LXY, RXY, PXY
from pymeasure.auto.imec.helpers.Design2XML import read_designfile
from pymeasure.util.AuxiliaryFunctions import  ConvertDimensionlesslist2UnitList
from pymeasure.util.AuxiliaryFunctions import SearchObjectListForFieldValue
# from pymeasure.util.AuxiliaryFunctions import ConvertDimensionedList2DimensionlessList
from pymeasure.util.AuxiliaryFunctions import ConvertList2StringWithoutUnits
# from pymeasure.util.AuxiliaryFunctions import ConvertCommaSeparatedString2list
# from pymeasure.util.AuxiliaryFunctions import CheckListType
from pymeasure.util.AuxiliaryFunctions import ConvertList2CommaSeparatedString
from pymeasure.util.AuxiliaryFunctions import SeparateTupleList
from pymeasure.units.unit import DBM
from pymeasure.units.unit import MICROMETER 
from pymeasure.units.unit import NANOMETER
from pymeasure.units.unit import MICROMETERPERSECOND
from pymeasure.units.unit import MILLISECOND
from pymeasure.units.unit import MILLIMETER
from pymeasure.units.unit import VOLT
from pymeasure.util.result_folder import result_folder2
from pymeasure.instruments.Cascade.PA300 import ResponseError
from pymeasure.instruments.PhoenixPhotonics.EPC import NoHeaterCalibrationData
from pymeasure.instruments.PhoenixPhotonics.PhoenixDLL import ErrorWithCode
from pymeasure.instruments.exceptions import InstrumentValueError
from pymeasure.util.mathtools import FindPolyFittedMax
try:
    from pymeasure.auto.imec.core.__start_pos__ import __get_start_pos__
except ImportError:
    pass
try:
    from pymeasure.auto.imec.core.__wafer_alignment__ import __get_waferalignmentinfo__
except ImportError:
    pass
from pymeasure.auto.imec.core.alignment import align_spiral
from util.threadmethods import FiniteWaitForKBInput

from MeasurementSetups.ILPDL.yaw import yaw_compensation, __calibrate_yaw_factor__, __calibrate_yaw__, __move_yaw__
from pymeasure.auto.imec.users.dong87.FGC_svr_pointsfitting_V2 import xypoints_fitting
from scipy import asarray as ar
def Property(func):
    kwargs = func(None)
    ks = kwargs.keys()
    if not 'fset' in ks:
        kwargs['fset'] = None
    if not 'fdel' in ks:
        kwargs['fdel'] = None  
    return property(fget=kwargs['fget'], fset=kwargs['fset'], 
                    fdel=kwargs['fdel'], doc=kwargs['doc'])

def __nameerror__(objectclass, propertyname, expectedtype):
    raise NameError(propertyname + " must be given as " + expectedtype + " in object " + objectclass.__name__ + "!")

class __setup_ILPDL__(__setup_base__):
    default_laser_power = None
    __align_wavelength__ = 1550*NANOMETER
    
    def __init__(self, **kwargs):
        '''Initialize the object'''
        self.laser = None
        self.OpticalCalfile = None
        self.__init_instruments__(initparents=False)

    def __init_instruments__(self, initparents=True):
        print 'Trying to connect to mainframe...',
        try:
            self.mainframe = Agilent8164AB( name = "AGILENT 8164AB Lightwave Measurement System", address = "GPIB::21" )
            self.mainframe2 = Agilent8164AB( name = "AGILENT 8164AB Lightwave Measurement System", address = "GPIB::20" )
            self.PM = self.sensor1 = self.mainframe.PM81634B( slot = 1 )      #'digital' readout of the power sensor
            self.PM.write("SENS1:CHAN1:POW:UNIT 0")     
            self.analog_source = analog_source_AgilentPM81634B( self.PM )     #handles the analog output of the power sensor for alignment purposes   
            self.sensor1.range_auto = False
            self.sensor1.range = -10 * DBM
            # flush old results
            self.sensor1.get_function_result()
            self.sensor1.write("*CLR")
            
            self.PM2 = self.sensor2 = self.mainframe.PM81636B( slot = 4 )      #'digital' readout of the power sensor
            self.PM2.write("SENS4:CHAN1:POW:UNIT 0")     
            self.analog_source2 = analog_source_AgilentPM81636B( self.PM2 )     #handles the analog output of the power sensor for alignment purposes   
            self.sensor2.range_auto = False
            self.sensor2.range = -10 * DBM
            # flush old results
            self.sensor2.get_function_result()
            self.sensor2.write("*CLR")
            
            self.switch = self.mainframe.SW81591B(2)
            self.switch.OutputPort = 1
            print 'OK - %s at %s' % (self.mainframe.identification, self.mainframe.address)
        except Exception, e:
            print e.message
            print "Failed."
            self.mainframe = None
        #connect to the O-band tunable laser:
        try:
            self.lasero = self.mainframe2.TL81602A( slot = 0 )
            self.lasero.get_lambda_logging()
            self.lasero.write(":SOUR0:POW:UNIT 0")
        except:
            print "Failed."
            self.lasero = None
        #connect to the CL-band tunable laser:
        try:
            self.laserc = self.mainframe.TL81608A( slot = 0 )
            self.laserc.get_lambda_logging()
            self.laserc.write(":SOUR0:POW:UNIT 0")
            self.laserc.write('sour0:wav:swe:stat 0') 
        except:
            print "Failed."
            self.laserc = None
        #select one of the connected lasers:
        if (self.laserc is None) and (self.lasero is None):
            msg = ("Agilent 8164B mainframe: at least one tunable laser ",
                   "needs to be installed!")
            raise Exception(''.join(x for x in msg))
        elif self.laserc is None:
            self.laser = self.lasero
            self.__align_wavelength__ = 1310*NANOMETER
        else:
            self.laser = self.laserc
            self.__align_wavelength__ = 1550*NANOMETER
        #Connect to the IL/PDL engine:
        #self.EngineMgr = win32com.client.Dispatch("AgServerILPDL.EngineMgr")
        #self.Engine = self.EngineMgr.NewEngine()
        #self.Engine.Activate()
        self.ILPDL = ILPDL()
        #EPC
        self.epc = None
        if initparents:
            super(__setup_ILPDL__, self).__init_instruments__(setup='ILPDL')
    
    def __prealign__(self):
        if self.__align_wavelength__ != None:
            laser_found = self.select_laser(self.__align_wavelength__)
            if not laser_found:
                msg = ("No tunable laser for %dnm " % self.__align_wavelength__,
                       "is installed!")
                raise Exception(''.join(x for x in msg))
            self.laser.wavelength = self.__align_wavelength__
            if (1260 <= self.__align_wavelength__.get_value(NANOMETER) <= 1375) and (not self.lasero is None):
                self.laser.sweep_speed = 8.0*NANOMETER # 50*NANOMETER #set default sweep speed to 100nm/s
            elif (1505 <= self.__align_wavelength__.get_value(NANOMETER) <= 1630) and (not self.laserc is None):
                self.laser.sweep_speed = 50*NANOMETER #set default sweep speed to 100nm/s
            # laser needs some time to set WL
#             print self.laser.wavelength
            # laser needs some time to set WL
            time.sleep(0.25)
            print self.laser.wavelength
    
    def __laser_available__(self, wavelength):
        '''check if laser for given wavelength is available
        '''
        if not self.lasero is None:
            o1 = self.lasero.__wavelength_min__.get_value(NANOMETER)
            o2 = self.lasero.__wavelength_max__.get_value(NANOMETER)
        if not self.laserc is None:
            c1 = self.laserc.__wavelength_min__.get_value(NANOMETER)
            c2 = self.laserc.__wavelength_max__.get_value(NANOMETER)
        if (not self.lasero is None) and (o1 <= wavelength.get_value(NANOMETER) <= o2):
            return True
        elif (not self.laserc is None) and (c1 <= wavelength.get_value(NANOMETER) <= c2):
            return True
        else:
            return False
        
    def continuous_sweep(self,
                         start_wavelength,
                         scan_range,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=None,
                         preprint = '    +' ,
                         PM = None):
        #if wavelength range spans across O and C band, we will perform
        #two separate sweeps and stitch the results:
        if not self.lasero is None:
            lo1 = self.lasero.__wavelength_min__
            lo2 = self.lasero.__wavelength_max__
            self.lasero.write(":SOUR0:POW:UNIT 0")
        else:
            lo1 = None
            lo2 = None
#         l1 = lo1
#         l2 = lo2
        if not self.laserc is None:
            lc1 = self.laserc.__wavelength_min__
            lc2 = self.laserc.__wavelength_max__
            self.laserc.write(":SOUR0:POW:UNIT 0")
#             if l1 is None:
#                 l1 = lc1
#             l2 = lc2
        else:
            lc1 = None
            lc2 = None
        stop_wavelength = start_wavelength + scan_range
        startwl = start_wavelength.get_value(NANOMETER)
        stopwl = startwl + scan_range.get_value(NANOMETER)
        start_found = self.__laser_available__(start_wavelength)
        stop_found = self.__laser_available__(start_wavelength + scan_range)
        #laser_found = self.select_laser(start_wavelength)
        if not start_found:
            msg = ("The appropriate laser for measurements at ",
                   "%dnm " % startwl,
                   "is not connected!")
            raise Exception(''.join(x for x in msg))
        if not stop_found:
            msg = ("The appropriate laser for measurements up to ",
                   "%dnm " % stopwl,
                   "is not connected!")
            raise Exception(''.join(x for x in msg))
        if PM is None:
            self.PM.write("SENS1:CHAN1:POW:UNIT 0") 
        else:
            PM.write("SENS1:CHAN1:POW:UNIT 0")
        if lc1 is None:
            #C-band laser is not connected, therefore the sweep must be
            #within O-band (otherwise exception would have occurred above),
            #and O-band laser is connected
            self.laser.laser_active = 'ON'
            return self.agilent_continuous_sweep(start_wavelength,
                         scan_range,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint,
                         PM=PM)
        elif lo1 is None:
            #O-band laser is not connected, therefore the sweep must be
            #within C-band (otherwise exception would have occurred above),
            #and C-band laser is connected
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            return self.agilent_continuous_sweep(start_wavelength,
                         scan_range,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint, 
                         PM=PM)
        elif start_wavelength >= lc1:
            #both lasers are connected, sweep is in C band:
            self.select_laser(start_wavelength)
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            return self.agilent_continuous_sweep(start_wavelength,
                         scan_range,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint,
                         PM=PM)
        elif stop_wavelength <= lo2:
            #both lasers are connected, sweep is in O band:
            self.select_laser(start_wavelength)
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            return self.agilent_continuous_sweep(start_wavelength,
                         scan_range,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint,
                         PM=PM)
        else:
            #both lasers are connected and sweep spans both bands:
            self.select_laser(start_wavelength)
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            wlo, pwro, swppwro = self.agilent_continuous_sweep(start_wavelength,
                         lo2-start_wavelength,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint,
                         PM=PM)
            self.select_laser(lc1)
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            wlc, pwrc, swppwrc = self.agilent_continuous_sweep(lc1,
                         stop_wavelength-lc1,
                         resolution_wavelength,
                         averaging_time,
                         sensor_range,
                         laser_power=laser_power,
                         preprint=preprint,
                         PM=PM)
            wl = np.hstack((wlo, wlc))
            pwr = pwro + pwrc
            return wl, pwr, [swppwro, swppwrc] 
        
    def select_laser(self, wavelength):
        '''Select one of the lasers, based on a given wavelength.
        
        Args:
        -wavelength (float): wavelength for which to select the appropriate 
            laser.
        
        Returns:
        -laser_found (bool): True if a suitable laser was found, False 
            otherwise.
        '''
        print self.laser.idn, wavelength
        if (1260 <= wavelength.get_value(NANOMETER) <= 1375) and (not self.lasero is None):
            if (not self.laser is None) and any(x in self.laser.idn for x in ['81690A', '81608A']):
                #the c-band laser was selected: make sure it is switched off
                #and then select the O-band laser
                print 'switching to O-band laser', self.laser.idn, wavelength
                self.laser.laser_active = 'OFF'
                self.laser = self.lasero
            self.laser.wavelength = wavelength
            return True
        elif (1505 <= wavelength.get_value(NANOMETER) <= 1630) and (not self.laserc is None):
            if (not self.laser is None) and any(x in self.laser.idn for x in ['81600B', '81602A']):
                #the O-band laser was selected: make sure it is switched off
                #and then select the C-band laser
                print 'switching to C-band laser', self.laser.idn, wavelength
                self.laser.laser_active = 'OFF'
                self.laser = self.laserc
            self.laser.wavelength = wavelength
            return True
        else:
            return False
            
class ILPDLSetup(ArraySetup, __setup_ILPDL__):
    """Wafer-level IL/PDL measurement class
    """
    
    def __init__(self, **kwargs):
        self.hostname = socket.gethostname()
        self.tempstorage =  dict()
        self.tempstorage['currentdevice'] = 'device'
        self.tempstorage['currenttestsite'] = 'site'
        self.tempstorage['leftgrating_name'] = 'L'
        self.tempstorage['rightgrating_name'] ='R'
        self.tempstorage['probepad_name'] = 'P'
        self.tempstorage['left_trajectories']=0
        self.tempstorage['left_alignments']=0
        self.tempstorage['right_trajectories']=0
        self.tempstorage['right_alignments']=0
        self.tempstorage['chuck_movements']=0
        self.tempstorage['left_movements']=0
        self.tempstorage['right_movements']=0
        self.tempstorage['wavelength_sweeps']=0
        self.tempstorage['l_start'] = 1510*NANOMETER
        self.tempstorage['l_span'] = 90*NANOMETER
        self.tempstorage['l_step'] = 0.1*NANOMETER
        self.tempstorage['l_power'] = 6.0*DBM
        self.tempstorage['l_powerrange'] = -10*DBM
        self.tempstorage['currentdevice'] = 'None'
        self.tempstorage['currenttestsite'] = 'None'
        self.tempstorage['comment'] = ''
        self.menutimeout = 900 #timeout in seconds - program will exit after inactivity
        super(ILPDLSetup, self).__init__(**kwargs)
        self.MeasurementSettings = self.define_settings()
        self.MeasurementTree = self.define_measurementtree()
        self.MeasurementTree.AlignMethod == 'spiral'
        self.MeasurementTree.StorageFolder = os.sep*2 + self.hostname + os.sep + 'OIO'
        self.__gather_toolinfo__()
        self.__init_devicecatalog__()
        self.A.set_arms_speed(0.1)
        self.__align_wavelength__ = self.MeasurementTree.DefaultWavelength
        self.__prealign__()
        self.sensor1.wavelength = self.MeasurementTree.DefaultWavelength
        self.L_rotation_rad = self.MeasurementTree.Wafer.RotationAngle #-0.0008 #StepperSettings.RotationAngle) # self.waferInfo.RotationAngle) #*np.pi/180.0 #-(self.rotation) * math.pi / 180.0 #-(self.rotation-0.07) * math.pi / 180.0
        if self.A.__class__ is ImecAutomaticSetup:
            self.R_rotation_rad = self.MeasurementTree.Wafer.RotationAngle + 0.0085 +0.0025#-0.006 #StepperSettings.RotationAngle) #self.waferInfo.RotationAngle) #*np.pi/180.0 #-(self.rotation) * math.pi / 180.0
        elif self.A.__class__ is Imec300AutomaticSetup:
            self.R_rotation_rad = self.MeasurementTree.Wafer.RotationAngle
        self.yaw_radius = None
        self.yaw_center = None
        self.yaw_factor = 1.0
        self.MeasurementTree.StorageFolder = os.sep*2 + self.hostname + os.sep + 'OIO'
        #load the project file on the PA300 prober:
        if self.A.__class__ is Imec300AutomaticSetup:
            self.A.TABLE.OpenProject(r'C:\Documents and Settings\Cascade\My Documents'+os.sep+self.MeasurementTree.Mask + '.spp')
        #self.__perform_sweep__()
        that_folder = r'\\winbe\oiodata\01_data\Logs\calibrations'
        that_folder += os.sep + self.MeasurementTree.Setup + os.sep + 'setuploss'
        self.MeasurementTree.Calibration = 'meter1.csv'
        self.OpticalCalfile = that_folder + os.sep + 'meter1.csv'
        self.__menu__(True)
        
        #self.run()
        
        
    def __menu__(self, initial_choice, **kwargs): 
        #print initial_choice
        commands = [ 
            self.__load_sample__, 
            self.__array_navigator__,
            self.__laser_settings__, 
            self.__set_startpos__,
            self.__return_to_startpos__,
            self.run,
            self.__perform_sweep__,
            self.__switch_light__,
            self.__Agilent8164B_calibration__,
            self.__calibrate_yaw_factor__
        ]
        prefix = "                  "
        while 1:
            print r"""
                  ( \
                  \ \
                  / /                |\\
                  / /     .-`````-.   / ^`-.
                  \ \    /         \_/  {|} `o
                  \ \  /   .---.   \\ _  ,--'
                  \ \/   /     \,  \( `^^^
                  \   \/\      (\  )
                  \   ) \     ) \ \
                  ) /__ \__  ) (\ \___
                  (___)))__))(__))(__)))"""
            print prefix, "======================================================"
            print prefix, "0) load sample"
            print prefix, "1) wafer navigator"
            print prefix, "2) set laser wavelength, power, output state"
            print prefix, "3) set current as start_pos"
            print prefix, "4) return to start_pos"
            print prefix, "5) run measurement"
            print prefix, "6) perform sweep (experimental)"
            print prefix, "7) toggle the microscope light"
            print prefix, "8) calibrate setup loss" 
            print prefix, "9) calibrate yaw angle"
            print
            print prefix, "q) quit\n"
            #self.__perform_sweep__()
            try:
                q = FiniteWaitForKBInput(lambda: raw_input("Your choice: "), self.menutimeout).result
                if q is None:
                    #no response received before timeout, i.e. exit loop
                    if self.A.__class__ == ImecAutomaticSetup:
                        self.A.TABLE.Light = True
                    print 'Exiting.'
                    self.A.Dispose()
                    break
                elif q == 'q':
                    if self.A.__class__ == ImecAutomaticSetup: 
                        self.A.TABLE.Light = True
                    self.A.__close_ftp__()
                    self.A.LEFT.disconnect()
                    self.A.RIGHT.disconnect()
                    try:
                        self.A.XPS.disconnect()
                    except:
                        pass
                    try:
                        self.A.leftXPS.disconnect()
                        self.A.rightXPS.disconnect()
                    except:
                        pass
                    del self.A
                    break
                i = int(q)
                command = commands[i]
            except ValueError:
                continue
            except IndexError:
                continue
            command()
    
    def __calibrate_yaw_factor__(self):
        """Guide user through procedure to calibrate yaw compensation
        """
        #read left fiber coordinates:
        Lx1, Ly1, Lz1 = self.A.LEFT.PositionCurrentGet()
        m = xypoints_fitting() #will use this model to train x coordinate
        #guide user through three points
        trained_yaw = [5.0, 7.0 ,9.0]
        trained_x = []
        trained_y = []
        m.training_x = trained_yaw
        for i, yaw in enumerate(trained_yaw):
            msg = ("The yaw angle of the left fiber will now be adjusted ",
                   "to %2.3gmm.\n" % yaw)
            print ''.join(x for x in msg)
            #insert code to adjust yaw
            self.A.LEFT.MoveYawAbsolute(yaw)
            msg = ("Use the keyboard to move the left fibre back and",
                   "align it to the grating.  Press esc when done.")
            print ''.join(x for x in msg)
            self.__array_navigator__()
            #insert code to read the x, y coordinates of left fiber
            xleft, yleft, _ = self.A.LEFT.PositionCurrentGet()
            trained_x.append(xleft)
            trained_y.append(yleft)
        m.training_x = trained_x
        m.training_y = trained_y
        m.vali_u = trained_yaw
        #m.FitModel()
        predicted_x, predicted_y = m.SVRegresion()
        xerror = m.calculate_error(trained_x, predicted_x)
        yerror = m.calculate_error(trained_y, predicted_y)
        print 'Sum of absolute errors in', len(trained_yaw),'points:', xerror+yerror, 'um'
        #now ask for '4' additional points
        extra_yaw = [6.0, 8.0, 6.5, 7.5]
        for i, yaw in enumerate(extra_yaw):
            trained_yaw.append(yaw)
            msg = ("The yaw angle of the left fiber will now be adjusted ",
                   "to %2.3gmm.\n" % yaw)
            print ''.join(x for x in msg)
            #insert code to adjust yaw
            self.A.LEFT.MoveYawAbsolute(yaw)
            #now predict x and y:
            predx = mx.Evaluate(yaw)
            predy = my.Evaluate(yaw)
            #insert code to adjust x and y of left fiber
            self.A.move_abs_L(predx, predy, Lz1)
            #then let user do fine tuning
            msg = ("Use the keyboard to move the left fibre back and",
                   "align it to the grating.  Press esc when done.")
            print ''.join(x for x in msg)
            self.__array_navigator__()
            #insert code to read the x, y coordinates of left fiber
            xleft, yleft, _ = self.A.LEFT.PositionCurrentGet()
            trained_x.append(xleft)
            trained_y.append(yleft)
            m.training_u = trained_yaw
            m.training_x = trained_x
            m.training_y = trained_y
            m.vali_u = trained_yaw
            #m.FitModel()
            predicted_x, predicted_y = m.SVRegresion( )
            xerror = m.calculate_error(trained_x, predicted_x)
            yerror = m.calculate_error(trained_y, predicted_y)
            print 'Sum of absolute errors in', len(trained_yaw),'points:', xerror+yerror, 'um'
        #show users the error, if ok then use this model, if too big we train new set
        m.Prune()
        #final model
        m.FitModel()
        
    
    def __calibrate_yaw__(self):
        self.yaw_center, self.yaw_radius = __calibrate_yaw__(self)
        print self.yaw_center, self.yaw_radius
    
    def __move_yaw__(self, delta_yaw):
        """
        Moves the yaw angle of the left fiber by the specified amount.
        """
        #calculate based on delta_yaw and self.yaw_center, self.yaw_radius
        x_delta = self.yaw_radius*(1-np.cos(delta_yaw*self.yaw_factor))
        y_delta = self.yaw_radius*np.sin(delta_yaw*self.yaw_factor)
        self.LEFT.MoveRelative6DOF(x_delta, y_delta, 0.0, yaw1=delta_yaw, pitch=0.0, roll=0.0)
    
    def __Agilent8164B_calibration__(self, reset=False):
        '''Calibrate agilent mainframe
        
        Args:
        -reset (bool): if True, the calibration of the mainframe gets reset 
            (i.e. no calibration file is used) and no new calibration is 
            performed. 
            If False, a wavelength sweep between the min and max wavelength of 
            the laser source is performed. This sweep is then stored in a csv 
            file and the data are used as a reference when performing a 
            continuous sweep. Default: False.
        '''
        if (not hasattr(self, 'mainframe')) or \
                (not self.mainframe.__class__ == Agilent8164AB):
            msg = ("This calibration procedure only applies to measurement ",
                   "setups that comprise an Agilent8164B mainframe.")
            print ''.join(x for x in msg)
            return
        if not reset:
            #calibrate both O and C band lasers:
            msg = ("Connect a fiber patchcord bypassing the measurement ",
                   "pigtails.")
            print ''.join(x for x in msg)
            usr_keys = raw_input("Press 'y' to continue or any other key to abort.")
            if usr_keys == 'y':      
                l1 = None
                l2 = None      
#                 if not self.lasero is None:
#                     l1 = self.lasero.__wavelength_min__
#                     print 'O-band min wl:', l1
#                     l2 = self.lasero.__wavelength_max__
#                     print 'O-band max wl:', l2
                if not self.laserc is None:
                    if l1 is None:
                        l1 = self.laserc.__wavelength_min__
                        print 'C-band min wl:', l1
                    l2 = self.laserc.__wavelength_max__
                    print 'C-band max wl:', l2
                #perform wavelength sweeps
                data = None
                if not l1 is None:
                    span = (l2.get_value(NANOMETER) - l1.get_value(NANOMETER))*NANOMETER
                    #make sure we do not apply any compensation to the reference measurement
                    self.OpticalCalfile = None
                    sweep_pwr = 6.0*DBM
                    lun, ilun, sweep_power = self.continuous_sweep(l1, span,
                                     0.5*NANOMETER,
                                     1.0*MILLISECOND,
                                     10*DBM,
                                     laser_power=sweep_pwr,
                                     PM=self.PM)
                    nbp = len(lun)
                    #store the measured data to a calibration file and enable compensation
                    data = np.hstack((np.reshape(lun[:nbp], [nbp,1]), 
                                      np.reshape(ilun[:nbp], [nbp,1])))
                if 0:
                    #determine which laser source to calibrate:
                    if self.MeasurementTree.DefaultWavelength.get_value(NANOMETER) < 1505:
                        band = 'O'
                    else:
                        band = 'C'
                    if reset == False:
                        self.laser.laser_active = 'ON'
                        msg = ("Connect a fiber patchcord bypassing the measurement ",
                               "pigtails.")
                        print ''.join(x for x in msg)
                        usr_keys = raw_input("Press 'y' to continue or any other key to abort.")
                        if usr_keys == 'y':
                            if (band == 'O') and (self.lasero is None):
                                msg = ("The O-band tunable laser must be installed ",
                                       "in the mainframe!")
                                raise Exception(''.join(x for x in msg)) 
                            if (band == 'C') and (self.laserc is None):
                                msg = ("The C-band tunable laser must be installed ",
                                       "in the mainframe!")
                                raise Exception(''.join(x for x in msg))
                            if band == 'O':
                                l1 = self.lasero.__wavelength_min__
                                l2 = self.lasero.__wavelength_max__
                            elif band == 'C':
                                l1 = self.laserc.__wavelength_min__
                                l2 = self.laserc.__wavelength_max__
                            #perform wavelength sweeps
                            span = (l2.get_value(NANOMETER) - l1.get_value(NANOMETER))*NANOMETER
                            #make sure we do not apply any compensation to the reference measurement
                            self.OpticalCalfile = None
                            sweep_pwr = 6.0*DBM
                            lun, ilun, sweep_power = self.continuous_sweep(l1, span,
                                             0.5*NANOMETER,
                                             0.025*MILLISECOND,
                                             10*DBM,
                                             laser_power=sweep_pwr,
                                             PM=self.PM)
                            nbp = len(lun)
                            #store the measured data to a calibration file and enable compensation
                            data = np.hstack((np.reshape(lun[:nbp], [nbp,1]), 
                                              np.reshape(ilun[:nbp], [nbp,1])))
                if not data is None:
                    #print data
                    #at least one of the lasers has been calibrated
                    that_folder = r'\\winbe\oiodata\01_data\Logs\calibrations'
                    that_folder += os.sep + self.MeasurementTree.Setup + os.sep + 'setuploss'
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    that_file = '%s_calibration_agilent8164B.csv' % timestamp
                    localcalfile = 'agilent8164Bcal.csv'
                    headerstr = ("Start wavelength [nm],%d\n" % l1.get_value(NANOMETER),
                              "Stop wavelength [nm],%d\n" % l2.get_value(NANOMETER),
                              "Sweep power O-band [dBm],%g\n" % np.nan,
                              "Sweep power C-band [dBm],%g" % sweep_power.get_value(DBM))
                    header = ''.join(x for x in headerstr)
                    #print headerstr
                    np.savetxt(localcalfile,data,delimiter=",", header=header)
                    #print localcalfile
                    self.MeasurementTree.Calibration = localcalfile
                    self.OpticalCalfile = localcalfile
                    #re-measure the patch cord with compensation enabled:
                    lcal, ilcal, sweep_power = self.continuous_sweep(l1, span,
                                     0.5*NANOMETER,
                                     1.0*MILLISECOND,
                                     10*DBM, 
                                     laser_power=6*DBM,
                                     PM=self.PM)
                    #print 'done sweeping'
                    #print ilcal
                    _, ax = plt.subplots()
                    ax.plot(lun, ilun)
                    ax.hold(True)
                    ax.plot(lcal,ilcal)
                    plt.grid()
                    #plt.show()
                    plt.savefig(that_folder+os.sep+that_file[:-3] + 'png')
                    nbp1 = len(lun)
                    nbp2 = len(lcal)
                    nbp = min([nbp1, nbp2])
                    #print nbp
                    data = np.hstack((np.reshape(lun[:nbp], [nbp,1]), 
                                      np.reshape(ilun[:nbp], [nbp,1]),
                                      np.reshape(lcal[:nbp], [nbp,1]),
                                      np.reshape(ilcal[:nbp], [nbp,1])))
                    try:
                        np.savetxt(that_folder+os.sep+that_file,data,delimiter=",",
                                   header=header)
                    except:
                        msg = ("Calibration result could not be saved to the ",
                               "oiodata network folder. This does not affect the ",
                               "calibration, though. The calibration was ",
                               "successful.")
                        print ''.join(x for x in msg)
            else:
                return
        else:
            msg = ("Do you really want to reset the setup loss calibration [y/n]?")
            q = FiniteWaitForKBInput(lambda: raw_input(''.join(x for x in msg)), self.menutimeout).result
            if q is None:
                return
            elif q == 'y':
                print 'Resetting Agilent 8164B mainframe calibration...'
                #write an empty file to the calibrations folder such that we know
                #that the calibration was reset.
                that_folder = r'\\winbe\oiodata\01_data\Logs\calibrations'
                that_folder += os.sep + self.MeasurementTree.Setup + os.sep + 'setuploss'
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                that_file = '%s_calibration-reset_Agt8164B.csv' % timestamp
                localcalfile = 'agilent8164Bcal.csv'
                self.MeasurementTree.Calibration = that_file
                self.OpticalCalfile = localcalfile
                np.savetxt(localcalfile, np.ndarray([0,0]))
                try:
                    np.savetxt(that_folder+os.sep+that_file, np.ndarray([0,0]))
                except:
                    msg = ("Calibration result could not be saved to the ",
                           "oiodata network folder. This does not affect the ",
                           "calibration, though. The calibration was ",
                           "successfully reset.")
                    print ''.join(x for x in msg)
                    
    def run(self):
        if self.MeasurementTree.StorageFolder == os.sep*2 + self.hostname + os.sep + 'OIO': #r'E:\OIO':
            #folder has not yet been created:
            self.MeasurementTree.StorageFolder += '\\' + self.MeasurementTree.Operator + '\\' + self.MeasurementTree.Wafer.BatchID + '\\' + self.MeasurementTree.Wafer.WaferID + '\\'
        self.__R = result_folder2(self.MeasurementTree.StorageFolder)
        self.MeasurementTree.StorageFolder = self.__R.tmp_path
        print self.MeasurementTree.StorageFolder
        try:
            self.measure_function()
        except:
            self.MeasurementTree.StorageFolder = self.__R.base_folder
            self.__R.finalize(move = False)
            del self.__R
            #raise
        else:
            # move the result folder from user_name/_temp/ to user_name/
            self.__R.finalize(move = True)
            self.MeasurementTree.StorageFolder = self.__R.base_folder
        
    
    def __gather_toolinfo__(self):
        #print 'Tools being used for this measurement:'
        try:
            self.MeasurementTree.ToolInfo = ToolInfo(Name='mainframe', IDN=self.mainframe.__identification_get__())
        except:
            pass
        try:
            self.MeasurementTree.ToolInfo.append(ToolInfo(Name='Tunable_Laser', IDN=self.laser.__idn_get__()))
        except:
            pass
        try:
            self.MeasurementTree.ToolInfo.append(ToolInfo(Name='Power_Sensor', IDN=self.sensor1.__idn_get__()))
        except:
            pass
        try:
            self.MeasurementTree.ToolInfo.append(ToolInfo(Name="Variable_Optical_Attenuator, Power_Sensor", IDN=self.voa.IDN))
        except:
            pass
        try:
            self.MeasurementTree.ToolInfo.append(ToolInfo(Name='Source_Measure_Unit', IDN=self.source.__identification_get__()))
        except:
            pass
        try:
            self.MeasurementTree.ToolInfo.append(ToolInfo(Name='ILPDLEngineMgr', IDN=str(self.ILPDL.Version)))
        except:
            pass
    
    def define_settings(self):
        """Define the measurement settings here
        """
        ms = ILPDLMeasurementSetting()
        ms.AlignSet.AvgTime = 0.5*MILLISECOND
        ms.AlignSet.AlignL = 1555*NANOMETER
        ms.AlignSet.FibreRange = 15*MICROMETER
        ms.AlignSet.FibreSpeed = 100*MICROMETERPERSECOND
        ms.AvgTime = 0.5*MILLISECOND
        ms.AlignSet.LStep = 0.1*NANOMETER
        ms.LStep = 0.1*NANOMETER
        ms.LStart = 1500*NANOMETER
        ms.LSpan = 130*NANOMETER
        ms.LStep = 0.1*NANOMETER
        ms.ID = 'PDL1550'
        ms.AgConfigFile = r'C:\Users\Public\Documents\Photonic Application Suite\SIPPSR3_P170846_D10_XIS_calibration.agconfig'
        
        '''L1550'''
        AlignmentSetting = FibreAlignmentSetting(LStart=1510*NANOMETER, LSpan=90*NANOMETER, LStep=0.1*NANOMETER, AvgTime=0.5*MILLISECOND, FibreRange=15*MICROMETER, FibreSpeed=100*MICROMETERPERSECOND, AlignL=1560*NANOMETER)
        L1550 = LossMeasurementSetting(LStart=1510*NANOMETER, LSpan=90*NANOMETER, LStep=0.1*NANOMETER, LPower=6*DBM, AvgTime=0.5*MILLISECOND, ID='L1550', AlignSet=AlignmentSetting)
        
        return [ms, L1550]
    
    def define_measurementtree(self):
        """Define the measurementTree object here (i.e. ~test plan)
        """
        D_FA = [DUT(Name='FS1', PortCombos=[PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=0*DBM, BlindStep=True, Left='IN', Right='OUT', Probe='LEFT', SettID='PDL1550',AlignAtPeakWL = False,RefWG = True),
                                                        ]
                           )
                       ]
        T_FA = [TestSite(Name='XIS_DEMO', DUTs = D_FA, DynamicAlignWL = False,Recipes='ilpdlmeasurement', SiteOffset=XY(0.0,0.0))]
        M = MeasurementTree()
        M.Wafer.BatchID = 'P170846' # to be adjusted
        M.Wafer.WaferID = 'D10'
        M.Mask = 'SIPPSR3'
        M.Wafer.HomeDie = (0,0)
        M.DieSelection = 'SIPPSR3_full.chip_pos'
        M.TestSites = T_FA
        M.Operator = 'dcosterj'
        M.UseZProfiling = True
        M.AlignMethod = 'spiral'
        M.FiberOutput = {1550:1.70*DBM, 1310:1.15*DBM}
        M.OutputLoss = 0.0
        M.FiberHeight = 20*MICROMETER
        M.FiberAngle = 10
        M.Comment = 'using input fibers 6 and 7, outputs 2,3 (via ext mmi out2 to fiber 7), 4,5 (via ext mmi out 1 to fiber 6) (calibration SIPPSR3_P170846_D10_XIS_calibration.agconfig)'
        M.Temperature = 23
        M.RelativeHumidity = 33
        M.Purpose = ''
        M.ProbeSerial = '41051'
        M.KD = 329
        M.DefaultWavelength = 1550*NANOMETER
        M.DisableChuck = False
        M.Setup = 'ILPDL'
        return M

    def __init_devicecatalog__(self):
        self.devices = DeviceCatalog()
        self.register_device = self.__register_device1
        self.register_function()

    def __register_device1(self, oiodesign, dut, testsite, createdummyprobe):
        '''
        This function is only executed for the first device. All other devices
        are registered using __register_device2.
        '''
        print 'Registering device ', oiodesign.DesignInfo.Name
        if createdummyprobe:
            ''' None or 'NC' was specified in one of the PortCombos for this device. We will create a dummy probe object '''
            lx = oiodesign.DesignInfo.L[0].GDSPosition.X
            ly = oiodesign.DesignInfo.L[0].GDSPosition.Y
            rx = oiodesign.DesignInfo.R[0].GDSPosition.X
            ry = oiodesign.DesignInfo.R[0].GDSPosition.Y
            lxmin = lx
            lymin = ly
            rxmax = rx
            rymin = ry
            for p in oiodesign.DesignInfo.L:
                if (p.GDSPosition.X < lxmin):
                    lxmin = p.GDSPosition.X
                if (p.GDSPosition.Y < lymin):
                    lymin = p.GDSPosition.Y
            for p in oiodesign.DesignInfo.R:
                if (p.GDSPosition.X > rxmax):
                    rxmax = p.GDSPosition.X
                if (p.GDSPosition.Y < rymin):
                    rymin = p.GDSPosition.Y
            #finally, create the dummy probe outside the area spanned by all gratings
            #P = CouplerInfo(Type='Probe', Name='NC', GDSPosition = PXY(lxmin + (lxmin + rxmax)/2, min(lymin, rymin) - 200.0))
            P = CouplerInfo(Type='Probe', Name='NC', GDSPosition = PXY(lxmin + 200.0, lymin - 400.0))
            oiodesign.DesignInfo.P.append(P)
        if self.MeasurementTree.Wafer.Rotated180:
            #if the wafer is 'notch up', left and right fibres are swapped. Moreover, all coordinates need to be inverted.
            L = oiodesign.DesignInfo.L
            R = oiodesign.DesignInfo.R
            oiodesign.DesignInfo.L = []
            oiodesign.DesignInfo.R = []
            for ci in L:
                cx = CouplerInfo(Type='right')
                cx.GDSPosition = RXY(ci.GDSPosition.X, ci.GDSPosition.Y)
                cx.RelativePosition = RXY(ci.RelativePosition[0], ci.RelativePosition[1])
                cx.Name = ci.Name
                cx.AlignmentInfo = ci.AlignmentInfo
                oiodesign.DesignInfo.R.append(cx)
            for ci in R:
                cx = CouplerInfo(Type='left')
                cx.GDSPosition = LXY(ci.GDSPosition.X, ci.GDSPosition.Y)
                cx.RelativePosition = LXY(ci.RelativePosition[0], ci.RelativePosition[1])
                cx.Name = ci.Name
                cx.AlignmentInfo = ci.AlignmentInfo
                oiodesign.DesignInfo.L.append(cx)    
            #oiodesign.DesignInfo.L = R
            #oiodesign.DesignInfo.R = L
            for p in oiodesign.DesignInfo.L:
                p.GDSPosition = -p.GDSPosition
            for p in oiodesign.DesignInfo.R:
                p.GDSPosition = -p.GDSPosition
            for p in oiodesign.DesignInfo.P:
                p.GDSPosition = -p.GDSPosition
        d = self.devices.add_abs(oiodesign, dut, testsite.Recipes, self.MeasurementSettings)
        d.IsHome = True #the first registered device is designated as 'home' device
        ''' at this point, the stage coordinates that were set manually are connected to the first registered device '''
        table_pos, l_pos, r_pos = self.__get_start_pos__()
        self.MeasurementTree.Wafer.RotationAngle = self.__get_waferalignmentinfo__()
        ''' ensure that the relative positions of the first set of gratings is (0,0) '''
        #look for the first left grating that is referred to in the test plan
        left_1st = dut.PortCombos[0].Left
        self.tempstorage['left_1st'] = left_1st
        right_1st = dut.PortCombos[0].Right
        self.tempstorage['right_1st'] = right_1st
        probe_1st = dut.PortCombos[0].Probe
        self.tempstorage['probe_1st'] = probe_1st
        if self.MeasurementTree.Wafer.Rotated180:
            R = SearchObjectListForFieldValue(oiodesign.DesignInfo.R, 'Name', left_1st) #this is the CouplerInfo object for the left grating that is mentioned first in the test plan
            L = SearchObjectListForFieldValue(oiodesign.DesignInfo.L, 'Name', right_1st) #this is the CouplerInfo object for the right grating that is mentioned first in the test plan
        else:
            L = SearchObjectListForFieldValue(oiodesign.DesignInfo.L, 'Name', left_1st) #this is the CouplerInfo object for the left grating that is mentioned first in the test plan
            R = SearchObjectListForFieldValue(oiodesign.DesignInfo.R, 'Name', right_1st) #this is the CouplerInfo object for the right grating that is mentioned first in the test plan
        if (probe_1st == None):
            self.tempstorage['probe_1st'] = 'NC'
            P = SearchObjectListForFieldValue(oiodesign.DesignInfo.P, 'Name', 'NC')
        else:
            P = SearchObjectListForFieldValue(oiodesign.DesignInfo.P, 'Name', probe_1st)
        L.RelativePosition = LXY(0.0,0.0)
        R.RelativePosition = RXY(0.0,0.0)
        P.RelativePosition = PXY(0.0,0.0)
        L.AlignmentInfo = AlignmentResult(AlignSuccess=True, AlignedPosition=XYZ(*l_pos), WaferStageFromDieHome=PXY(0.0, 0.0)) #''' Associate alignment results with first left grating '''
        R.AlignmentInfo = AlignmentResult(AlignSuccess=True, AlignedPosition=XYZ(*r_pos), WaferStageFromDieHome=PXY(0.0, 0.0)) #''' Associate alignment results with first right grating '''
        LXY1, RXY1 = L.RelativePosition, R.RelativePosition
        #print 'LXYZGroup home is at', l_pos, '- and is associated with GDS', L.GDSPosition
        #print 'RXYZGroup home is at', r_pos, '- and is associated with GDS', R.GDSPosition
        LXY1.add_align_result(0, None, l_pos) #(l_pos.X, l_pos.Y, l_pos.Z))
        RXY1.add_align_result(0, None, r_pos) #(r_pos.X, r_pos.Y, r_pos.Z))
        self.L_movements = [LXY1]        #at this point, the property 'L_movements of this class contains one object of type LXY, i.e. the XY coordinate of the first left grating of the first device + the corresponding absolute stage coordinate
        self.R_movements = [RXY1]        #at this point, the property 'R_movements of this class contains one object of type RXY, i.e. the XY coordinate of the first right grating of the first device + the corresponding absolute stage coordinate
        #adjust relative positions of all ports to L[0], R[0] and P[0]
        for lc in d.Design.DesignInfo.L:
            lc.RelativePosition = lc.GDSPosition - L.GDSPosition
        for rc in d.Design.DesignInfo.R:
            rc.RelativePosition = rc.GDSPosition - R.GDSPosition
        for pc in d.Design.DesignInfo.P:
            pc.RelativePosition = pc.GDSPosition - P.GDSPosition
            #print pc.Name, pc.GDSPosition, pc.RelativePosition
        self.register_device = self.__register_device2
        return d
    
    def __register_device2(self, oiodesign, dut, testsite, createdummyprobe):
        print 'Registering device ', oiodesign.DesignInfo.Name
        if createdummyprobe:
            ''' None or 'NC' was specified in one of the PortCombos for this device. We will create a dummy probe object '''
            lx = oiodesign.DesignInfo.L[0].GDSPosition.X
            ly = oiodesign.DesignInfo.L[0].GDSPosition.Y
            rx = oiodesign.DesignInfo.R[0].GDSPosition.X
            ry = oiodesign.DesignInfo.R[0].GDSPosition.Y
            lxmin = lx
            lymin = ly
            rxmax = rx
            rymin = ry
            for p in oiodesign.DesignInfo.L:
                if (p.GDSPosition.X < lxmin):
                    lxmin = p.GDSPosition.X
                if (p.GDSPosition.Y < lymin):
                    lymin = p.GDSPosition.Y
            for p in oiodesign.DesignInfo.R:
                if (p.GDSPosition.X > rxmax):
                    rxmax = p.GDSPosition.X
                if (p.GDSPosition.Y < rymin):
                    rymin = p.GDSPosition.Y
            #finally, create the dummy probe outside the area spanned by all gratings
            #P = CouplerInfo(Type='Probe', Name='NC', GDSPosition = PXY(lxmin + (lxmin + rxmax)/2, min(lymin, rymin) - 200.0))
            P = CouplerInfo(Type='Probe', Name='NC', GDSPosition = PXY(lxmin + 200.0, lymin - 400.0))
            oiodesign.DesignInfo.P.append(P)
        if self.MeasurementTree.Wafer.Rotated180: #self.E.StepperSettings.Rotated180deg:
            #if the wafer is 'notch up', left and right fibres are swapped. Moreover, all coordinates need to be inverted.
            L = oiodesign.DesignInfo.L
            R = oiodesign.DesignInfo.R
            oiodesign.DesignInfo.L = []
            oiodesign.DesignInfo.R = []
            for ci in L:
                cx = CouplerInfo()
                cx.Type = 'right'
                cx.GDSPosition = RXY(ci.GDSPosition.X, ci.GDSPosition.Y)
                cx.RelativePosition = RXY(ci.RelativePosition[0], ci.RelativePosition[1])
                cx.Name = ci.Name
                cx.AlignmentInfo = ci.AlignmentInfo
                oiodesign.DesignInfo.R.append(cx)
            for ci in R:
                cx = CouplerInfo()
                cx.Type = 'left'
                cx.GDSPosition = LXY(ci.GDSPosition.X, ci.GDSPosition.Y)
                cx.RelativePosition = LXY(ci.RelativePosition[0], ci.RelativePosition[1])
                cx.Name = ci.Name
                cx.AlignmentInfo = ci.AlignmentInfo
                oiodesign.DesignInfo.L.append(cx)    
            #oiodesign.DesignInfo.L = R
            #oiodesign.DesignInfo.R = L
            for p in oiodesign.DesignInfo.L:
                p.GDSPosition = -p.GDSPosition
            for p in oiodesign.DesignInfo.R:
                p.GDSPosition = -p.GDSPosition
            for p in oiodesign.DesignInfo.P:
                p.GDSPosition = -p.GDSPosition
        ''' Adjust the RelativePosition properties for the left and right gratings as well as for the probe pads '''
        HomeDeviceName = self.MeasurementTree.Mask + '_' + self.MeasurementTree.TestSites[0].Name + '_' + self.MeasurementTree.TestSites[0].DUTs[0].Name
        if self.MeasurementTree.Wafer.Rotated180:
            R = SearchObjectListForFieldValue(self.devices[HomeDeviceName].Design.DesignInfo.R, 'Name', self.tempstorage['left_1st']) #this is the CouplerInfo object for the left grating that is mentioned first in the test plan
            L = SearchObjectListForFieldValue(self.devices[HomeDeviceName].Design.DesignInfo.L, 'Name', self.tempstorage['right_1st']) #this is the CouplerInfo object for the right grating that is mentioned first in the test plan
        else:
            L = SearchObjectListForFieldValue(self.devices[HomeDeviceName].Design.DesignInfo.L, 'Name', self.tempstorage['left_1st']) #this is the CouplerInfo object for the left grating that is mentioned first in the test plan
            R = SearchObjectListForFieldValue(self.devices[HomeDeviceName].Design.DesignInfo.R, 'Name', self.tempstorage['right_1st']) #this is the CouplerInfo object for the right grating that is mentioned first in the test plan
        P = SearchObjectListForFieldValue(self.devices[HomeDeviceName].Design.DesignInfo.P, 'Name', self.tempstorage['probe_1st'])
        #print testsite.SiteOffset
        #print self.MeasurementTree.TestSites[0].SiteOffset
        for lc in oiodesign.DesignInfo.L:
            lc.RelativePosition = lc.GDSPosition - L.GDSPosition + testsite.SiteOffset - self.MeasurementTree.TestSites[0].SiteOffset
        for rc in oiodesign.DesignInfo.R:
            rc.RelativePosition = rc.GDSPosition - R.GDSPosition + testsite.SiteOffset - self.MeasurementTree.TestSites[0].SiteOffset
        for pc in oiodesign.DesignInfo.P:
            pc.RelativePosition = pc.GDSPosition - P.GDSPosition + testsite.SiteOffset - self.MeasurementTree.TestSites[0].SiteOffset
            #print pc.Name, pc.GDSPosition, pc.RelativePosition
        return self.devices.add_abs(oiodesign, dut, testsite.Recipes, self.MeasurementSettings)
    
    def register_function(self):
        m = self.MeasurementTree.Mask
        demo_instruments = []
        for ti, t in enumerate(self.MeasurementTree.TestSites):
            for d in t.DUTs:
                #retrieve design info from the relevant XML file:
                try:
                    designfile = os.path.dirname(os.path.abspath(__file__)) + os.sep + r'..\..\pymeasure\auto\imec\core\Design' + os.sep + m + os.sep + m+'_'+t.Name + os.sep + m+'_'+t.Name+'_'+d.Name+'.xml'
                    #check whether this file exists
                    if os.path.isfile(designfile):
                        #try to open this file for reading
                        with open(designfile) as f: pass
                    else:
                        raise Exception('File ' + designfile + ' was not found.')
                except Exception, e:
                    raise e
                else:
                    d_design = read_designfile(designfile)
                    ''' check whether the device name from the xml filename and the from the DesignInfo.attrib['Name'] field are the same '''
                    if not (d.Name == d_design.DesignInfo.Name):
                        raise Exception('The device name mentioned in the xml file name ' + designfile + ' is different from the device name mentioned inside the xml file (' + d_design.DesignInfo.Name + ')! ')
                    ''' check whether the testsite name from the xml filename and the from the TestSiteInfo.attrib['Name'] field are the same '''
                    if not (t.Name == d_design.TestSiteInfo.Name):
                        raise Exception('The test site name mentioned in the xml file name ' + designfile + ' is different from the test site name mentioned inside the xml file (' + d_design.TestSiteInfo.Name + ')! ')
                    ''' check whether the specified port names could be found in the designfile '''
                    createdummyprobe = False
                    for p in d.PortCombos:
                        leftfound = SearchObjectListForFieldValue(d_design.DesignInfo.L, 'Name', p.Left)
                        rightfound = SearchObjectListForFieldValue(d_design.DesignInfo.R, 'Name', p.Right)
                        probefound = SearchObjectListForFieldValue(d_design.DesignInfo.P, 'Name', p.Probe)
                        if (leftfound == None):
                            raise Exception('The left coupler with name ' + p.Left + ' was not found in the design file ' + designfile + '.\nPlease amend your test plan!')
                        if (rightfound == None):
                            raise Exception('The right coupler with name ' + p.Right + ' was not found in the design file ' + designfile + '.\nPlease amend your test plan!')
                        if ((p.Probe != None) and (p.Probe != 'NC')) and (probefound == None):
                            raise Exception('The probe pad with name ' + p.Probe + ' was not found in the design file ' + designfile + '.\nPlease amend your test plan!')
                        if (p.Probe == 'NC') or (p.Probe == None):
                            createdummyprobe = True
                        #before registering this device in the catalog, let's check whether the measurementsettings specified for each of the portcombos are valid and the required instruments are connected
                        for sid, s in enumerate(p.SettID):
                            if not s == None:
                                recipe = t.Recipes[sid]
                                ''' search for a MeasurementSetting object with ID = s; also check if the recipe specified in the definition of the TestSite to which this device belongs, is of the same type as the MeasurementSetting object '''
                                ms =  SearchObjectListForFieldValue(self.MeasurementSettings, 'ID', s)
                                if (ms == None):
                                    raise RuntimeError("No MeasurementSetting object with ID=%r could be found! Check the SettID field for device %r in your test plan!"%(s, t.Name + '_' + d.Name))
                                elif (ms.__class__.__name__.lower() != recipe.lower() + 'setting'):
                                    raise RuntimeError("The MeasurementSetting object with ID=%r is of the following type: %r. This does not match the given recipe: %r for device %r! Amend your test plan!"%(s, ms.__class__.__name__, recipe, t.Name + '_' + d.Name))
                                ''' check whether all instruments that are required for the specified recipe, are connected '''
                                for instrument in ms.RequiredInstruments:
                                    #x = SearchObjectListForFieldValue(self.MeasurementTree.ToolInfo, 'Name', instrument)
                                    instr_found = False
                                    for x in self.MeasurementTree.ToolInfo:
                                        if instrument.lower() in x.Name.lower():
                                            instr_found = True
                                            break
                                    if (instr_found == False) and (not instrument in demo_instruments):
                                        #then a required instrument was not found:
                                        msg = ("The measurement recipe %r " % recipe,
                                               "(specified for device %r) " % d.Name,
                                               "requires a %s to be connected! " % instrument,
                                               "Please verify your test plan ",
                                               "and/or instrument connections!")
                                        if (instrument in ['Tunable_Laser', 'Power_Sensor']):
                                            q2 = "Type 'OK' to continue in demo mode, or any other key to quit."
                                            q = raw_input(''.join(x for x in msg[:-2]) + q2)
                                            if q == 'OK':
                                                demo_instruments.append(instrument)
                                            else:
                                                raise RuntimeError(''.join(x for x in msg))
                                        else:
                                            raise RuntimeError(''.join(x for x in msg))
                    #print d_design.DesignInfo.Name, createdummyprobe
                    ''' check whether mask name specified in the xml file corresponds with mask name specified in MeasurementTree'''
                    if not (d_design.MaskInfo.Name == self.MeasurementTree.Mask):
                        raise Exception('The mask name (' + d_design.MaskInfo.Name + ') mentioned in the xml file ' + designfile + ' is different from the mask name mentioned in the test plan (' + self.MeasurementTree.Mask + ')! ')
                finally:
                    pass
                self.register_device(d_design, d, t, createdummyprobe)
    
    def measure_function(self):
        CurrentMaskSet = self.MeasurementTree.Mask
        ''' make sure the laser is on before we start a measurement '''
        self.select_laser(self.MeasurementTree.DefaultWavelength)
        if self.laser.laser_active == 0:
            self.laser.laser_active = 'ON'
        ''' step through all dies, test sites and devices and execute the requested measurement recipe '''
        if self.MeasurementTree.Wafer.Reversed:
            raise Exception('Measurement in reversed order not implemented yet.')
        else:
            for die in self.MeasurementTree.DieList:
                #warnings.filterwarnings('error')
                try:
                    if self.MeasurementTree.DisableChuck == False:
                        self.__step_to_reticle__(die[0], die[1])
                except UserWarning as e:
                    print e, "\nSkipping die (%d,%d)" % (die[0], die[1])
                    continue
                except:
                    raise
                if self.MeasurementTree.TestSites == []:
                    print 'No test sites found in MeasurementTree!'
                    return
                for site_idx, testsite in enumerate(self.MeasurementTree.TestSites):
                    for tindex, testtodo in enumerate(testsite.Recipes):
                        SiteTestResults = []
                        resultfunction = eval('self.__write' + testtodo.lower() + 'result__') 
                        testfunction=eval('self.__' + testtodo.lower() + '__')
                        for di, device in enumerate(testsite.DUTs):
                            DeviceTestResults = []
                            #TODO: check if device.PortCombos.SettID[tindex] == None for all portcombos of this device, then we can skip this device
                            print 'Stepping to device ' + CurrentMaskSet + '_' + testsite.Name + '_' + device.Name
                            CurrentDevice = self.devices[CurrentMaskSet + '_' + testsite.Name + '_' + device.Name]
                            ''' execute the specified measurement recipe '''
                            #SiteTestResults.append(testfunction(self, CurrentDevice, tindex, (di+1, len(testsite.DUTs))))
                            if (testtodo.lower() in ['lossmeasurement', 'ilpdlmeasurement', 'geapdreliabilitymeasurement', 'zsweeplossmeasurement']): # and (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device'):
                                for measdata, dev, portcombo, msett in testfunction(site_idx, CurrentDevice, tindex, (di+1, len(testsite.DUTs))):
                                    if (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device'):
                                        resultfunction([[[measdata, dev, portcombo, msett]]], self.MeasurementTree, write_xml_per_device=True)
                                    else:
                                        DeviceTestResults.append([measdata, dev, portcombo, msett])
                                if (not (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device')) and (not DeviceTestResults == []):
                                    SiteTestResults.append(DeviceTestResults)
                            elif testtodo.lower() in ['heateddemuxwithrefmeasurement', 'heatermeasurement']:
                                for VResults in testfunction(site_idx, CurrentDevice, tindex, (di+1, len(testsite.DUTs))):
                                    DeviceTestResults.append(VResults)
                                if (not (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device')) and (not DeviceTestResults == []):
                                    SiteTestResults.append(DeviceTestResults)
                                '''
                                for VResults in testfunction(self, CurrentDevice, tindex, (di+1, len(testsite.DUTs))):
                                    if (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device'):
                                        resultfunction([[VResults]], self.MeasurementTree, write_xml_per_device=True)
                                    else:
                                        DeviceTestResults.append(VResults)
                                if (not (self.MeasurementTree.GroupMeasurementsBy.lower() == 'device')) and (not DeviceTestResults == []):
                                    SiteTestResults.append(DeviceTestResults)
                                '''
                            else:
                                t = testfunction(self, site_idx, CurrentDevice, tindex, (di+1, len(testsite.DUTs)))
                                if not t == None:
                                    SiteTestResults.append(t)
                            #when we're done measuring the device, save the results:
                            if self.MeasurementTree.GroupMeasurementsBy.lower() == 'device':
                                resultfunction([DeviceTestResults], self.MeasurementTree, write_xml_per_device=True)
                        ''' do something with the results for all devices (e.g. write them to a file) '''
                        if (self.MeasurementTree.GroupMeasurementsBy.lower() == 'testsite') and (not len(SiteTestResults) == 0):
                            print 'writing measurement results'
                            resultfunction(SiteTestResults, self.MeasurementTree)
        
    def __ilpdlmeasurement__(self, site_index, device, recipe_index, siteprogress):
        '''Perform a loss measurement
        Args:
        -site_index (int): index of the current test site in the overall
            measurement plan.
        -device (Device): a 'Device' object (class is defined in core), 
            representing the device to be measured.
        -recipe_index (int): index of the loss measurement in the list of recipes 
            that is specified for the current test site.
        -siteprogress (tuple): (x,y) where x is the 1-based index of the 
            current device in the test site, and y is the number of devices in
            the test site.
        '''        
        that_folder = r'\\winbe\oiodata\01_data\Logs\calibrations'
        that_folder += os.sep + self.MeasurementTree.Setup + os.sep + 'setuploss'
        print "*******************************************************************************"
        print "begin il/pdl measurement on ", device.Design.DesignInfo.Name
        ''' for every PortCombo in device.PortCombos, we will look for the corresponding MeasurementSetting object '''
        settings_list = []    
        for p in device.PortCombos:
            settings_increment = None
            for m in self.MeasurementSettings:
                if (m.__class__.__name__.lower() == 'ilpdlmeasurementsetting') & (m.ID == p.SettID[recipe_index]):
                    #we have found the corresponding MeasurementSetting object
                    settings_increment = m
                    break #stop browsing
            settings_list.append(settings_increment)
        if all(v == None for v in settings_list):
            print "no portcombos of this device marked for ilpdlmeasurement"
        else:
            ''' we will now move the fibres and the wafer to each of the specified PortCombos and perform a measurement at each one of them '''
            TestResults = []
            scenario = 1 #1: fiber array, 2: fiber array in and single fiber out
            for portcombo, peakWL, probefromdiehome, msett, deviceprogress in self.walk_device(site_index, device, settings_list):

                #perform wavelength sweep and store data:
                try:
                    #del self.Engine
                    #switch to output 1:
                    self.switch.OutputPort = 1
                    self.laser.write('sour0:wav:swe:stat 0') 
                    self.sensor1.write("SENS1:CHAN1:POW:UNIT 0")
                    self.laser.write(":SOUR0:POW:UNIT 0") 
                    self.laser.power = msett.AlignSet.AlignP
                    self.laser.laser_active = 'ON'
                    self.laser.wavelength = msett.AlignSet.AlignL
                    print msett.AlignSet.AlignL
                    #align left fiber manipulator
                    self.__spiral_align_fibre_R__(radius=15*MICROMETER, 
                                                  turns=5, 
                                                  velocity=80*MICROMETERPERSECOND,
                                                  expected_power=None, #-10*DBM,
                                                  onlysmall=False)
                    through = self.analog_source.get_power()
                    print 'Rx = %sdBm' % through.get_value()
                    if through.get_value() < -15:
                        #re-align
                        self.__spiral_align_fibre_R__(radius=15*MICROMETER, 
                                                  turns=5, 
                                                  velocity=80*MICROMETERPERSECOND,
                                                  expected_power=None, #-10*DBM,
                                                  onlysmall=False)
                        through = self.analog_source.get_power()
                        print 'Rx = %sdBm' % through.get_value()
                    self.laser.power = msett.LPower
                    msmtresult = LossMeasurementResult(DateStamp=localtime())
                    #load calibration for first power meter
                    self.OpticalCalfile = that_folder + os.sep + 'meter1.csv'
                    print self.OpticalCalfile
                    if msett.SweepDir.lower() == 'up':
                        wavelengths, powers, sweep_power = self.continuous_sweep( start_wavelength = msett.LStart, 
                                                    scan_range = msett.LSpan, 
                                                    resolution_wavelength = msett.LStep, 
                                                    averaging_time = msett.AvgTime, 
                                                    sensor_range = portcombo.MeasurePwrRng, laser_power=msett.LPower,
                                                    PM=self.PM)
                        self.tempstorage['wavelength_sweeps']+=1
                    elif msett.SweepDir.lower() == 'updown':
                        wavelengths, powers, sweep_power = self.stepped_2way_sweep( start_wavelength = msett.LStart, 
                                                    scan_range = msett.LSpan, 
                                                    resolution_wavelength = msett.LStep, 
                                                    averaging_time = msett.AvgTime, 
                                                    sensor_range = portcombo.MeasurePwrRng, laser_power=msett.LPower)
                    else:
                        raise Exception('Sweepdir ' + msett.SweepDir + ' is not implemented in LossMeasurement recipe.')
                    msmtresult.LPower = sweep_power
                    msmtresult.Wavelengths = ConvertDimensionlesslist2UnitList(wavelengths, NANOMETER)
                    msmtresult.ILoss = powers #ConvertDimensionlesslist2UnitList(powers, DBM)
                    
                    if scenario == 2:
                        #now measure transmission to right fiber
                        #align right fiber manipulator if it is used:
                        self.switch.OutputPort = 3
                        self.laser.power = msett.AlignSet.AlignP
                        self.laser.wavelength = msett.AlignSet.AlignL
                        self.__spiral_align_fibre_R__(radius=15*MICROMETER, 
                                                  turns=5, 
                                                  velocity=80*MICROMETERPERSECOND,
                                                  expected_power=None, #-10*DBM,
                                                  onlysmall=False)
                        print 'Rx = %sdBm' % self.analog_source2.get_power().get_value()
                        self.laser.power = msett.LPower
                        msmtresult2 = LossMeasurementResult(DateStamp=localtime())
                        #load calibration for second power meter
                        self.OpticalCalfile = that_folder + os.sep + 'meter2.csv'
                        wavelengths, powers, sweep_power = self.continuous_sweep( start_wavelength = msett.LStart, 
                                                    scan_range = msett.LSpan, 
                                                    resolution_wavelength = msett.LStep, 
                                                    averaging_time = msett.AvgTime, 
                                                    sensor_range = portcombo.MeasurePwrRng, laser_power=msett.LPower,
                                                    PM=self.PM2)
                        self.tempstorage['wavelength_sweeps']+=1
                        msmtresult2.LPower = sweep_power
                        msmtresult2.Wavelengths = ConvertDimensionlesslist2UnitList(wavelengths, NANOMETER)
                        msmtresult2.ILoss = powers #ConvertDimensionlesslist2UnitList(powers, DBM)
                        self.__writelossmeasurementresult__([[[msmtresult2, device, portcombo, msett]]], self.MeasurementTree, False, False)
                        
                    elif scenario == 1:
                        #perform IL PDL measurement
                        #load configuration
                        self.ILPDL.LoadConfiguration(msett.AgConfigFile)
                        #switch to output 2:
                        self.switch.OutputPort = 2
                        #start measurement
                        #self.Engine.StartMeasurement()
                        #wait max 60 seconds
                        meas_attempts = 2
                        meas_func = self.ILPDL.StartMeasurement
                        while meas_attempts > 0:
                            meas_func()
                            busy = 120
                            engine_flag = 1
                            while (busy >= 1) and (engine_flag == 1):
                                time.sleep(0.5)
                                busy -= 1
                                engine_flag = self.ILPDL.Engine.Busy
                            if engine_flag == 0:
                                #measurement finished successfully
                                break
                            elif busy <= 1:
                                #timeout elapsed:
                                #try to reconnect to the engine
                                engine_was_ok = self.ILPDL.ReConnect()
                                if not engine_was_ok:
                                    #a new engine has been started, retry the measurement
                                    meas_func = self.ILPDL.StartMeasurement
                                    meas_attempts -= 1
                                else:
                                    #engine was ok, so maybe the measurement got 
                                    #stuck for some reason. try to stop it
                                    meas_func = self.ILPDL.StopMeasurement
                                    meas_attempts -= 1
    #                     self.ILPDL.StartMeasurement()
    #                     #Wait for measurement to be finished
    #                     while self.ILPDL.Engine.Busy:
    #                         time.sleep(1)
                        #Get result object
                        #IOMRFile = self.ILPDL.Engine.MeasurementResult
                        #ilpdlMeasurementResult = self.ILPDL.Engine.MeasurementResult;
                        #save file
                        L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Left)
                        Die = L.AlignmentInfo.Die
                        Mask = device.Design.MaskInfo.Name
                        TestSite = device.Design.TestSiteInfo.Name
                        filename = self.MeasurementTree.StorageFolder + os.sep + self.MeasurementTree.Wafer.BatchID + '_' + self.MeasurementTree.Wafer.WaferID + '_' + '(%d,%d)' % Die + '_' + Mask + '_' + TestSite
                        t = glob.glob(filename + '*')
                        if len(t) > 0:
                            filename += '%0.3d.omr' % len(t)
                        else:
                            filename += '.omr'
                        print filename
                        self.ILPDL.FileSave(filename)
                        #Save as OMR file
                        #IOMRFile.Write(filename)
                        #Release measurement object
                        #IOMRFile.release
    #                     self.ILPDL.Engine.Deactivate()
                        #del self.Engine
                        #release the TLS
                        self.laser.write('sour0:wav:swe:stat 0') 
                        self.switch.OutputPort = 2
                    yield msmtresult, device, portcombo, msett
                    
                #except InstrumentValueError, e:
                #    raise e
                except:
                    raise
                
        
    def __writeilpdlmeasurementresult__(self, result_list, measurementtree, write_xml_per_device=False, write_xml_per_port=False):
        '''
        This function writes an xml result file for a loss site measurement.
        Input arguments:
            result_list: a nested list of [LossMeasurementResult object, device object, portcombo object, LossMeasurementSetting object] lists.
                first level of indexing: different devices in a test site
                second level of indexing: different portcombos for a given device
                third level: choice between access to LossMeasurementResult object, device object or portcombo object
            measurementtree: a MeasurementTree object
        '''
        self.__writelossmeasurementresult__(result_list, measurementtree, write_xml_per_device, write_xml_per_port)
    
    def __lossmeasurement__(self, site_index, device, recipe_index, siteprogress):
        '''Perform a loss measurement
        Args:
        -site_index (int): index of the current test site in the overall
            measurement plan.
        -device (Device): a 'Device' object (class is defined in core), 
            representing the device to be measured.
        -recipe_index (int): index of the loss measurement in the list of recipes 
            that is specified for the current test site.
        -siteprogress (tuple): (x,y) where x is the 1-based index of the 
            current device in the test site, and y is the number of devices in
            the test site.
        '''        
        print "*******************************************************************************"
        print "begin loss measurement on ", device.Design.DesignInfo.Name
        
        ''' for every PortCombo in device.PortCombos, we will look for the corresponding MeasurementSetting object '''
        settings_list = []    
        for p in device.PortCombos:
            settings_increment = None
            for m in self.MeasurementSettings:
                if (m.__class__.__name__.lower() == 'lossmeasurementsetting') & (m.ID == p.SettID[recipe_index]):
                    #we have found the corresponding MeasurementSetting object
                    settings_increment = m
                    break #stop browsing
            settings_list.append(settings_increment)
        if all(v == None for v in settings_list):
            print "no portcombos of this device marked for lossmeasurement"
        else:
            ''' we will now move the fibres and the wafer to each of the specified PortCombos and perform a measurement at each one of them '''
            TestResults = []
        #for portcombo, peakWL, probefromdiehome, msett, deviceprogress in self.walk_device(site_index, device, settings_list):
        portcombo = device.PortCombos[0]
        msett = settings_list[0]
        deviceprogress = (1,len(device.PortCombos))
        proberfromdiehome = PXY(0.0, 0.0)
        peakWL = msett.AlignSet.AlignL
#             if (siteprogress[0] == 1) & (deviceprogress[0] == 1):
#                 self.tempstorage['original_prealign'] = msett.AlignSet.PreAlign
                
#             if (peakWL != None) & (msett.AlignSet.PreAlign == True) & (portcombo.BlindStep == False) & (('ALIGN' in device.Design.DesignInfo.Name) or (msett.ForcePreAlign == True)):
#                 #if this portcombo is on a reference waveguide, we fill in the detected peakWL in the alignment settings object in msett and disable PreAlign for any subsequent portcombos and devices at this testsite:
#                 if not msett.ForcePreAlign:
#                     msett.AlignSet.AlignL = peakWL #all subsequent devices at this site will be aligned at this wavelength.
#                     msett.AlignSet.PreAlign = False #pre-align wavelength sweep will not be performed for any remaining portcombos of the current device, nor for any remaining devices at the current test site and for the 
#                 self.align_fibres_LR(device, portcombo, probefromdiehome, align_wavelength = peakWL, align_travel = msett.AlignSet.FibreRange, align_velocity = msett.AlignSet.FibreSpeed)
    
        ''' at this point we are aligned to the left and right ports from portcombo '''
        try:
            #self.laser.power = msett.LPower
            #self.laser.laser_active = 'ON'
            msmtresult = LossMeasurementResult(DateStamp=localtime())
            if msett.SweepDir.lower() == 'up':
                wavelengths, powers, sweep_power = self.continuous_sweep( start_wavelength = msett.LStart, 
                                            scan_range = msett.LSpan, 
                                            resolution_wavelength = msett.LStep, 
                                            averaging_time = msett.AvgTime, 
                                            sensor_range = portcombo.MeasurePwrRng, laser_power=msett.LPower)
                self.tempstorage['wavelength_sweeps']+=1
            elif msett.SweepDir.lower() == 'updown':
                wavelengths, powers, sweep_power = self.stepped_2way_sweep( start_wavelength = msett.LStart, 
                                            scan_range = msett.LSpan, 
                                            resolution_wavelength = msett.LStep, 
                                            averaging_time = msett.AvgTime, 
                                            sensor_range = portcombo.MeasurePwrRng, laser_power=msett.LPower)
            else:
                raise Exception('Sweepdir ' + msett.SweepDir + ' is not implemented in LossMeasurement recipe.')
            print sweep_power
            print msmtresult.LPower
            msmtresult.LPower = sweep_power
            msmtresult.Wavelengths = ConvertDimensionlesslist2UnitList(wavelengths, NANOMETER)
            if hasattr(self, 'ct400') or hasattr(self, 'mainframe'):
                #we are measuring insertion loss rather than absolute power at the detector:
                msmtresult.ILoss = powers
            else:
                msmtresult.Powers = ConvertDimensionlesslist2UnitList(powers, DBM)
            #TestResults.apped([LossMeasurementResult(Wavelengths = wavelengths_xml, Powers = powers_xml, DateStamp=localtime()), device, portcombo, msett])
            #if self.laser.idn == 'Yenista,Tunics,0,6.03':
            #    #laser power, measured at the output of the CT400 box:
            #    outp = self.ct400.ScanGetPowerSyncArray(1)
            #    msett.LPower = outp[0]*DBM
            if hasattr(self, 'thermometer') and (not self.thermometer is None):
                msmtresult.Temperature = self.thermometer.voltage
            yield msmtresult, device, portcombo, msett
        except InstrumentValueError, e:
            raise e
        except Exception, e:
            ei = sys.exc_info()[0]
            print ei
            raise
        
    def __writelossmeasurementresult__(self, result_list, measurementtree, write_xml_per_device=False, write_xml_per_port=False):
        '''
        This function writes an xml result file for a loss site measurement.
        Input arguments:
            result_list: a nested list of [LossMeasurementResult object, device object, portcombo object, LossMeasurementSetting object] lists.
                first level of indexing: different devices in a test site
                second level of indexing: different portcombos for a given device
                third level: choice between access to LossMeasurementResult object, device object or portcombo object
            measurementtree: a MeasurementTree object
        '''
        #look for the die row and column. In order to do this, we need to look at 
        #the alignmentinfo of a measured grating:
        portcombo = result_list[0][0][2]
        L = SearchObjectListForFieldValue(result_list[0][0][1].Design.DesignInfo.L, 'Name', portcombo.Left)
        Die = L.AlignmentInfo.Die
        Mask = result_list[0][0][1].Design.MaskInfo.Name
        TestSite = result_list[0][0][1].Design.TestSiteInfo.Name
        #Die = result_list[0][0][1].Design.DesignInfo.L[0].AlignmentInfo.Die
        mainnode = Efactory.OIOMeasurement(Operator=measurementtree.Operator, CreationDate=asctime(localtime()))
        
        testsiteinfonode = Efactory.TestSiteInfo(Batch=measurementtree.Wafer.BatchID, Wafer=measurementtree.Wafer.WaferID, DieRow='%d'%Die[0], DieColumn='%d'%Die[1], TestSite=TestSite, Maskset=Mask)
        mainnode.append(testsiteinfonode)
        toolinfonode = Efactory.ToolInfo()
        mainnode.append(toolinfonode)
        for tool in measurementtree.ToolInfo:
            toolnode = Efactory.Tool(Name=tool.Name, IDN=tool.IDN)
            toolinfonode.append(toolnode)
        setupinfonode = Efactory.SetupInfo()
        mainnode.append(setupinfonode)
        #select the appropriate fiber output power depending on the alignment wavelength in the settings object:
        #align wl:
        alignwl = result_list[0][0][3].AlignSet.AlignL.get_value(NANOMETER)
        selectedkey = None
        distance = np.inf
        for k in measurementtree.FiberOutput.keys():
            if np.abs(k-alignwl) < distance:
                selectedkey = k
                distance = np.abs(k-alignwl)
        infonode = Efactory.FiberOutput(str(measurementtree.FiberOutput[selectedkey]))
        setupinfonode.append(infonode)
        infonode = Efactory.OutputLoss(str(measurementtree.OutputLoss))
        setupinfonode.append(infonode)                     
        infonode = Efactory.AlignMethod(str(measurementtree.AlignMethod))
        setupinfonode.append(infonode)
        infonode = Efactory.UseZProfiling(str(measurementtree.UseZProfiling))
        setupinfonode.append(infonode)
        infonode = Efactory.FiberHeight(str(measurementtree.FiberHeight))
        setupinfonode.append(infonode)
        infonode = Efactory.FiberAngle(str(measurementtree.FiberAngle))
        setupinfonode.append(infonode)
        infonode = Efactory.WaferHomeFromChuckCenter(str(measurementtree.Wafer.HomeFromChuckCenter))
        setupinfonode.append(infonode)
        
        commentnode = Efactory.Comment(Info=measurementtree.Comment)
        mainnode.append(commentnode)
        
        measurenode = Efactory.MeasurementResults()
        mainnode.append(measurenode)
        opticalnode = Efactory.OpticalMeasurements()
        mainnode.append(opticalnode)
        electroopticalnode = Efactory.ElectroOpticalMeasurements()
        mainnode.append(electroopticalnode)
        electricalnode = Efactory.ElectricalMeasurements()
        mainnode.append(electricalnode)
        lossnode = Efactory.LossMeasurement(Operator=measurementtree.Operator)
        opticalnode.append(lossnode)
        for devicelevelresult in result_list:
            device = devicelevelresult[0][1]
            waveguidenode = Efactory.WaveguideLossMeasurement(Name=device.Design.DesignInfo.Name, Designer=device.Design.Designer)
            lossnode.append(waveguidenode)
            commentnode = Efactory.DesignDescription(device.Design.DesignDescription)
            waveguidenode.append(commentnode)
            devicenode = Efactory.DeviceInfo(Name=device.Design.DesignInfo.Name)
            waveguidenode.append(devicenode)
            parameternode = Efactory.DesignParameters()
            devicenode.append(parameternode)
            for p in device.Design.DesignInfo.DesignParameters:
                paramnode = Efactory.DesignParameter(p.Value, Unit=repr(p.Unit)[5:], Name=p.Name, Symbol=p.Symbol)
                parameternode.append(paramnode)
            for portcombolevelresult in devicelevelresult:
                temperature = portcombolevelresult[0].Temperature.get_value(VOLT)
                portcombonode = Efactory.PortLossMeasurement(Left=portcombolevelresult[2].Left, Right=portcombolevelresult[2].Right, Probe=portcombolevelresult[2].Probe, DateStamp=asctime(portcombolevelresult[0].DateStamp),
                                                             Temperature=repr(temperature), TempUnit=repr(VOLT))
                waveguidenode.append(portcombonode)
                testresult = portcombolevelresult[0]
                device = portcombolevelresult[1]
                portcombo = portcombolevelresult[2]
                settings = portcombolevelresult[3]
                L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Left) #this is the CouplerInfo object for the left grating
                R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Right) #this is the CouplerInfo object for the right grating
                P = SearchObjectListForFieldValue(device.Design.DesignInfo.P, 'Name', portcombo.Probe) #this is the CouplerInfo object for the probe pad  
                positionnode = Efactory.PositionerInfo()
                portcombonode.append(positionnode)
                leftnode = Efactory.LeftFibre(Name=L.Name, Absolute=repr(L.AlignmentInfo.AlignedPosition), GDS=repr(L.GDSPosition), FromHome=repr(L.RelativePosition), Shift=repr(L.AlignmentInfo.FibreShift))
                positionnode.append(leftnode)
                for trajdata in L.AlignmentInfo.TrajectoryData:
                    trajnode = Efactory.TrajectoryData()
                    leftnode.append(trajnode)
                    if len(trajdata) > 0:
                        XYZV = SeparateTupleList(trajdata)
                        xnode = Efactory.X(ConvertList2CommaSeparatedString(XYZV['0']), XUnit=repr(MILLIMETER))
                        ynode = Efactory.Y(ConvertList2CommaSeparatedString(XYZV['1']), YUnit=repr(MILLIMETER))
                        znode = Efactory.Z(ConvertList2CommaSeparatedString(XYZV['2']), ZUnit=repr(MILLIMETER))
                        vnode = Efactory.V(ConvertList2CommaSeparatedString(XYZV['3']), VUnit=repr(VOLT))
                        trajnode.append(xnode)
                        trajnode.append(ynode)
                        trajnode.append(znode)
                        trajnode.append(vnode)
                rightnode = Efactory.RightFibre(Name=R.Name, Absolute=repr(R.AlignmentInfo.AlignedPosition), GDS=repr(R.GDSPosition), FromHome=repr(R.RelativePosition), Shift=repr(R.AlignmentInfo.FibreShift))
                positionnode.append(rightnode)
                for trajdata in R.AlignmentInfo.TrajectoryData:
                    trajnode = Efactory.TrajectoryData()
                    rightnode.append(trajnode)
                    if len(trajdata) > 0:
                        XYZV = SeparateTupleList(trajdata)
                        xnode = Efactory.X(ConvertList2CommaSeparatedString(XYZV['0']), XUnit=repr(MILLIMETER))
                        ynode = Efactory.Y(ConvertList2CommaSeparatedString(XYZV['1']), YUnit=repr(MILLIMETER))
                        znode = Efactory.Z(ConvertList2CommaSeparatedString(XYZV['2']), ZUnit=repr(MILLIMETER))
                        vnode = Efactory.V(ConvertList2CommaSeparatedString(XYZV['3']), VUnit=repr(VOLT))
                        trajnode.append(xnode)
                        trajnode.append(ynode)
                        trajnode.append(znode)
                        trajnode.append(vnode)
                probenode = Efactory.WaferStage(Name=P.Name, FromCenter=repr(P.AlignmentInfo.AlignedPosition), GDS=repr(P.GDSPosition), FromDieHome=repr(P.RelativePosition))
                positionnode.append(probenode)
                successnode = Efactory.AlignSuccess(Left=repr(L.AlignmentInfo.AlignSuccess), Right=repr(R.AlignmentInfo.AlignSuccess))
                positionnode.append(successnode)
                if L.AlignmentInfo.AlignWavelength == None:
                    wavelengthnode = Efactory.AlignWavelength('NaN', Unit=repr(NANOMETER)[5:])
                else:    
                    wavelengthnode = Efactory.AlignWavelength(repr(L.AlignmentInfo.AlignWavelength.get_value(NANOMETER)), Unit=repr(NANOMETER)[5:])
                positionnode.append(wavelengthnode)
                pwr = ''
                for pw in testresult.LPower:
                    pwr += '%4.4g,' % pw.get_value(testresult.PUnit)
    #             pwr = repr(testresult.LPower.get_value(testresult.PUnit))
                resultnode = Efactory.MeasurementResult(Power=pwr[:-1], PowerUnit=repr(testresult.PUnit)[5:])
                portcombonode.append(resultnode)
                wavenode = Efactory.L(ConvertList2StringWithoutUnits(testresult.Wavelengths, testresult.WUnit), Unit=repr(testresult.WUnit)[5:])
                if not testresult.ILoss is None:
                    #insertion loss rather than absolute power has been measured:
                    powernode = Efactory.IL(ConvertList2CommaSeparatedString(testresult.ILoss))
                else:
                    powernode = Efactory.P(ConvertList2StringWithoutUnits(testresult.Powers, testresult.PUnit), Unit=repr(testresult.PUnit)[5:])
                resultnode.append(wavenode)
                resultnode.append(powernode)
        if not write_xml_per_device:
            filename = measurementtree.StorageFolder + os.sep + measurementtree.Wafer.BatchID + '_' + measurementtree.Wafer.WaferID + '_' + '(%d,%d)' % Die + '_' + Mask + '_' + TestSite
        else:
            if write_xml_per_port:
                filename = measurementtree.StorageFolder + os.sep + measurementtree.Wafer.BatchID + '_' + measurementtree.Wafer.WaferID + '_' + '(%d,%d)' % Die + '_' + Mask + '_' + TestSite + '_' + device.Design.DesignInfo.Name + '_L-' + L.Name + '_R-' + R.Name + '_P-' + P.Name
            else:
                filename = measurementtree.StorageFolder + os.sep + measurementtree.Wafer.BatchID + '_' + measurementtree.Wafer.WaferID + '_' + '(%d,%d)' % Die + '_' + Mask + '_' + TestSite + '_' + device.Design.DesignInfo.Name
        t = glob.glob(filename + '*')
        if len(t) > 0:
            filename += '%0.3d.xml' % len(t)
        else:
            filename += '.xml'
        print filename
        outp = etree.tostring(mainnode, pretty_print=True)
        f = open(filename, 'w')
        f.write(outp)
        f.close()
        
    def __laser_settings__(self):
        ''' this function changes the laser wavelength and allows the laser to be switched on and off '''
        print "Press 'w' to set wavelength, 'p' to set the power level, o to switch the output on/off, or 'escape' to quit."
        state = 0
        while 1:
            command = None
            c = FiniteWaitForKBInput(lambda: msvcrt.getch(), self.menutimeout).result
            #c = msvcrt.getch()
            if c is None:
                break
            d = ord(c)
            #print c, d
            if state == 0:
                if d == 27:     #esc key pressed --> leave the while loop
                    break
                elif c == 'w':
                    ''' set wavelength '''
                    while 1:
                        try:
                            q = FiniteWaitForKBInput(lambda: raw_input("Enter desired wavelength [nm]: "), self.menutimeout).result
                            if q is None:
                                break
                            #q = raw_input("Enter desired wavelength [nm]: ")
                            Wx = float(q)
                            break
                        except:
                            #stay in the while loop until user has entered valid numbers
                            print 'Please type a numeric value!'
                    try:
                        self.select_laser(Wx*NANOMETER)
                        #self.laser.wavelength = Wx*NANOMETER
                    except InstrumentValueError as ive:
                        print ive
                elif c == 'p':
                    ''' set power level '''
                    while 1:
                        try:
                            q = FiniteWaitForKBInput(lambda: raw_input("Enter desired power level [dBm]: "), self.menutimeout).result
                            if q is None:
                                break
                            #q = raw_input("Enter desired power level [dBm]: ")
                            Wx = float(q)
                            break
                        except:
                            #stay in the while loop until user has entered valid numbers
                            print 'Please type a numeric value!'
                    try:
                        self.laser.power = Wx*DBM
                    except InstrumentValueError as ive:
                        print ive
                elif c == 'o':
                    ''' switch output on and off '''
                    while 1:
                        try:
                            q = FiniteWaitForKBInput(lambda: raw_input("Enter desired output state [1 or 0]: "), self.menutimeout).result
                            if q is None:
                                break
                            #q = raw_input("Enter desired output state [1 or 0]: ")
                            Wx = float(q)
                            if (Wx == 0) or (Wx == 1):
                                break
                            else:
                                print "Please answer '1' or '0'"
                        except:
                            #stay in the while loop until user has entered valid numbers
                            print "Please answer '1' or '0'"
                    if (Wx == 1):
                        self.laser.laser_active = 'ON'
                    elif (Wx == 0):
                        self.laser.laser_active = 'OFF'
    
    def __perform_sweep__(self, **kwargs):
        '''Method to perform a wavelength sweep.
        Settings are defined as follows:
        -through the __sweep_questions__ method
        -or through a msett object provided as keyword argrument
        
        Testsite name, device name and comment are defined as follows:
        -through self.tempstorage dictionary
        -or through TestSite, Device and Comment string keyword arguments
        
        Wafer and device properties are defined as follows:
        -through the self.MeasurementTree object
        -or through a MeasurementTree object provided as keyword argument
        
        Portcombo properties are defined as follows:
        -through self.tempstorage dictionary
        -or through PortCombo object provided as keyword argument
        '''
        self.A.set_arms_speed(.1)
        self.tempstorage['l_spot'] = self.laser.wavelength
#         self.laser.laser_active = 'ON'
        if ('msett' in kwargs.keys()) and (not kwargs['msett'] is None):
            msett = kwargs['msett']
        else:
            if 'skipquestions' in kwargs.keys():
                skipq = kwargs['skipquestions']
            else:
                skipq = False
            q_ans = self.__sweep_questions__(skipq)
            if (skipq == False) and (q_ans == False):
                return
            #generate a settings object
            stt = LossMeasurementSetting
            msett = stt(LStart=self.tempstorage['l_start'], LSpan=self.tempstorage['l_span'], LStep=self.tempstorage['l_step'], LPower=self.tempstorage['l_power'], AvgTime=0.5*MILLISECOND, ID='dummyloss')
        if ('MeasurementTree' in kwargs.keys()) and (not kwargs['MeasurementTree'] is None):
            localMsmtTree = kwargs['MeasurementTree']
        else:
            localMsmtTree = self.MeasurementTree
        if ('PortCombo' in kwargs.keys()) and (not kwargs['PortCombo'] is None):
            p = kwargs['PortCombo']
        else:
            if not 'leftgrating_name' in self.tempstorage.keys():
                self.tempstorage['leftgrating_name'] = 'Left'
            if not 'rightgrating_name' in self.tempstorage.keys():
                self.tempstorage['rightgrating_name'] = 'Right'
            if not 'probepad_name' in self.tempstorage.keys():
                self.tempstorage['probepad_name'] = 'Probe'
            p = PortCombo(BlindStep=True, MeasurePwrRng=self.tempstorage['l_powerrange'], Left=self.tempstorage['leftgrating_name'], Right=self.tempstorage['rightgrating_name'], Probe=self.tempstorage['probepad_name'], SettID=msett.ID)
        #generate a dummy 'Device' object:
        t = OIODesign()
        t.MaskInfo.Name = localMsmtTree.Mask
        if ('Comment' in kwargs.keys()) and  (not kwargs['Comment'] is None):
            #t.DesignDescription = kwargs['Comment']
            localMsmtTree.Comment = kwargs['comment']
        elif ('Comment' in self.tempstorage.keys()):
            #t.DesignDescription = self.tempstorage['comment']
            localMsmtTree.Comment = self.tempstorage['comment']
        t.Designer = '-'
        if ('TestSite' in kwargs.keys()) and  (not kwargs['TestSite'] is None):
            t.TestSiteInfo.Name = kwargs['TestSite']
        elif ('currenttestsite' in self.tempstorage.keys()):
            t.TestSiteInfo.Name = self.tempstorage['currenttestsite']
        if ('Device' in kwargs.keys()) and  (not kwargs['Device'] is None):
            t.DesignInfo.Name = kwargs['Device']
        elif ('currentdevice' in self.tempstorage.keys()):
            t.DesignInfo.Name = self.tempstorage['currentdevice']
        t.DesignInfo.L = CouplerInfo(Type='Left', Name=p.Left)
        t.DesignInfo.L[0].AlignmentInfo.Die = localMsmtTree.Wafer.CurrentDie
        t.DesignInfo.R = CouplerInfo(Type='Right', Name=p.Right)
        t.DesignInfo.P = CouplerInfo(Type='Probe', Name=p.Probe)
        
        dev = Device()
        dev.Design = t
        dev.PortCombos = [p]
        dev.IsHome = False
        measresult = LossMeasurementResult
        mr = measresult()
        #create a folder for storage if needed:
        if localMsmtTree.StorageFolder == os.sep*2 + self.hostname + os.sep + 'OIO': #r'E:\OIO':
            #no measurement has been performed yet. initialize the storage folder:
            localMsmtTree.StorageFolder = localMsmtTree.StorageFolder + '\\' + localMsmtTree.Operator + '\\' + localMsmtTree.Wafer.BatchID + '\\' + localMsmtTree.Wafer.WaferID + '\\'
            if not os.path.exists(localMsmtTree.StorageFolder):
                os.makedirs(localMsmtTree.StorageFolder)
        #perform the sweep
        that_folder = r'\\winbe\oiodata\01_data\Logs\calibrations'
        that_folder += os.sep + self.MeasurementTree.Setup + os.sep + 'setuploss'
        self.OpticalCalfile = that_folder + os.sep + 'meter1.csv'
        fast_X, fast_Y, sweep_power = self.continuous_sweep( start_wavelength = msett.LStart, scan_range = msett.LSpan, resolution_wavelength=msett.LStep, averaging_time = msett.AvgTime, sensor_range = p.MeasurePwrRng, laser_power=msett.LPower)
#         print fast_X[0]
#         print fast_Y[0]
        mr.Wavelengths = ConvertDimensionlesslist2UnitList(fast_X, NANOMETER)
        if hasattr(self, 'ct400') or hasattr(self, 'mainframe'):
            #we are measuring insertion loss rather than absolute power at the detector:
            mr.ILoss = fast_Y
        else:
            mr.Powers = ConvertDimensionlesslist2UnitList(fast_Y, DBM)
        mr.LPower = sweep_power
        mr.DateStamp = time.localtime()
        #save the result
        if ('ret' in kwargs.keys()) and (kwargs['ret'] == True):
            return [mr, dev, p, msett]
        else:
            resultfunction=self.__writelossmeasurementresult__
            resultfunction([[[mr, dev, p, msett]]], localMsmtTree, write_xml_per_device=True, write_xml_per_port=True)
            plt.plot(fast_X, fast_Y)
            plt.grid()
            plt.show()
        #set laser back to intial wavelength
        if 'l_spot' in self.tempstorage.keys():
            self.select_laser(self.tempstorage['l_spot'])
#             self.laser.wavelength = self.tempstorage['l_spot']
        
    def __sweep_questions__(self, skipq=False):
        '''Ask the user a number of questions about wavelength sweep settings
        and current DUT. Answers are stored in self.tempstorage dictionary.
        
        Returns: True if all questions have been answered, False if some
            answer was 'q'.
        '''
        if skipq != True:
            while 1:
                try:
                    if 'l_start' in self.tempstorage.keys():
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('start wavelength [nm] (default %s) (q to quit, enter to accept): ' % self.tempstorage['l_start']), self.menutimeout).result
                        #usr_keys = raw_input("start wavelength [nm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_start'])
                        if not usr_keys in ['', None]:
                            l_start = float(usr_keys)*NANOMETER
                            self.tempstorage['l_start'] = l_start
                    else:
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('start wavelength [nm] (q to quit): '), self.menutimeout).result
                        #usr_keys = raw_input("start wavelength [nm] (q to quit): ")
                        if not usr_keys in [None]:
                            l_start = float(usr_keys)*NANOMETER
                            self.tempstorage['l_start'] = l_start
                    break
                except:
                    if usr_keys == 'q':
                        return False
                    #stay in the while loop until user has entered valid numbers
                    print 'Please type a number.'
            while 1:
                try:
                    if 'l_span' in self.tempstorage.keys():
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('wavelength span [nm] (default %s) (q to quit, enter to accept): ' % self.tempstorage['l_span']), self.menutimeout).result
                        #usr_keys = raw_input("wavelength span [nm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_span'])
                        if not usr_keys in [None, '']:
                            l_span = float(usr_keys)*NANOMETER
                            self.tempstorage['l_span'] = l_span
                    else:
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('wavelength span [nm] (q to quit): '), self.menutimeout).result
                        #usr_keys = raw_input("wavelength span [nm] (q to quit): ")
                        if not usr_keys in [None]:
                            l_span = float(usr_keys)*NANOMETER
                            self.tempstorage['l_span'] = l_span
                    break
                except:
                    if usr_keys == 'q':
                        return False
                    #stay in the while loop until user has entered valid numbers
                    print 'Please type a number.'
            while 1:
                try:
                    if 'l_step' in self.tempstorage.keys():
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input("wavelength resolution [nm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_step']), self.menutimeout).result
                        #usr_keys = raw_input("wavelength resolution [nm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_step'])
                        if not usr_keys in [None, '']:
                            l_step = float(usr_keys)*NANOMETER
                            self.tempstorage['l_step'] = l_step
                    else:
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('wavelength resolution [nm] (q to quit): '), self.menutimeout).result
                        #usr_keys = raw_input("wavelength resolution [nm] (q to quit): ")
                        if not usr_keys in [None,]:
                            l_step = float(usr_keys)*NANOMETER
                            self.tempstorage['l_step'] = l_step
                    break
                except:
                    if usr_keys == 'q':
                        return False
                    #stay in the while loop until user has entered valid numbers
                    print 'Please type a number.'
            while 1:
                try:
                    if 'l_power' in self.tempstorage.keys():
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input("laser power [dBm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_power']), self.menutimeout).result
                        #usr_keys = raw_input("laser power [dBm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_power'])
                        if not usr_keys == '':
                            l_power = float(usr_keys)*DBM
                            self.tempstorage['l_power'] = l_power
                    else:
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input('laser power [dBm]  (q to quit): '), self.menutimeout).result
                        #usr_keys = raw_input("laser power [dBm]  (q to quit): ")
                        l_power = float(usr_keys)*DBM
                        self.tempstorage['l_power'] = l_power
                    break
                except:
                    if usr_keys == 'q':
                        return False
                    #stay in the while loop until user has entered valid numbers
                    print 'Please type a number.'
            while 1:
                try:
                    if 'l_powerrange' in self.tempstorage.keys():
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input("Measurement power range (-20,-10,0,10) [dBm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_powerrange']), self.menutimeout).result
                        #usr_keys = raw_input("Measurement power range (-20,-10,0,10) [dBm] (default %s) (q to quit, enter to accept): " % self.tempstorage['l_powerrange'])
                        if not usr_keys == '':
                            l_powerrange = float(usr_keys)*DBM
                            self.tempstorage['l_powerrange'] = l_powerrange
                    else:
                        usr_keys = FiniteWaitForKBInput(lambda: raw_input("Measurement power range (-20,-10,0,10) [dBm] (q to quit): "), self.menutimeout).result
                        #usr_keys = raw_input("Measurement power range (-20,-10,0,10) [dBm] (q to quit): ")
                        l_powerrange = float(usr_keys)*DBM
                        self.tempstorage['l_powerrange'] = l_powerrange
                    if not self.tempstorage['l_powerrange'] in [-20*DBM, -10*DBM, 0*DBM, 10*DBM]:
                        print 'Please choose from -20, -10, 0 or 10.' 
                    break
                except:
                    if usr_keys == 'q':
                        return False
                    #stay in the while loop until user has entered valid numbers
                    print 'Please type a number.'
        if not self.tempstorage['currentdevice'] is None:
            dev_name = FiniteWaitForKBInput(lambda: raw_input("name of the device (default %s) (q to quit, return to accept default): " % self.tempstorage['currentdevice']), self.menutimeout).result
            #dev_name = raw_input("name of the device (default %s) (q to quit, return to accept default): " % self.tempstorage['currentdevice'])
            if dev_name == 'q':
                return False
            elif not dev_name == '':
                self.tempstorage['currentdevice'] = dev_name
        else:
            dev_name = FiniteWaitForKBInput(lambda: raw_input('name of the device (q to quit): '), self.menutimeout).result
            #dev_name = raw_input("name of the device (q to quit): ")
            if dev_name == 'q':
                return False
            else:
                self.tempstorage['currentdevice'] = dev_name
        if not self.tempstorage['currenttestsite'] is None:
            site_name = FiniteWaitForKBInput(lambda: raw_input("name of the test site (default %s) (q to quit, return to accept default): " % self.tempstorage['currenttestsite']), self.menutimeout).result
            #site_name = raw_input("name of the test site (default %s) (q to quit, return to accept default): " % self.tempstorage['currenttestsite'])
            if site_name == 'q':
                return False
            elif not site_name == '':
                self.tempstorage['currenttestsite'] = site_name
        else:
            site_name = FiniteWaitForKBInput(lambda: raw_input('name of the test site (q to quit): '), self.menutimeout).result
            #site_name = raw_input("name of the test site (q to quit): ")
            if site_name == 'q':
                return False
            else:
                self.tempstorage['currenttestsite'] = site_name
        if ('comment' in self.tempstorage.keys()) and (not self.tempstorage['comment'] is None):
            comment = FiniteWaitForKBInput(lambda: raw_input("comments (default: %s - q to quit - enter to confirm - 'None' to remove): " % self.tempstorage['comment']), self.menutimeout).result
            #comment = raw_input("comments (default: %s - q to quit - enter to confirm - 'None' to remove): " % self.tempstorage['comment'])
            if comment.lower() == 'none':
                self.tempstorage['comment'] = None
            elif comment == 'q':
                return False
            elif not comment == '':
                self.tempstorage['comment'] = comment
        else:
            comment = FiniteWaitForKBInput(lambda: raw_input('comments (optional - q to quit): '), self.menutimeout).result
            #comment = raw_input("comments (optional - q to quit): ")
            if comment == 'q':
                return False
            elif comment == '':
                self.tempstorage['comment'] = None
            else:
                self.tempstorage['comment'] = comment
        return True
    
    def __get_currentdiecoordinates__(self, reference='Home'):
        '''Return the wafer stage coordinates of the home device on the current
        die, relative to a given reference position.
        Args:
        -reference (str): by default this is 'Home', i.e. wafer stage 
            coordinates are relative to the home die. Other option is 'center', 
            i.e. coordinates are relative to the center of the wafer stage.
        '''
        if self.MeasurementTree.Wafer.Rotated180:
            xwafer_abs = -(self.MeasurementTree.Wafer.CurrentDie[1]-self.MeasurementTree.Wafer.HomeDie[1])*self.MeasurementTree.DieSizeX.get_value(MICROMETER)
            ywafer_abs = -(self.MeasurementTree.Wafer.CurrentDie[0]-self.MeasurementTree.Wafer.HomeDie[0])*self.MeasurementTree.DieSizeY.get_value(MICROMETER)
        else:
            xwafer_abs = (self.MeasurementTree.Wafer.CurrentDie[1]-self.MeasurementTree.Wafer.HomeDie[1])*self.MeasurementTree.DieSizeX.get_value(MICROMETER)
            ywafer_abs = (self.MeasurementTree.Wafer.CurrentDie[0]-self.MeasurementTree.Wafer.HomeDie[0])*self.MeasurementTree.DieSizeY.get_value(MICROMETER)
        if reference == 'Center':
            #return coordinates relative to wafer stage center:
            if self.A.__class__ == ImecAutomaticSetup:
                #relative position of 'home' location to 'center' location:
                xc = -self.A.TABLE.XHome
                yc = -self.A.TABLE.YHome
            elif self.A.__class__ == Imec300AutomaticSetup:
                #relative position of 'home' location to 'center' location:
                XYc = self.A.TABLE.CenterXY
                XYh = self.A.TABLE.HomeXY
                xc = XYh.X - XYc.X
                yc = XYh.Y - XYc.Y
            xwafer_abs += xc
            ywafer_abs += yc
        angle_ideal = math.atan2(xwafer_abs, ywafer_abs) #angle between horizontal line and line between zero position and (xwafer_abs, ywafer_abs)
        angle_actual = angle_ideal - self.MeasurementTree.Wafer.RotationAngle
        waferdist = math.sqrt(xwafer_abs**2+ywafer_abs**2)
        xwafer_act = waferdist*math.sin(angle_actual)
        ywafer_act = waferdist*math.cos(angle_actual)
        return (xwafer_act, ywafer_act)
    
    def __step_to_reticle__(self, row, col):
        #first move the fibres up by 500um
        self.A.move_rel_LR((0,0,0.5), (0,0,0.5))
        if self.MeasurementTree.Wafer.Rotated180:
            xwafer_abs = -(col-self.MeasurementTree.Wafer.HomeDie[1])*self.MeasurementTree.DieSizeX.get_value(MICROMETER)
            ywafer_abs = -(row-self.MeasurementTree.Wafer.HomeDie[0])*self.MeasurementTree.DieSizeY.get_value(MICROMETER)
        else:
            xwafer_abs = (col-self.MeasurementTree.Wafer.HomeDie[1])*self.MeasurementTree.DieSizeX.get_value(MICROMETER)
            ywafer_abs = (row-self.MeasurementTree.Wafer.HomeDie[0])*self.MeasurementTree.DieSizeY.get_value(MICROMETER)
        print 'Stepping to die (', row, ',', col, ') with absolute coordinates (', xwafer_abs, ',', ywafer_abs,').'
        #correct coordinates of the reticle for rotation of the wafer
        angle_ideal = math.atan2(xwafer_abs, ywafer_abs) #angle between horizontal line and line between zero position and (xwafer_abs, ywafer_abs)
        angle_actual = angle_ideal - self.MeasurementTree.Wafer.RotationAngle
        waferdist = math.sqrt(xwafer_abs**2+ywafer_abs**2)
        xwafer_act = waferdist*math.sin(angle_actual)
        ywafer_act = waferdist*math.cos(angle_actual)
        try:
            self.A.move_wafer_Separation()
            try:
                self.A.move_abs_wafer(xwafer_act, ywafer_act)
                self.MeasurementTree.Wafer.CurrentDie = (row,col)
            except:
                raise
            self.A.move_wafer_Contact()
        except ResponseError:
            print 'Error during wafer chuck movement!'
            pass
        except:
            raise
        #lower fibres again to initial height
        self.A.move_rel_LR((0,0,-0.5), (0,0,-0.5))
    
    def __switch_light__(self):
        if self.A.__class__ == ImecAutomaticSetup:
            if self.A.TABLE.Light:
                self.A.TABLE.Light = False
            else:
                self.A.TABLE.Light = True
        else:
            print 'Microscope light not implemented for this setup.'
    
    def are_you_sure(self, query = 'Are you sure?'):
        r = FiniteWaitForKBInput(lambda: raw_input(query + ' (y/n): '), self.menutimeout).result
        #r = raw_input(query + ' (y/n): ')
        if r is None:
            return False
        elif r == 'y':
            return True
        else:
            return False
            
    def walk_device(self, site_index, device, settings_list):
        ''' 
        This function executes all wafer and fibre stage movements needed for a given device. 
        The function looks a the device.PortCombos property to find out which port and pad combinations need to be measured, 
        moves the appropriate stages, performs a fibre alignment if requested to do so and waits for a measurement sequence
        to finish before moving on to the next set of grating couplers/probe pads.
        Input arguments: 
        -site_index (int): index of the current test site in self.MeasurementTree.TestSites
        -device (Device): the currently measured device from the DeviceCatalog
        -settings_list (list): a list with MeasurementSetting objects for each PortCombo in device.PortCombos
        '''
        #preparatory work: look for the TestSite object and for the 'reference'
        #port combo. The 'reference' port combo is defined as follows:
        #1- default: reference = very first port combo of the first device 
        #    in this test site. This implies that there is only one reference
        #    in the entire test site (no matter how many devices there are in
        #    the test site).
        #2- if manually enabled in the code below: 'reference' = the first 
        #    port combo of the device that is currently being measured. This 
        #    implies that each device in the test site has its own reference.
        testsite = self.MeasurementTree.TestSites[site_index]
        if 1:
            reference_device_name = testsite.DUTs[0].Name
            #the name of this reference device in the device catalog:
            device_catalog_name = self.MeasurementTree.Mask + '_' + \
                                    testsite.Name + '_' + reference_device_name
            #the actual Device object from the DeviceCatalog:
            reference_device = self.devices[device_catalog_name]
            #below is the first port combo that was (or is) being measured in  
            #the current test site:
            reference_portcombo_name = reference_device.PortCombos[0].Left
        else:
            #reference_device_name = device.design.DesignInfo.Name
            reference_device = device
            reference_portcombo_name = reference_device.PortCombos[0].Left
        
        #if self.MeasurementTree.Wafer.Rotated180 == False:
        for pix, p in enumerate(device.PortCombos):
            #create info dictionary to pass to alignment method
            algn_inf = dict()
            algn_inf['lot'] = self.MeasurementTree.Wafer.BatchID
            algn_inf['wafer'] = self.MeasurementTree.Wafer.WaferID
            algn_inf['dierow'] = self.MeasurementTree.Wafer.CurrentDie[0]
            algn_inf['diecol'] = self.MeasurementTree.Wafer.CurrentDie[1]
            algn_inf['site'] = testsite.Name
            algn_inf['device'] = device.Design.DesignInfo.Name
            algn_inf['L'] = p.Left
            algn_inf['R'] = p.Right
            ''' lookup the MeasurementSetting object for this specific device&portcombo '''
            msett = settings_list[pix]
            if (msett == None):
                #this portcombo does not need to be measured
                continue #continue with the next portcombo
            else:
                alignset = msett.AlignSet
            if (testsite.DynamicAlignWL == True):
                #look for the wavelength at which the very first port combo in this
                #test site was aligned:
                L = SearchObjectListForFieldValue(reference_device.Design.DesignInfo.L, 'Name', 
                                                  reference_portcombo_name)
                first_wl =  L.AlignmentInfo.AlignWavelength
                if first_wl is None:
                    #the first port combo of the reference device has
                    #not been measured yet (i.e.: we are measuring it right now!)
                    first_wl = alignset.AlignL
            else:
                #use the alignment wavelength in the settings object:
                first_wl = alignset.AlignL 
            '''force laser wavelength to first_wl'''
            self.select_laser(first_wl)
            if not self.laser.laser_active == 1:
                self.laser.laser_active = 'ON'
            self.laser.power = alignset.AlignP
            #self.laser.wavelength = first_wl
            '''set polarization state'''
            if (not self.epc is None) and (self.epc.Remote == True):
                try:
                    msg = ("Adjusting polarization to %s " % p.Polarization,
                           "at %dnm." % msett.AlignSet.AlignL.get_value(NANOMETER))
                    print ''.join(x for x in msg)
                    self.epc.__get_heater_voltages__(p.Polarization, 
                                                 msett.AlignSet.AlignL.get_value(NANOMETER))
                    time.sleep(2.5)
                except NoHeaterCalibrationData:
                    msg = ("No EPC calibration data found for this port combo!")
                    print ''.join(x for x in msg)
                except ErrorWithCode, e:
                    msg = ("EPC error %d: %s!" % (e.code, e.message))
                    print ''.join(x for x in msg)
            ''' adjust wafer position for probing '''
            if (p.Probe == None):
                P = SearchObjectListForFieldValue(device.Design.DesignInfo.P, 'Name', 'NC') #this is the CouplerInfo object for the probe pad we need to move towards
            else:
                P = SearchObjectListForFieldValue(device.Design.DesignInfo.P, 'Name', p.Probe) #this is the CouplerInfo object for the probe pad we need to move towards
            if P == None:
                raise NameError('The probe site with name ' + p.Probe + ' was not found in the definition of device ' + device.Design.DesignInfo.Name)
            probefromdiehome = P.RelativePosition.rotate(-self.MeasurementTree.Wafer.RotationAngle) #the desired displacement of the wafer from the die's home position
            if (pix == 0) | (p.Probe != device.PortCombos[pix-1].Probe):
                ''' if we are at the first PortCombo, or if the name of the current probe site is different from the previous probe site, we will perform a movement '''
                CurrentDiePosition = self.__get_currentdiecoordinates__(reference='Home')
                if self.MeasurementTree.DisableChuck == False:
                    try:
                        self.tempstorage['chuck_movements']+=1
                        self.A.move_abs_wafer(CurrentDiePosition[0]+probefromdiehome.X, CurrentDiePosition[1]+probefromdiehome.Y)
                    except ResponseError:
                        print 'Error during chuck movement!'
                        continue
                    except:
                        continue
                ''' fill in the absolute wafer stage coordinates in the P object '''
                CurrentDiePosition_fromcenter = self.__get_currentdiecoordinates__(reference='Center')
                P.AlignmentInfo.AlignedPosition = XYZ(CurrentDiePosition_fromcenter[0]+probefromdiehome.X, 
                                                      CurrentDiePosition_fromcenter[1]+probefromdiehome.Y, 0)
            ''' adjust left and right fibre '''
            if self.MeasurementTree.Wafer.Rotated180:
                L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', p.Right) #this is the CouplerInfo object for the left grating
            else:
                L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', p.Left) #this is the CouplerInfo object for the left grating
            if L == None:
                raise NameError('The left grating with name ' + p.Left + ' was not found in the definition of device ' + device.Design.DesignInfo.Name)
            if self.MeasurementTree.Wafer.Rotated180:
                R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', p.Left) #this is the CouplerInfo object for the right grating
            else:
                R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', p.Right) #this is the CouplerInfo object for the right grating
            if R == None:
                raise NameError('The right grating with name ' + p.Right + ' was not found in the definition of device ' + device.Design.DesignInfo.Name)
            if (pix == 0) | ((p.Left != device.PortCombos[pix-1].Left) & (p.Right != device.PortCombos[pix-1].Right)) | (p.Probe != device.PortCombos[pix-1].Probe):
                ''' this is the first portcombo we are measuring, or both left and right grating are different from the previous gratings, or we are probing a different bondpad '''
                if self.MeasurementTree.DisableChuck == False:
                    #move the fibers and wait until movement is finished:
                    self.move_fibres_LR(L, R, probefromdiehome, async=False)
                else:
                    self.move_fibres_LR(L, R, PXY(0.0,0.0), async=False)
                #measure power at the detector. If power is less than -36dBm,
                #we will align twice in order to achieve better results
                #self.analog_source.PM.range_auto = True
                #time.sleep(1.0)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except ValueError:
                    #if something goes wrong while reading out the power meter,
                    #let's play safe and force aligntwice=True
                    Pwr = -40
                #print 'Power after stepping: ', Pwr
                #time.sleep(1.0)
                #Pwr = self.analog_source.get_power().get_value()
                #print 'Power after stepping: ', Pwr
                if Pwr < -36:
                    aligntwice = True
                else:
                    aligntwice = False
                #print aligntwice
                if (alignset.FibreRange != 0.0) & (p.BlindStep != True):
                    self.sensor1.wavelength = first_wl
                    self.align_fibres_LR(device, p, probefromdiehome, align_wavelength = first_wl, align_travel = alignset.FibreRange, 
                                         align_velocity = alignset.FibreSpeed,
                                         nbr_turns=alignset.NbrTurns,
                                         info=algn_inf)
                    if aligntwice == True:
                        #repeat the alignment
                        self.align_fibres_LR(device, p, probefromdiehome, align_wavelength = first_wl, 
                                             align_travel = alignset.FibreRange, 
                                             align_velocity = alignset.FibreSpeed,
                                             nbr_turns=alignset.NbrTurns,
                                             info=algn_inf)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except ValueError:
                    #Pwr = 'NaN'
                    #print 'Power after alignment: ', Pwr
                    pass
            elif ((self.MeasurementTree.Wafer.Rotated180 == False) and (p.Left != device.PortCombos[pix-1].Left)) or ((self.MeasurementTree.Wafer.Rotated180 == True) and (p.Right != device.PortCombos[pix-1].Right)):
                ''' only the left grating is different from the previous PortCombo '''
                if self.MeasurementTree.DisableChuck == False:
                    self.move_fibre_L(L, probefromdiehome)
                else:
                    self.move_fibre_L(L, PXY(0.0,0.0))
                #measure power at the detector. If power is less than -36dBm,
                #we will align twice in order to achieve better results
                #self.analog_source.PM.range_auto = True
                #time.sleep(1.0)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except ValueError:
                    #if something goes wrong while reading out the power meter,
                    #let's play safe and force aligntwice=True
                    Pwr = -40
                if Pwr < -36:
                    aligntwice = True
                else:
                    aligntwice = False
                if (alignset.FibreRange != 0.0) & (p.BlindStep != True):
                    self.sensor1.wavelength = first_wl
                    self.align_fibre_L(device, p, probefromdiehome, 
                                       align_wavelength = first_wl, 
                                       align_travel = alignset.FibreRange, 
                                       align_velocity = alignset.FibreSpeed,
                                       nbr_turns=alignset.NbrTurns,
                                       info=algn_inf)
                    if aligntwice == True:
                        self.align_fibre_L(device, p, probefromdiehome, 
                                           align_wavelength = first_wl, 
                                           align_travel = alignset.FibreRange, 
                                           align_velocity = alignset.FibreSpeed,
                                           nbr_turns=alignset.NbrTurns,
                                           info=algn_inf)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except:
                    #Pwr = 'NaN'
                    #print 'Power after alignment: ', Pwr
                    pass
            else:
                ''' only the right grating is different from the previous PortCombo '''
                if self.MeasurementTree.DisableChuck == False:
                    self.move_fibre_R(R, probefromdiehome)
                else:
                    self.move_fibre_R(R, PXY(0.0,0.0))
                #measure power at the detector. If power is less than -36dBm,
                #we will align twice in order to achieve better results
                #self.analog_source.PM.range_auto = True
                #time.sleep(1.0)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except:
                    Pwr = -40
                if Pwr < -36:
                    aligntwice = True
                else:
                    aligntwice = False
                if (alignset.FibreRange != 0.0) & (p.BlindStep != True):
                    self.sensor1.wavelength = first_wl
                    self.align_fibre_R(device, p, probefromdiehome, 
                                       align_wavelength = first_wl, 
                                       align_travel = alignset.FibreRange, 
                                       align_velocity = alignset.FibreSpeed,
                                       nbr_turns=alignset.NbrTurns,
                                       info=algn_inf)
                    if aligntwice == True:
                        self.align_fibre_R(device, p, probefromdiehome, 
                                           align_wavelength = first_wl, 
                                           align_travel = alignset.FibreRange, 
                                           align_velocity = alignset.FibreSpeed,
                                           nbr_turns=alignset.NbrTurns,
                                           info=algn_inf)
                try:
                    Pwr = self.analog_source.get_power().get_value()
                except:
                    #Pwr = 'NaN'
                    #print 'Power after alignment: ', Pwr
                    pass
            self.tempstorage['currentdevice'] = device.Design.DesignInfo.Name
            self.tempstorage['currenttestsite'] = device.Design.TestSiteInfo.Name
            self.tempstorage['leftgrating_name'] = L.Name
            self.tempstorage['rightgrating_name'] = R.Name
            self.tempstorage['probepad_name'] = P.Name
            if p.SnapImage:
                self.A.SnapImage(self.MeasurementTree.StorageFolder + os.sep + \
                                 self.MeasurementTree.Wafer.BatchID + '_' + \
                                 self.MeasurementTree.Wafer.WaferID + '_' + \
                                 self.MeasurementTree.Mask + '_' + \
                                 self.MeasurementTree.Wafer.CurrentDie + '_' + \
                                 testsite.Name + '_' + \
                                 device.Design.DesignInfo.Name + '_' + \
                                 p.Left + '_' + p.Right + '_' + p.Probe + \
                                 '.jpg')
                
            ''' at this point, the fibres have been aligned. 
            we should now look for the wavelength with highest transmission
            and re-align the fibers 
            '''
            if (testsite.DynamicAlignWL == True) and (device == reference_device) and (pix == 0) and (p.BlindStep == False) and (alignset.FibreRange != 0.0):
                #we are now measuring the 1st portcombo of the reference device.
                #Since DynamicAlignWL is True, we need to perform a wavelength 
                #sweep and re-align the fibers at the peak wavelength.
                fast_X, fast_Y, sweep_power = self.continuous_sweep(start_wavelength = alignset.LStart, scan_range = alignset.LSpan, resolution_wavelength=alignset.LStep, averaging_time = alignset.AvgTime, sensor_range = p.MeasurePwrRng, laser_power=msett.LPower)
                self.tempstorage['wavelength_sweeps']+=1
                #sweep has been done, we need to look for the peak wavelength:
                peak_wl, peak_pw, P, _, _ = FindPolyFittedMax(fast_X, fast_Y, 
                      FilterMode='Mean', FitOrder=2, Smoothing=2, FitRange=0.2)
                lo = alignset.LStart.get_value(NANOMETER)
                hi = lo + alignset.LSpan.get_value(NANOMETER)
                #print peak_wl, lo, hi, peak_pw
                if (not peak_wl is None) and (lo <= peak_wl <= hi) and (peak_pw > -40):
                    #peak detection succeeded 
                    #re-align the fibers at the detected peak wavelength:
                    self.sensor1.wavelength = peak_wl*NANOMETER
                    self.align_fibres_LR(device, p, probefromdiehome, 
                                         align_wavelength = peak_wl*NANOMETER, 
                                         align_travel = alignset.FibreRange, 
                                         align_velocity = alignset.FibreSpeed,
                                         nbr_turns=alignset.NbrTurns,
                                         onlysmall=True)
                    try:
                        Pwr = self.analog_source.get_power().get_value()
                    except:
                        Pwr = -40
                    #print 'Power after re-alignment at peak wl: ', Pwr
                else:
                    peak_wl = None
            elif (p.AlignAtPeakWL == True) and (p.BlindStep == False) and (alignset.FibreRange != 0.0): #and ((not device == reference_device) or (not pix == 0))
                #this is not the first port combo of the reference device 
                #(or: if DynamicAlignWL attribute of the test site is False,
                #this could be the first port combo fo the reference device) 
                #AlignAtPeakWL is True: we need to re-align the fibers at the
                #peak wavelength:
                fast_X, fast_Y, sweep_power = self.continuous_sweep(start_wavelength = alignset.LStart, scan_range = alignset.LSpan, resolution_wavelength=alignset.LStep, averaging_time = alignset.AvgTime, sensor_range = p.MeasurePwrRng, laser_power=msett.LPower)
                self.tempstorage['wavelength_sweeps']+=1
                #sweep has been done, we need to look for the peak wavelength:
                peak_wl, peak_pw = self.__detect_peakwl__(msett.DeviceType, 
                                                      fast_X, fast_Y, first_wl)
                lo = alignset.LStart.get_value(NANOMETER)
                hi = lo + alignset.LSpan.get_value(NANOMETER)
                #print 'core 2957 - peak wl: %s' % repr(peak_wl)
                if (not peak_wl is None) and (lo <= peak_wl <= hi) and (peak_pw > -40):
                    #peak detection succeeded 
                    self.sensor1.wavelength = peak_wl*NANOMETER
                    #re-align the fibers at the detected peak wavelength:
                    self.align_fibres_LR(device, p, probefromdiehome, 
                                         align_wavelength = peak_wl*NANOMETER, 
                                         align_travel = alignset.FibreRange, 
                                         align_velocity = alignset.FibreSpeed,
                                         nbr_turns=alignset.NbrTurns,
                                         onlysmall=True)
                    try:
                        Pwr = self.analog_source.get_power().get_value()
                    except:
                        #Pwr = 'NaN'
                        #print 'Power after re-alignment at peak wl: ', Pwr
                        pass
                else:
                    peak_wl = None
            else:
                peak_wl = alignset.AlignL.get_value(NANOMETER)
            self.sensor1.wavelength = self.MeasurementTree.DefaultWavelength
            yield p, peak_wl, probefromdiehome, msett, (pix+1, len(device.PortCombos))
    
    ############################################################################################################        

    # movements in Relative coordinates
    def move_fibres_LR(self, L, R, probefromdiehome, async=True):
        '''
        This function moves both the left and right fibre stages to the gratings defined by the CouplerInfo objects L and R, respectively.
        probefromdiehome is a PXY object giving the physical position of the waferstage relative to the die's home position
        (die home = first probe pad of the first registered device).
        '''
        best_neighbour, neighbourdistance = self.find_best_neighbour(L) #the best_neighbour is the nearest left grating to which the fibre has been successfully aligned in the past
        L_abs = self.predict_fibrestage_coordinates(best_neighbour, L, probefromdiehome, neighbourdistance)
        print 'predicted left fibre position:', L_abs, 'best neighbour:', best_neighbour, 'is at', neighbourdistance
        best_neighbour, neighbourdistance = self.find_best_neighbour(R) #the best_neighbour is the nearest right grating to which the fibre has been successfully aligned in the past
        R_abs = self.predict_fibrestage_coordinates(best_neighbour, R, probefromdiehome, neighbourdistance)
        #print L_abs, R_abs
        self.tempstorage['left_movements']+=1
        self.tempstorage['right_movements']+=1
        try:
            self.A.move_abs_LR(L_abs, R_abs, async=async)
        except InstrumentValueError, e:
            print e.message
        #initialize values in L and R.AlignmentInfo (these may be overwritten during alignment)
        #we will only do this if the destination coupler is different from the best_neighbour
        #if neighbourdistance > 1.0:
        L.AlignmentInfo.AlignSuccess = False
        L.AlignmentInfo.FibreShift = XYZ(0,0,0)
        L.AlignmentInfo.AlignedPosition = L_abs
        L.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        L.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie
        R.AlignmentInfo.AlignSuccess = False
        R.AlignmentInfo.FibreShift = XYZ(0,0,0)
        R.AlignmentInfo.AlignedPosition = R_abs
        R.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        R.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie

    def move_fibre_L(self, L, probefromdiehome):
        '''
        This function moves the left fibre stage to the grating defined by the CouplerInfo object L.
        probefromdiehome is a PXY object giving the physical position of the waferstage relative to the die's home position
        (die home = first probe pad of the first registered device).
        '''
        best_neighbour, neighbourdistance = self.find_best_neighbour(L) #the best_neighbour is the nearest left grating to which the fibre has been successfully aligned in the past
        L_abs = self.predict_fibrestage_coordinates(best_neighbour, L, probefromdiehome, neighbourdistance)
        self.tempstorage['left_movements']+=1
        self.A.move_abs_L(*L_abs)
        #initialize values in L.AlignmentInfo (these may be overwritten during alignment)
        L.AlignmentInfo.AlignSuccess = False
        L.AlignmentInfo.FibreShift = XYZ(0,0,0)
        L.AlignmentInfo.AlignedPosition = L_abs
        L.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        L.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie

    def move_fibre_R(self, R, probefromdiehome):
        '''
        This function moves the right fibre stage to the grating defined by the CouplerInfo objects R.
        probefromdiehome is a PXY object giving the physical position of the waferstage relative to the die's home position
        (die home = first probe pad of the first registered device).
        '''
        best_neighbour, neighbourdistance = self.find_best_neighbour(R) #the best_neighbour is the nearest right grating to which the fibre has been successfully aligned in the past
        R_abs = self.predict_fibrestage_coordinates(best_neighbour, R, probefromdiehome, neighbourdistance)
        self.tempstorage['right_movements']+=1
        self.A.move_abs_R(*R_abs)
        #initialize values in R.AlignmentInfo (these may be overwritten during alignment)
        R.AlignmentInfo.AlignSuccess = False
        R.AlignmentInfo.FibreShift = XYZ(0,0,0)
        R.AlignmentInfo.AlignedPosition = R_abs
        R.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        R.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie

    def predict_fibrestage_coordinates(self, neighbour_coupler, destination_coupler, probefromdiehome, neighbourdistance):
        '''
        This function calculates the fibre stage coordinates that should set the fibre exactly above the destination_coupler, based on a past successful alignment
        above a neighbour_coupler and the current wafer stage position given in probefromdiehome.
        Important note: For the left fibre stage, the x axis points right, the y axis points towards the front of the setup.
                        For the right fibre stage, the x axis points left and the y axis points towards the front of the setup.
                        Hence the difference in signs when adding/subtracting the destination_coupler's and neighbour_coupler's RelativePosition to the previously aligned position.
        '''
        print 'destination coupler: ', destination_coupler.Name
        #print self.L_rotation_rad
#         print 'best neighbour', neighbour_coupler.Name, 'is at a distance of', neighbourdistance
        if destination_coupler.Type.lower() == 'left':
            t = destination_coupler.RelativePosition.rotate(-self.L_rotation_rad) #-self.MeasurementTree.Wafer.RotationAngle)
            t2 = neighbour_coupler.RelativePosition.rotate(-self.L_rotation_rad) #-self.MeasurementTree.Wafer.RotationAngle)
        else:
            #print self.R_rotation_rad
            t = destination_coupler.RelativePosition.rotate(-self.R_rotation_rad) # -self.MeasurementTree.Wafer.RotationAngle)
#             print 'y correction: ', t.Y
            t2 = neighbour_coupler.RelativePosition.rotate(-self.R_rotation_rad) # -self.MeasurementTree.Wafer.RotationAngle)
        waferhome, lfibrehome, rfibrehome = self.__get_start_pos__()
        if destination_coupler.Type.lower() == 'left':
            x_fl2 = neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000 - probefromdiehome.X + neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X + t.X - t2.X
            y_fl2 = neighbour_coupler.AlignmentInfo.AlignedPosition.Y*1000 + probefromdiehome.Y - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.Y - t.Y + t2.Y
            #x_fl2 = -probefromdiehome.X + neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X + t.X - t2.X
            #y_fl2 = probefromdiehome.Y - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.Y - t.Y + t2.Y
            #x_fl3 = neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000 + x_fl2*math.cos(self.L_rotation_rad-self.MeasurementTree.Wafer.RotationAngle) - y_fl2*math.sin(self.L_rotation_rad-self.MeasurementTree.Wafer.RotationAngle)
            #y_fl3 = neighbour_coupler.AlignmentInfo.AlignedPosition.Y*1000 + x_fl2*math.sin(self.L_rotation_rad-self.MeasurementTree.Wafer.RotationAngle) + y_fl2*math.cos(self.L_rotation_rad-self.MeasurementTree.Wafer.RotationAngle)
            z_fl2 = lfibrehome[2]
        else:
            #print 'Neighbour - relative position x:', t2.X
            #print 'Neighbour - wafer stage x:', neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X #WaferStageFromDieHome
            #print 'Neighbour - alignstatus:', neighbour_coupler.AlignmentInfo.AlignSuccess
            #print 'Neighbour - aligned fibre stage x:', neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000
            #print 'Destination - relative position x:', t.X
            #print 'Destination - wafer stage x:', probefromdiehome.X
            x_fl2 = neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000 + probefromdiehome.X - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X - t.X + t2.X
            y_fl2 = neighbour_coupler.AlignmentInfo.AlignedPosition.Y*1000 + probefromdiehome.Y - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.Y - t.Y + t2.Y
            #x_fl2 = probefromdiehome.X - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X - t.X + t2.X
            #y_fl2 = probefromdiehome.Y - neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.Y - t.Y + t2.Y
            #x_fl3 = neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000 + x_fl2*math.cos(self.R_rotation_rad-self.MeasurementTree.Wafer.RotationAngle) - y_fl2*math.sin(self.R_rotation_rad-self.MeasurementTree.Wafer.RotationAngle)
            #y_fl3 = neighbour_coupler.AlignmentInfo.AlignedPosition.Y*1000 + x_fl2*math.sin(self.R_rotation_rad-self.MeasurementTree.Wafer.RotationAngle) + y_fl2*math.cos(self.R_rotation_rad-self.MeasurementTree.Wafer.RotationAngle)
            z_fl2 = rfibrehome[2]
        #print 'Destination - aligned fibre stage x prediction:', x_fl2, y_fl2
        if destination_coupler.Type.lower() == 'right':
            #override and try out a new method of predicting the fiber stage
            #coordinate, taking the rotational offset between the fiber stage's
            #coordinate system and the frame of the prober
            #sample coordinate of neighbour grating:
            xs1=neighbour_coupler.RelativePosition.X
            ys1=neighbour_coupler.RelativePosition.Y
            #wafer stage coordinate when probing neighbour grating:
            xw1=neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.X
            yw1=neighbour_coupler.AlignmentInfo.WaferStageFromDieHome.Y
            #fiber stage coordinate when probing neighbour grating:
            xf1=neighbour_coupler.AlignmentInfo.AlignedPosition.X*1000
            yf1=neighbour_coupler.AlignmentInfo.AlignedPosition.Y*1000
            #sample coordinate of destination grating:
            xs2=destination_coupler.RelativePosition.X
            ys2=destination_coupler.RelativePosition.Y
            #wafer stage coordinate when probing destination grating:
            xw2=probefromdiehome.X
            yw2=probefromdiehome.Y
            #calculate fiber stage coordinate for destination grating:
            #refer to scratch folder, stage_coordinate_transformation_draft
            #for more explanations:
            tf=self.R_rotation_rad-self.MeasurementTree.Wafer.RotationAngle+np.pi
            #tf: rotation of the right fiber stage, relative
            #to the wafer. We need to subtract the rotation angle between
            #the wafer and the wafer stage in order to obtain
            #the rotation angle between the fiber stage and a fixed reference 
            #frame (e.g. base of the prober)
            ts=self.MeasurementTree.Wafer.RotationAngle #angle between 
            #coordinate system fixed to the wafer and coordinate system fixed 
            #to tha base of the prober
            #the coordinate of the neighbour grating on the sample can be transformed into a coordinate
            #in a reference frame that is fixed to the base of the prober:
            xp1_s=xs1*np.cos(ts)-ys1*np.sin(ts)-xw1
            yp1_s=xs1*np.sin(ts)+ys1*np.cos(ts)-yw1

            #the coordinate of the fiber tip in the reference frame that is fixed to the 
            #prober:
            xp1_f=xf1*np.cos(tf)-yf1*np.sin(tf) #+ an unknown but fixed offset, 'A'
            yp1_f=xf1*np.sin(tf)+yf1*np.cos(tf) #+ an unknown but fixed offset, 'B'

            #we can calculate the translational offset between the origins of 'p' and 'f':
            A = xp1_s-xp1_f
            B = yp1_s-yp1_f

            #Given: sample coordinates of a second grating, and the step that is going
            #to be made by the wafer stage.
            #Asked: fiber stage coordinates that will bring the fiber tip above this second
            #grating
            
            #second grating position on sample:
            #xs2=3128e-6 #6578e-6
            #ys2=1378e-6
            #position to where the wafer stage will move:
            #xw2=4598e-6
            #yw2=1397e-6
            #the coordinate of the second grating  can be transformed into a coordinate
            #in a reference frame that is fixed to the base of the prober:
            xp2_s=xs2*np.cos(ts)-ys2*np.sin(ts)-xw2
            yp2_s=xs2*np.sin(ts)+ys2*np.cos(ts)-yw2
            #we can calculate xf2 and yf2 using the values of A and B determined above,
            #and by solving xp2_s=xp2_f, yp2_s=yp2_f
            #define two auxiliary terms:
            C=xp2_s-A
            D=yp2_s-B
            #finally we get xf2 and yf2:
            x_fl2 = C*np.cos(tf)+D*np.sin(tf)
            y_fl2 = D*np.cos(tf)-C*np.sin(tf)
            #print 'xf2:', xf2
            #print 'yf2:', yf2
            #z_fl2 = rfibrehome[2]
#             print 'x_r2:', x_fl2 
#             print 'y_r2:', y_fl2
        
        return XYZ(x_fl2/1000, y_fl2/1000, z_fl2)
    
    def find_best_neighbour(self, coupler):
        '''
        This function takes a CouplerInfo object as input and returns the nearest grating coupler in the device catalog to which the fibre has been successfully aligned.
        '''
        #check to see if the fibre has been aligned to this specific coupler before. If a successful alignment has been performed before, the absolute fibre stage coordinates
        #should have been stored in the coupler.AlignedPosition field (which is an LXY or an RXY object)
        d = self.MeasurementTree.Wafer.CurrentDie #die that is currently being probed
#         print 'current die:', d
        if (coupler.AlignmentInfo.AlignSuccess) & (d == coupler.AlignmentInfo.Die):
            #then the fibre has been successfully aligned to this coupler on this exact die
            best_neighbour = coupler
            dist = 0.0
        else:
            #an unsuccessful alignment (or no alignment at all) has been done in the past: look for another grating in the vicinity by browsing through the device catalog 
            #and checking each of the left or right couplers on all devices
#             print 'first alignment to this grating'
            ''' start by determining the type of coupler we are dealing with '''
            if coupler.Type.lower() == 'left':
                couplertype = 'L'
            elif coupler.Type.lower() == 'right':
                couplertype = 'R'
            else:
                raise NameError("find_best_neighbour expects either a left-type or right-type CouplerInfo object as input parameter!")
            dist = None  #initialize distance between 'coupler' and another grating from the device catalog
            best_neighbour = None #initialize the nearest sucessfully aligned grating
            for dk, dv in self.devices.items():
                for co in getattr(dv.Design.DesignInfo, couplertype):
                    co_distance = co.RelativePosition - coupler.RelativePosition
                    co_distance = co_distance.norm()
                    #print 'device', dv.Design.DesignInfo.Name, '- grating', co.Name, 'is at', co_distance, 'and has alignresult', co.AlignmentInfo.AlignSuccess
                    #print co_distance
                    #we need to add the distance from the current die to the die in which this grating was last aligned:
                    co_distance += math.sqrt(((co.AlignmentInfo.Die[0]-d[0])*self.MeasurementTree.DieSizeX.get_value(MICROMETER))**2+((co.AlignmentInfo.Die[1]-d[1])*self.MeasurementTree.DieSizeY.get_value(MICROMETER))**2)
                    #print co_distance
                    if ((dist == None) | (co_distance < dist)) & co.AlignmentInfo.AlignSuccess:
                        #we have found a coupler to which a fibre has been successfully aligned.
                        dist = co_distance
                        best_neighbour = co
                    if (dist != None) & (dist < 100):
                        #this is close enough, no need to look at other couplers in this device
                        break
                if (dist != None) & (dist < 100):
                    #close enough, no need to look at other devices
                    break
            if (dist == None):
                #we did not find a coupler to which the fibre was successfully aligned - this situation can only arise if alignment to the first set of gratings of the home device did not succeed 
                #(in which case the only couplers in the devicecatalog with AlingSuccess = True get overwritten with AlignSuccess = False) and if alignment at all subsequent portcombos also fails.
                #NOTE: this situation can also arise if alignments to all port combos on a previous die failed! All info in the device catalog will then have been overwritten!
                hd = self.devices.home_device()
                co_list = getattr(hd.Design.DesignInfo, couplertype)
                if (couplertype.lower() == 'l'):
                    if self.MeasurementTree.Wafer.Rotated180:
                        best_neighbour = SearchObjectListForFieldValue(co_list, 'Name', self.tempstorage['right_1st']) # co_list[0]
                    else:
                        best_neighbour = SearchObjectListForFieldValue(co_list, 'Name', self.tempstorage['left_1st']) # co_list[0]
                else:
                    if self.MeasurementTree.Wafer.Rotated180:
                        best_neighbour = SearchObjectListForFieldValue(co_list, 'Name', self.tempstorage['left_1st']) # co_list[0]
                    else:
                        best_neighbour = SearchObjectListForFieldValue(co_list, 'Name', self.tempstorage['right_1st']) # co_list[0]
                co_distance = best_neighbour.RelativePosition - coupler.RelativePosition
                co_distance = co_distance.norm()
                co_distance += math.sqrt(((best_neighbour.AlignmentInfo.Die[0]-d[0])*self.MeasurementTree.DieSizeX.get_value(MICROMETER))**2+((best_neighbour.AlignmentInfo.Die[1]-d[1])*self.MeasurementTree.DieSizeY.get_value(MICROMETER))**2)
                dist = co_distance
        return best_neighbour, dist
    
    def align_fibre_L(self, device, portcombo, probefromdiehome, 
                      align_wavelength = 1550*NANOMETER, 
                      align_travel = 10*MICROMETER, 
                      align_velocity = 10*MICROMETERPERSECOND,
                      nbr_turns=5,
                      onlysmall=False,
                      info=None):
        '''
        This function aligns the left fibre to the coupler given in portcombo.Left, 
        using the alignment settings given in align_wavelength, align_travel, align_velocity.
        Alignment results are stored in device.Design.DesignInfo.L[portcombo.Left].AlignmentInfo
        Args:
        -onlysmall (bool): if set to True, and if alignmethod is spiral: the 
            first, large spiral is skipped and only the second, smaller spiral
            is executed. Default is False.
        -info (dict): dictionary with lot, wafer, dierow, diecol, testsite, 
            device, left and right coupler name
        '''
        self.__align_wavelength__ = align_wavelength
        align_parameters = self.__prealign__() #this sets the laser wavelength to self.__align_wavelength__
        '''retrieve the power range from a previous alignment to this port 
        combo:'''
        L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', 
                                          portcombo.Left)
        finalpwrrange = L.AlignmentInfo.PwrRange
        if not finalpwrrange is None:
            print 'Power range from a previous alignment to this port: %s' % repr(finalpwrrange)
        else:
            #note: the finalpwrrange may be None if no alignment has happened before
            #to this grating. If an alignment has been done at some point in the past,
            #the final power range from that alignment is stored here.
            finalpwrrange = portcombo.AlignPwrRng
        if self.MeasurementTree.AlignMethod == 'cross':
            left_xyz, total_shift, errors, trajectorydata = self.__cross_align_fibre_L__(xtravel = align_travel, ytravel = align_travel, travelvelocity = align_velocity, expected_power = portcombo.AlignPwrRng)
        elif self.MeasurementTree.AlignMethod == 'spiral':
            left_xyz, total_shift, errors, trajectorydata, finalpwrrange = self.__spiral_align_fibre_L__(radius=align_travel, turns=nbr_turns, 
                                     velocity=align_velocity,
                                     expected_power=finalpwrrange,
                                     onlysmall=onlysmall,
                                     info=info)
        self.tempstorage['left_alignments'] += 1
        self.tempstorage['left_trajectories']+=len(trajectorydata)
        if self.MeasurementTree.Wafer.Rotated180:
            L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Right)
        else:
            L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Left)
        #L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Left)
        if (not errors):
            L.AlignmentInfo.AlignSuccess = True
            L.AlignmentInfo.FibreShift += total_shift
        else:
            L.AlignmentInfo.AlignSuccess = False
            L.AlignmentInfo.FibreShift = XYZ(0,0,0)
        L.AlignmentInfo.AlignedPosition = left_xyz
        L.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        L.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie
        L.AlignmentInfo.AlignWavelength = align_wavelength
        if not finalpwrrange is None:
            L.AlignmentInfo.PwrRange = finalpwrrange
        #L.AlignmentInfo.TrajectoryData = trajectorydata

    def align_fibre_R(self, device, portcombo, probefromdiehome, 
                      align_wavelength = 1550*NANOMETER, 
                      align_travel = 10*MICROMETER, 
                      align_velocity = 10*MICROMETERPERSECOND,
                      nbr_turns=5,
                      onlysmall=False,
                      info=None):
        '''
        This function aligns the right fibre to the coupler given in portcombo.Right, 
        using the alignment settings given in align_wavelength, align_travel, align_velocity.
        Alignment results are stored in device.Design.DesignInfo.R[portcombo.Right].AlignmentInfo
        Args:
        -onlysmall (bool): if set to True, and if alignmethod is spiral: the 
            first, large spiral is skipped and only the second, smaller spiral
            is executed. Default is False.
        -info (dict): dictionary with lot, wafer, dierow, diecol, testsite, 
            device, left and right coupler name
        '''
        self.__align_wavelength__ = align_wavelength
        align_parameters = self.__prealign__() #this sets the laser wavelength to self.__align_wavelength__
        '''retrieve the power range from a previous alignment to this port 
        combo:'''
        R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', 
                                          portcombo.Right)
        finalpwrrange = R.AlignmentInfo.PwrRange
        if not finalpwrrange is None:
            print 'Power range from a previous alignment to this port: %s' % repr(finalpwrrange)
        else:
            #note: the finalpwrrange may be None if no alignment has happened before
            #to this grating. If an alignment has been done at some point in the past,
            #the final power range from that alignment is stored here.
            finalpwrrange = portcombo.AlignPwrRng
        if self.MeasurementTree.AlignMethod == 'cross':
            right_xyz, total_shift, errors, trajectorydata = self.__cross_align_fibre_R__(xtravel = align_travel, ytravel = align_travel, travelvelocity = align_velocity, expected_power = portcombo.AlignPwrRng)
        elif self.MeasurementTree.AlignMethod == 'spiral':
            right_xyz, total_shift, errors, trajectorydata, finalpwrrange = self.__spiral_align_fibre_R__(radius=align_travel, turns=nbr_turns, 
                                     velocity=align_velocity,
                                     expected_power=finalpwrrange,
                                     onlysmall=onlysmall,
                                     info=info)
        self.tempstorage['right_alignments'] += 1
        self.tempstorage['right_trajectories']+=len(trajectorydata)
        if self.MeasurementTree.Wafer.Rotated180:
            R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Left)
        else:
            R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Right)
        #R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Right)
        if (not errors):
            R.AlignmentInfo.AlignSuccess = True
            R.AlignmentInfo.FibreShift += total_shift
        else:
            R.AlignmentInfo.AlignSuccess = False
            R.AlignmentInfo.FibreShift = XYZ(0,0,0)
        R.AlignmentInfo.AlignedPosition = right_xyz
        R.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        R.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie
        R.AlignmentInfo.AlignWavelength = align_wavelength
        #R.AlignmentInfo.TrajectoryData = trajectorydata
        if not finalpwrrange is None:
            R.AlignmentInfo.PwrRange = finalpwrrange
    
    def align_fibres_LR(self, device, portcombo, probefromdiehome, 
                        align_wavelength = 1550*NANOMETER, 
                        align_travel = 10*MICROMETER, 
                        align_velocity = 10*MICROMETERPERSECOND,
                        nbr_turns=5,
                        onlysmall=False,
                        info=None):
        '''
        This function aligns the left and right fibres to the couplers given in portcombo.Left and portcombo.Right, 
        using the alignment settings given in align_wavelength, align_travel, align_velocity.
        Alignment results are stored in device.Design.DesignInfo.L[portcombo.Left].AlignmentInfo and in
        device.Design.DesignInfo.R[portcombo.Right].AlignmentInfo
        Args:
        -onlysmall (bool): if set to True, and if alignmethod is spiral: the 
            first, large spiral is skipped and only the second, smaller spiral
            is executed. Default is False.
        -info (dict): dictionary with lot, wafer, dierow, diecol, testsite, 
            device, left and right coupler name
        '''
        self.__align_wavelength__ = align_wavelength
        #print 'in align_fibres_LR', align_wavelength
        align_parameters = self.__prealign__() #this sets the laser wavelength to self.__align_wavelength__
        '''retrieve the power range from a previous alignment to this port 
        combo:'''
        L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', 
                                          portcombo.Left)
        R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', 
                                          portcombo.Right)
        finalpwrrange = L.AlignmentInfo.PwrRange
        if not finalpwrrange is None:
            print 'Power range from a previous alignment to this port: %s' % repr(finalpwrrange)
        else:
            #note: the finalpwrrange may be None if no alignment has happened before
            #to this grating. If an alignment has been done at some point in the past,
            #the final power range from that alignment is stored here.
            finalpwrrange = portcombo.AlignPwrRng
        if self.MeasurementTree.AlignMethod == 'cross':
            left_xyz, total_shift, errors, trajectorydata = self.__cross_align_fibre_L__(xtravel = align_travel, ytravel = align_travel, travelvelocity = align_velocity, expected_power = portcombo.AlignPwrRng)
        elif self.MeasurementTree.AlignMethod == 'spiral':
            left_xyz, total_shift, errors, trajectorydata, finalpwrrange = self.__spiral_align_fibre_L__(radius=align_travel, turns=nbr_turns, 
                                     velocity=align_velocity,
                                     expected_power=finalpwrrange,
                                     onlysmall=onlysmall,
                                     info=info)
        self.tempstorage['left_alignments'] += 1
        self.tempstorage['left_trajectories']+=len(trajectorydata)
        if self.MeasurementTree.Wafer.Rotated180:
            L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Right)
        else:
            L = SearchObjectListForFieldValue(device.Design.DesignInfo.L, 'Name', portcombo.Left)
        if (not errors):
            L.AlignmentInfo.AlignSuccess = True
            L.AlignmentInfo.FibreShift += total_shift
        else:
            L.AlignmentInfo.AlignSuccess = False
            L.AlignmentInfo.FibreShift += XYZ(0,0,0)
        L.AlignmentInfo.AlignedPosition = left_xyz
        L.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        L.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie
        L.AlignmentInfo.AlignWavelength = align_wavelength
        #print L.AlignmentInfo.AlignWavelength
        #L.AlignmentInfo.TrajectoryData = trajectorydata
        if self.MeasurementTree.AlignMethod == 'cross':
            right_xyz, total_shift, errors, trajectorydata = self.__cross_align_fibre_R__(xtravel = align_travel, ytravel = align_travel, travelvelocity = align_velocity, expected_power = portcombo.AlignPwrRng)
        elif self.MeasurementTree.AlignMethod == 'spiral':
            right_xyz, total_shift, errors, trajectorydata, finalpwrrange = self.__spiral_align_fibre_R__(radius=align_travel, turns=nbr_turns, 
                                     velocity=align_velocity,
                                     expected_power=finalpwrrange,
                                     onlysmall=onlysmall,
                                     info=info)
        self.tempstorage['right_alignments'] += 1
        self.tempstorage['right_trajectories']+=len(trajectorydata)
        if self.MeasurementTree.Wafer.Rotated180:
            R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Left)
        else:
            R = SearchObjectListForFieldValue(device.Design.DesignInfo.R, 'Name', portcombo.Right)
        if (not errors):
            R.AlignmentInfo.AlignSuccess = True
            R.AlignmentInfo.FibreShift += total_shift
        else:
            R.AlignmentInfo.AlignSuccess = False
            R.AlignmentInfo.FibreShift += XYZ(0,0,0)
        R.AlignmentInfo.AlignedPosition = right_xyz
        R.AlignmentInfo.WaferStageFromDieHome = probefromdiehome
        R.AlignmentInfo.Die = self.MeasurementTree.Wafer.CurrentDie
        R.AlignmentInfo.AlignWavelength = align_wavelength
        '''write final power range to both left and right port'''
        #print 'core 2232 - final power range: %s' % finalpwrrange
        if not finalpwrrange is None:
            L.AlignmentInfo.PwrRange = finalpwrrange
            R.AlignmentInfo.PwrRange = finalpwrrange
    
    def __spiral_align_fibre_L__(self, radius=10*MICROMETER, turns=4, 
                                 velocity=100*MICROMETERPERSECOND,
                                 expected_power=-10*DBM, onlysmall=False,
                                 info=None):
        """Find optimum position of left fibre by describing a spiralling 
        motion.
        -onlysmall (bool): if set to True, and if alignmethod is spiral: the 
            first, large spiral is skipped and only the second, smaller spiral
            is executed. Default is False.
        -info (dict): dictionary with lot, wafer, dierow, diecol, testsite, 
            device, left and right coupler name
        """
        if not info is None:
            info['fiber'] = 'L'
        return align_spiral(self.A, self.analog_source, self.A.LEFT, 
             maxradius = radius.get_value(MICROMETER), 
             turns = turns, 
             micron_per_second = velocity.get_value(MICROMETERPERSECOND), 
             expected_power = expected_power,
             onlysmall=onlysmall,
             info=info)
    
    def __spiral_align_fibre_R__(self, radius=10*MICROMETER, turns=4, 
                                 velocity=100*MICROMETERPERSECOND,
                                 expected_power=-10*DBM, onlysmall=False,
                                 info=None):
        """Find optimum position of left fibre by describing a spiralling 
        motion.
        -onlysmall (bool): if set to True, and if alignmethod is spiral: the 
            first, large spiral is skipped and only the second, smaller spiral
            is executed. Default is False.
        -info (dict): dictionary with lot, wafer, dierow, diecol, testsite, 
            device, left and right coupler name
        """
        if not info is None:
            info['fiber'] = 'R'
        return align_spiral(self.A, self.analog_source, self.A.RIGHT, 
             maxradius = radius.get_value(MICROMETER), 
             turns = turns, 
             micron_per_second = velocity.get_value(MICROMETERPERSECOND), 
             expected_power = expected_power,
             onlysmall=onlysmall,
             info=info, 
             AI=self.A.rightXPS.GPIO2.ADC1)
        
    #############################################################################
    def __set_startpos__(self, re_register=True, interactive=True):
        # save current fibre holder position to a file:
        self.A.report_position(sys.stdout, indent = '')
        if interactive:
            if not self.are_you_sure():
                return
        directory = os.path.dirname(os.path.abspath(__file__))
        path = directory + os.sep + '..' + os.sep + '..' +  os.sep + 'pymeasure' + os.sep + 'auto' + os.sep + 'imec' + os.sep + 'core' + os.sep + '__start_pos__.py'
        print path
#         print "saving to ", path
        F = file(path, "wb")
        self.A.report_position(F, indent = '')
        del F
        execfile(path, {}, globals())
        #self.__init_alignments__()
        # set the prober's zero position at the current position:
        self.A.TABLE.PositionCurrentSetZero()
        #re-register all the devices in the catalog, since any existing alignment info will be voided by changing the zero position:
        if re_register:
            self.__init_devicecatalog__()
        #amend the HomeXY attribute of self.MeasurementTree.Wafer:
        if self.A.__class__ == ImecAutomaticSetup:
            self.MeasurementTree.Wafer.HomeFromChuckCenter = XY(self.A.TABLE.XHome, 
                                                   self.A.TABLE.YHome)
        elif self.A.__class__ == Imec300AutomaticSetup:
            self.MeasurementTree.Wafer.HomeFromChuckCenter = self.A.TABLE.HomeXY - \
                                                self.A.TABLE.CenterXY 

    def __get_start_pos__(self):
        try:
            return __get_start_pos__()
        except NameError:
            if self.A.__class__ == ImecAutomaticSetup:
                theta = 0.0
                contact = 0.0
                xy = XY(0.0, 0.0)
            elif self.A.__class__ == Imec300AutomaticSetup:
                theta = self.A.TABLE.HomeTheta
                contact = self.A.TABLE.ContactHeight
                xy = self.A.TABLE.HomeXY
            lp = XYZ(*self.A.LEFT.PositionCurrentGet())
            rp = XYZ(*self.A.RIGHT.PositionCurrentGet())
            return [xy.X, xy.Y, contact, theta], XYZ(lp.X, lp.Y, lp.Z), XYZ(rp.X, rp.Y, rp.Z)            

    def __return_to_startpos__(self):
        self.A.set_arms_speed(.1)
        table_pos, l_pos, r_pos = self.__get_start_pos__()
#         print table_pos
        #print l_pos
        #print r_pos
        if self.A.__class__ == ImecAutomaticSetup:
            pass
        elif self.A.__class__ == Imec300AutomaticSetup:
            self.A.TABLE.HomeXY.X = table_pos[0]
            self.A.TABLE.HomeXY.Y = table_pos[1]
            self.A.TABLE.ContactHeight = table_pos[2]
            self.A.TABLE.HomeTheta = table_pos[3]
            self.A.TABLE.RelativeTheta = 0.0
        self.A.TABLE.Home()
        self.A.TABLE.Separation()
        self.MeasurementTree.Wafer.CurrentDie = self.MeasurementTree.Wafer.HomeDie
#         print self.MeasurementTree.Wafer.CurrentDie
        self.A.move_abs_LR(l_pos, r_pos)
        self.A.TABLE.Contact()
        #amend the HomeXY attribute of self.MeasurementTree.Wafer:
        if self.A.__class__ == ImecAutomaticSetup:
            self.MeasurementTree.Wafer.HomeFromChuckCenter = XY(self.A.TABLE.XHome, 
                                                   self.A.TABLE.YHome)
        elif self.A.__class__ == Imec300AutomaticSetup:
            self.MeasurementTree.Wafer.HomeFromChuckCenter = self.A.TABLE.HomeXY - \
                                                self.A.TABLE.CenterXY 
        #select appropriate laser
        self.select_laser(self.MeasurementTree.DefaultWavelength)
        #set polarization:
        if (not self.epc is None) and (self.epc.Remote == True):
            '''TODO: retrieve polarization from home device'''
            try:
                self.epc.__get_heater_voltages__('TE', self.MeasurementTree.DefaultWavelength.get_value(NANOMETER))
            except NoHeaterCalibrationData:
                pass
    
    def __get_waferalignmentinfo__(self):
        try:
            return __get_waferalignmentinfo__()
        except NameError:           
            return 0.0  
    
    def __load_sample__(self):
        #read home position of left and right fibre and wafer stage
        Th, L, R = self.__get_start_pos__()
#         print Th, L, R
        #read current wafer position:
        T = self.A.table_xyz
        self.A.set_arms_speed(.1)
        L_saved, R_saved = XYZ(*L), XYZ(*R)
        L_saved.Z += 1
        R_saved.Z += 1
        #now move fibres to L_saved, R_saved, i.e.: 1mm higher than during measurement and at home x,y
        self.A.move_abs_LR(L_saved, R_saved)
        #move chuck to separation and then to load position:
        self.A.move_wafer_Separation()
        self.A.move_wafer_Load()
        showtext = True
        while 1:
            if showtext:
                print("Press 'f' when done loading the wafer.")
                showtext = False
            c = FiniteWaitForKBInput(lambda: msvcrt.getch(), self.menutimeout).result
            if c in ['f', None]:
                break
        #move wafer back to home, centre, or previous position
        if self.A.__class__ == Imec300AutomaticSetup:
            #on PA300, contact height and theta angle need to be set again
            #after a movement to load position:
            self.A.TABLE.HomeXY.X = Th[0]
            self.A.TABLE.HomeXY.Y = Th[1]
            self.A.TABLE.ContactHeight = Th[2]
            self.A.TABLE.HomeTheta = Th[3]
            self.A.TABLE.RelativeTheta = 0.0
        while 1:
            print("Press 'h' to return wafer to home position, 'p' to return to previous location or any other key to return to centre.")
            c = FiniteWaitForKBInput(lambda: msvcrt.getch(), self.menutimeout).result
            #c = msvcrt.getch()
            #c == raw_input("  Press 'h' to return wafer to home position, 'p' to return to previous location or any other key to return to centre.  ")
            if c == 'h':
                self.A.move_wafer_Home()
            elif c == 'p':
                try:
#                     print Th
#                     self.A.TABLE.HomeXY.X = Th[0]
#                     self.A.TABLE.HomeXY.Y = Th[1]
                    self.A.move_abs_wafer(T.X, T.Y)
                except ChuckTravelRangeError:
                    warnings.warn('Cannot move to previous location. Choose Home or center position.')
                    continue  
            else:
                self.A.move_wafer_Centre()
            break
        self.A.move_wafer_Separation()
        _, l_pos, r_pos = self.__get_start_pos__()
        self.A.move_abs_LR(l_pos, r_pos)
            
class ILPDLMeasurementSetting(LossMeasurementSetting):
    __slots__ = ('AgConfigFile', '_agconfigfile')
    def __init__(self, **kwargs):
        self._agconfigfile = r'C:\Users\Public\Documents\Photonic Application Suite\AgEngineILPDL0.agconfig'
        for k in kwargs.keys():
            if hasattr(self, k):
                setattr(self, k, kwargs[k])
        super(ILPDLMeasurementSetting, self).__init__(**kwargs)
        self._required_instruments = ['ILPDLEngine'] 
    
    @Property
    def AgConfigFile(self):
        doc = "AgConfigFile (str): configuration file"
        def fget(self):
            return self._agconfigfile
        def fset(self, agc_string):
            if type(agc_string) == str:
                self._agconfigfile = agc_string
            else:
                self.__nameerror__('AgConfigFile', 'a string')
        def fdel(self):
            del self._agconfigfile
        return locals()

class ILPDLMeasurementResult(MeasurementResult):
    """
    DateStamp (struct_time): represents the Date/time when these data were measured
    """
    __slots__ = ('DateStamp', '_datestamp')
    def __init__(self, **kwargs):
        self._datestamp = time.localtime()
        for k in kwargs.keys():
            if hasattr(self, k):
                setattr(self, k, kwargs[k])
    
    @Property
    def DateStamp(self):
        doc = "struct_time object representing the Date/time when these results were obtained."
        def fget(self):
            return self._datestamp
        def fset(self, datestamp):
            if (type(datestamp) != time.struct_time):
                self.__nameerror__('DateStamp', 'a time object')
            else:
                self._datestamp = datestamp
        def fdel(self):
            del self._datestamp
        return locals()

if __name__ == "__main__":
    I = ILPDLSetup()