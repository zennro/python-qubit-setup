import sys
import ctypes
import getopt
import re
import struct

"""
.. module:: useful_1
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Andrew Carter <andrew@invalid.com>


"""


from pyview.lib.classes import VisaInstrument
from lib.swig.tools import numerical
import numpy

class Waveform:

    def __init__(self):
      self._name = None
      self._data = None
      self._markers = None
      self._length = None
      self._format = None
      self._rawdata = None

class AwgException(Exception):
  pass

class Instr(VisaInstrument):

  """
  The AWG instrument.
  """
  
  def triggerInterval(self):
    return float(self.ask("TRIG:TIM?"))
    
  def setTriggerInterval(self,interval):
    self.write("TRIG:TIM %g" % interval)
  
  def saveState(self,name):
    """
    Saves the state of the instrument.
    """
    self.saveSetup(name)
    return name
    
  def restoreState(self,name):
    """
    Restores the state of the instrument.
    """
    self.loadSetup(name)
  
  def loadSetup(self,name):
    """
    Loads a given setup file.
    """
    self.write("AWGControl:SRestore \"%s\"" % name)
    for i in range(1,self.channels()+1):
      self.setState(i,True)
    
  def saveSetup(self,name):
    """
    Saves the current instrument configuration to a setup file.
    """
    self.write("AWGControl:SSave \"%s\"" % name)
    
  def runAWG(self):
    """
    Starts the AWG.
    """
    self.write("AWGControl:RUN")
    
  def stopAWG(self):
    """
    Stops the AWG.
    """
    self.write("AWGControl:STOP")
        
  def setups(self):
    """
    Returns a list of all available setups.
    """
    setups = []
    string = self.ask("MMemory:CATALOG?")
    result = re.match(r'^\d+\,\d+\,(.*)$',string)
    filestr = result.groups(0)[0]
    files = re.findall(r'\,?\"(.*?)\,(.*?)\,(.*?)\"',filestr)
    for filestr in files:
      if re.search(r'\.awg$',filestr[0],re.I):
        setups.append(filestr[0])
    return setups
    
  def writeRealData(self,values,markers):
    """
    Writes real-valued data to a string.
    """
    output = ""

    #Fast code that calls a C++ function to encode the data...

    valuesFloat = numpy.zeros(len(values),dtype = numpy.float32)
    markersInt = numpy.zeros(len(markers),dtype = numpy.uint8)

    valuesFloat[:] = values[:]
    markersInt[:] = markers[:] << 6

    buf = ctypes.create_string_buffer(len(valuesFloat)*5)

    numerical.awg_pack_real_data(len(valuesFloat),valuesFloat.ctypes.data,markersInt.ctypes.data,ctypes.addressof(buf))
  
    return buf.raw
    
  def parameters(self):
    """
    Returns all relevant AWG parameters.
    """
    params = dict()
    params["runMode"] = self.runMode()
    params["repetitionRate"] = self.repetitionRate()
    params["channels"] = []
    params["clockSource"] = self.clockSource()
    params["triggerInterval"] = self.triggerInterval()
    for i in [1,2,3,4]:
      channelParams = dict()
      channelParams["high"] = self.high(i)
      channelParams["low"] = self.low(i)
      channelParams["amplitude"] = self.amplitude(i)
      channelParams["offset"] = self.offset(i)
      channelParams["skew"] = self.skew(i)
      channelParams["function"] = self.function(i)
      channelParams["waveform"] = self.waveform(i)
      channelParams["phase"] = self.phase(i)
      channelParams["dac_resolution"] = self.DACResolution(i)
      params["channels"].append(channelParams)
    return params
    
  def state(self,channel):
    """
    Returns the output state of the instrument.
    """
    return self.ask("OUTPUT%d:STATE?" % channel)
    
  def setState(self,channel,state):
    """
    Sets the output state of the instrument.
    """
    buf = "OFF"
    if state == True:
      buf = "ON"
    self.write("OUTPUT%d:STATE %s" % (channel,buf))
    
  def channels(self):
    """
    Returns the number of channels of the instrument.
    """
    return int(self.ask("AWGControl:CONFIGURE:CNUMBER?"))
    
  def clockSource(self):
    """
    Returns the value of the clock:source parameter.
    """
    return self.ask("AWGControl:CLOCK:SOURCE?")
    
  def setWaveform(self,channel,name):
    """
    Sets the waveform for a given channel.
    """
    self.write("SOURCE%d:WAVEFORM \"%s\"" % (channel,name))
    
  def phase(self,channel):
    """
    Returns the phase of a given channel.
    """
    return float(self.ask("SOURCE%d:PHASE?" % channel))
    
  def setPhase(self,channel,phase):
    """
    Sets the phase of a given channel.
    """
    self.write("SOURCE%d:PHASE:ADJUST %g" % phase)
    
  def waveform(self,channel):
    """
    Returns the waveform of a given channel.
    """
    return self.ask("SOURCE%d:WAVEFORM?" % channel)[1:-1]
        
  def setRepetitionRate(self,rate):
    """
    Sets the repetition rate of the AWG.
    """
    self.write("AWGControl:RRate %g" % rate)
    
  def repetitionRate(self):
    """
    Returns the repetition rate of the AWG.
    """
    return float(self.ask("AWGControl:RRate?"))
    
  def runMode(self):
    """
    Returns the run mode of the AWG.
    """
    return self.ask("AWGControl:RMODE?")
    
  def DACResolution(self,channel):
    """
    Returns the DAC resolution of the AWG.
    """
    return int(self.ask("SOURCE%d:DAC:RES?" % channel))
    
  def setDACResolution(self,channel,resolution):
    """
    Sets the DAC resolution of the AWG.
    """
    self.write("SOURCE%d:DAC:RES %d" % (channel,int(resolution)))
      
  def function(self,channel):
    """
    Returns the function of a given channel.
    """
    return self.ask("SOURCE%d:FUNCTION:USER?" % channel)[1:-1]
    
  def setFunction(self,channel,name):
    """
    Sets the function of a given channel.
    """
    self.write("SOURCE%d:FUNCTION:USER \"%s\"" % name)
      
  def setSkew(self,channel,time):
    """
    Sets the skew time of a given channel.
    """
    self.write("SOURCE%d:SKEW %d ps" % (channel,int(time)))
    
  def skew(self,channel):
    """
    Returns the skew time of a given channel.
    """
    return float(self.ask("SOURCE%d:SKEW?" % channel))
      
  def setLow(self,channel,voltage):
    """
    Sets the low voltage of a given channel.
    """
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:LOW %g" % (channel,voltage))

  def setHigh(self,channel,voltage):
    """
    Sets the high voltage of a given channel.
    """
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:HIGH %g" % (channel,voltage))

  def setAmplitude(self,channel,voltage):
    """
    Sets the amplitude of a given channel.
    """
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:AMPLITUDE %g" % (channel,voltage))
    
  def setOffset(self,channel,voltage):
    """
    Sets the offset of a given channel.
    """
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:OFFSET %g" % (channel,voltage))

  def low(self,channel):
    """
    Returns the low voltage of a given channel.
    """
    return float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:LOW?" % channel))

  def high(self,channel):
    """
    Returns the high voltage of a given channel.
    """
    return float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:HIGH?" % channel))

  def amplitude(self,channel):
    """
    Returns the amplitude of a given channel.
    """
    return float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:AMPLITUDE?" % channel))

  def offset(self,channel):
    """
    Returns the offset of a given channel.
    """
    return float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:OFFSET?" % channel))

  def writeIntData(self,values,markers):
    """
    Writes integer data to a string.
    """
    output = ""
    for i in range(0,len(values)):
      marker = int(markers[i])
      value = int(values[i])
      output+=struct.pack("H",((marker & 3) << 14) + ((value & 0xFF) << 6))
    return output
    
  def writeMarkers(self,markers):
    """
    Writes marker data to a string.
    """
    output = ""
    for i in range(0,len(markers)):
      marker = int(markers[i])
      output+=struct.pack("B",marker << 6) 
    return output
    
  def readMarkers(self,data):
    """
    Reads marker data from a string.
    """
    markers = []
    for j in range(0,len(data)):
      marker = int(struct.unpack('B',data[j])[0]) >> 6
      markers.append(marker)
    return (numpy.array(markers))
    
  def readRealData(self,data):
    """
    Reads real-valued data from a string.
    """
    values = []
    markers = []
    for j in range(0,len(data)/5):
      value = struct.unpack('f',data[j*5:j*5+4])[0]
      values.append(float(value))
      marker = int(struct.unpack('B',data[j*5+4:j*5+5])[0])
      markers.append(marker)
    return (numpy.array(values),numpy.array(markers))
  
  def readIntData(self,data):
    """
    Reads integer data from a string.
    """
    values = []
    markers = []
    for j in range(0,len(data)/2):
      bytes = struct.unpack('H',data[j*2:j*2+2])[0]
      value = (bytes >> 6) & 0xFF 
      values.append(value)
      markers.append(bytes >> 14)
    return (numpy.array(values),numpy.array(markers))

  def deleteWaveform(self,name):
    """
    Deletes a given waveform.
    """
    self.write("WLIST:WAVEFORM:DELETE \"%s\"" % (name))
    
  def createRawWaveform(self,name,values,markers,wavetype):
    """
    Creates a waveform using a set of values and markers.
    """
    if wavetype == 'INT':
      data = self.writeIntData(values,markers)
    else:
      data = self.writeRealData(values,markers)
    return self.createWaveform(name,data,wavetype)

  def deleteWaveform(self,name):
    self.write("WLIST:WAVEFORM:DELETE \"%s\"" % name)
    
  def createWaveform(self,name,data,wavetype):
    """
    Creates a waveform using a data string as generated by WriteIntData or WriteRealData.
    """
    size = len(data) / 5
    if wavetype == 'INT':
      size = len(data) / 2
    #print "Creating waveform of length %d" % size
    self.write("WLIST:WAVEFORM:NEW \"%s\",%d,%s" %(name,size,wavetype))     
    header = "#%d%d" % (len("%d" % len(data)),len(data))
    self.write("WLIST:WAVEFORM:DATA \"%s\",0,%d," %(name,size)+header+data)

  def updateMarkers(self,name,markers):
    """
    Updates the markers on a given channel.
    """
    data = self.writeMarkers(markers)
    size = len(markers)
    header = "#%d%d" % (len("%d" % len(data)),len(data))
    self.write("WLIST:WAVEFORM:MARKER:DATA \"%s\",0,%d," %(name,size) +header+data)
 
  def getMarkers(self,name):
    """
    Returns the markers of a given channel.
    """
    data = self.ask("WLIST:WAVEFORM:MARKER:DATA? \"%s\"" % name)
    length = int(data[1])
    data = data[2+length:]
    return self.readMarkers(data)
    
  def getWaveform(self,name):
    """
    Returns the waveform with a given name.
    """
    self.write("*CLS")
    data = self.ask("WLIST:WAVEFORM:DATA? \"%s\"" % name)
    wavetype = self.ask("WLIST:WAVEFORM:TYPe? \"%s\"" % name)
    m = re.match("\\s*\#\\d+\\s*",data)
    print "Size: %s" % m.string[m.start(0):m.end(0)]
    data = m.string[m.end(0):]
    MyWaveform = Waveform()
    if wavetype == 'REAL':
      MyWaveform._length = len(data)/5
      (values,markers) = self.readRealData(data)
    elif wavetype == 'INT':
      MyWaveform._length = len(data)/2
      (values,markers) = self.readIntData(data)
    MyWaveform._rawdata = data
    MyWaveform._data = values
    MyWaveform._markers = markers
    MyWaveform._name = name
    MyWaveform._type = wavetype
    return MyWaveform
     
  def getWaveformNames(self):
    """
    Returns the names of all waveforms stored in the AWG memory.
    """
    nWaveforms = int(self.ask("WLIST:SIZE?"))
    print "Found %d waveforms." % nWaveforms
    self.waveformNames = []
    for i in range(0,nWaveforms):
      name = self.ask("WLIST:NAME? %d" % i)[1:-1]
      self.waveformNames.append(name)
    self.notify("waveformnames",self.waveformNames)
    return self.waveformNames
  
  def getWaveforms(self):
    """
    Retrieves all waveforms from the AWG.
    """
    nWaveforms = int(self.ask("WLIST:SIZE?"))
    print "Found %d waveforms." % nWaveforms
    self.waveforms = []
    for i in range(0,nWaveforms):
      name = self.ask("WLIST:NAME? %d" % i)[1:-1]
      try:
        waveform = self.getWaveform(name)
        self.waveforms.append(waveform)
      except:
        print "An error occured.."
    self.notify("waveforms",self.waveforms)
    return self.waveforms
  
  def initialize(self):
    """
    Initializes the AWG.
    """
    try:
      self.waveforms = []
      self._name = "Tektronix AWG"
      self._visaAddress = "TCPIP0::192.168.0.3::inst0"
    except:
      self.statusStr("An error has occured. Cannot initialize %s." % self._name)        