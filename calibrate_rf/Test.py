from pymeasure.auto.imec.core.MeasurementEngine import run300mm
from pymeasure.auto.imec.core.TestPlanDefinitions import MeasurementTree, PortCombo, TestSite, DUT
from pymeasure.auto.imec.core import MeasurementSettings as ms
from pymeasure.units.unit import NANOMETER, MICROMETER, MILLISECOND, DBM, VOLT, MILLIAMPERE, MICROMETERPERSECOND
from util.Coordinates import XY


import numpy as np

T = [] #empty list of testsites

D = []

D.append(DUT(Name='PGSP_CTE_L0_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='IN_REF', Right='OUT_REF', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTE_L25_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTE_L50_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTE_L100_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTE_L150_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='lossmeasurement', SiteOffset=XY(0.0, 0.0)))

D = []

D.append(DUT(Name='PGSP_CTM_L0_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='IN_REF', Right='OUT_REF', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTM_L25_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTM_L50_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTM_L100_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='PGSP_CTM_L150_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='lossmeasurement', SiteOffset=XY(0.0, 0.0)))

D = []

D.append(DUT(Name='GPD2_CTE_L25_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='GPD2_CTE_L50_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='GPD2_CTE_L100_WG500', PortCombos=PortCombo(MeasurePwrRng=0*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='lossmeasurement', SiteOffset=XY(0.0, 0.0)))

D = []

D.append(DUT(Name='GPD2_CTM_L25_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='GPD2_CTM_L50_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
D.append(DUT(Name='GPD2_CTM_L100_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=False, Left='Input', Right='Output', Probe='GND', SettID='loss1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='lossmeasurement', SiteOffset=XY(0.0, 0.0)))


D = []


D.append(DUT(Name='PGSP_CTE_L25_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='PGSP_CTE_L50_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='PGSP_CTE_L100_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='PGSP_CTE_L150_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))


D = []


D.append(DUT(Name='GPD2_CTE_L25_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='GPD2_CTE_L50_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='GPD2_CTE_L100_WG500', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))

D = []

D.append(DUT(Name='GPD2_CTM_L25_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='GPD2_CTM_L50_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
D = []
D.append(DUT(Name='GPD2_CTM_L100_WG750', PortCombos=PortCombo(MeasurePwrRng=-10*DBM, AlignPwrRng=-20*DBM, BlindStep=True, Left='Input', Right='Output', Probe='GND', SettID='d1')))
#T.append(TestSite(Name='GRA_PD_GR1', DUTs = D, Recipes='detectormeasurement', SiteOffset=XY(0.0, 0.0)))
M = MeasurementTree()
M.DisableChuck = True # enable only when check movement should be avoided
M.Wafer.BatchID = 'P162388'
M.Wafer.WaferID = 'D06_17362'
M.Mask = 'SIPP24'
M.Wafer.HomeDie = (-1,0)
M.DieSelection = [(-1,0)]#, (-1,0)]
M.TestSites = T
M.Operator = 'dong87'
M.Setup = '300mm'
M.UseZProfiling = False
M.AlignMethod = 'spiral'

M.OutputLoss = 0.0
M.FiberHeight = 20*MICROMETER
M.FiberAngle = 10
M.DefaultWavelength = 1560*NANOMETER
M.KD = 32329
M.Purpose = 'fsaffds'
M.Temperature = 24
M.RelativeHumidity = 47
M.Comment = ""
M.ProbeSerial = "41648"

''' settings object 'd1' '''
L4 = ms.DetectorMeasurementSetting()
L4.AlignSet = ms.FibreAlignmentSetting(LStart=1550*NANOMETER, LSpan=40*NANOMETER, LStep=0.05*NANOMETER, 
									AvgTime=0.025*MILLISECOND, FibreRange=30*MICROMETER, 
									FibreSpeed=100*MICROMETERPERSECOND, AlignL=1550*NANOMETER)
L4.AvgTime = 0.025*MILLISECOND
L4.ID = 'd1'
L4.LPower = 6*DBM
L4.Attenuations = [24, 21, 18, 15, 12, 9, 6, 3, 0]
#M.FiberOutput = {1560:10.05*DBM}
#M.FiberOutput = {1560:6.99*DBM}
M.FiberOutput = {1560:4.26*DBM}

#if L4.LPower == 12*DBM:
#	M.FiberOutput = {1560:9.81*DBM}
#elif L4.LPower == 9*DBM:
#	M.FiberOutput = {1560:6.79*DBM}
#elif L4.LPower == 6*DBM:
#	M.FiberOutput = {1560:3.79*DBM}

L4.LSpan = 40*NANOMETER
L4.LStart = 1540*NANOMETER
L4.LStep = 0.05*NANOMETER
L4.IVWavelength = 1560*NANOMETER
#L4.VGate = [-2.0*VOLT, -1.0*VOLT, 0.0*VOLT, 1.0*VOLT, 2.0*VOLT]
#L4.VGate = [-1.0*VOLT, -0.8*VOLT, -0.6*VOLT, -0.4*VOLT, -0.2*VOLT, 0.0*VOLT, 0.2*VOLT, 0.4*VOLT, 0.6*VOLT, 0.8*VOLT, 1.0*VOLT]
#L4.VGate = [-4.0*VOLT, -3.0*VOLT, -2.0*VOLT, -1.0*VOLT, 0.0*VOLT, 1.0*VOLT, 2.0*VOLT, 3.0*VOLT, 4.0*VOLT]
#L4.VGate = [-9.0*VOLT, -8.0*VOLT, -7.0*VOLT, -6.0*VOLT, -5.0*VOLT, -4.0*VOLT, -3.0*VOLT, -2.0*VOLT, -1.0*VOLT, 0.0*VOLT, 1.0*VOLT, 2.0*VOLT, 3.0*VOLT, 4.0*VOLT, 5.0*VOLT, 6.0*VOLT, 7.0*VOLT, 8.0*VOLT, 9.0*VOLT]
L4.VSpan = 4*VOLT
L4.VStart = -2*VOLT #L4.VGate[0]-4*VOLT
L4.VStep = 0.05*VOLT
Lrange = np.arange(1530,1590, 10) # start wavl, stop wavl and step in nm
for l in Lrange:
	L4.Wavelengths.append(l*NANOMETER)
L4.DCBias = -1.0*VOLT # should be the bias at which the Light-current spectrum is saved
L4.DCBiasCompliance = 1*MILLIAMPERE
L4.StoreOutputPower = True
L4.XSpan = 30*MICROMETER # for OE alignment
L4.YSpan = 30*MICROMETER # for OE alignment
L4.XYStep = 2*MICROMETER # for OE alignment
L4.OEAlignFibre = 'Left'
L4.OEAlignV = 0.0*VOLT # when 0.0, no OE alignment is done


''' settings object 'loss1' '''
AlignmentSetting = ms.FibreAlignmentSetting(LStart=1520*NANOMETER, LSpan=100*NANOMETER, LStep=2.5*NANOMETER, AvgTime=0.025*MILLISECOND, FibreRange=30*MICROMETER, FibreSpeed=100*MICROMETERPERSECOND, AlignL=1570*NANOMETER)
L3 = ms.LossMeasurementSetting(LStart=1520*NANOMETER, LSpan=100*NANOMETER, LStep=0.05*NANOMETER, LPower=6*DBM, AvgTime=0.025*MILLISECOND, ID='loss1', AlignSet=AlignmentSetting)


''' launch measurement '''
A = run300mm(M, [L3, L4])#, skipquestions=True, menuchoice=8) , autofinish=True)
