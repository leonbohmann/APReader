# binary reader import
# parallel processing
import multiprocessing as mp
import os
from datetime import datetime
from multiprocessing.pool import Pool as mpPool

# typing
from typing import List

# plotting
import matplotlib.pyplot as plt

# progress
import numpy as np

from apread.binaryReader import BinaryReader


def read_chunk_from_file(file_path, start, end, typ, buf_loc) -> np.ndarray:
    """Reads a chunk of a file by opening a binary reader.

    Args:
        file_path (str): Filepath to the file.
        start (int): Start buffer location in entries.
        end (int): End buffer location in entries.
        typ (nd.dtype): The type of data.
        cur_loc (int): Current buffer location in bytes.

    Returns:
        np.ndarray: The chunk of the file as a numbered array.
    """
    # open the file and seek the buffer to the start of channel entries
    with open(file_path, 'rb') as f:
        f.seek(buf_loc)
        # read the chunk of data from the file
        chunk = np.fromfile(f, dtype=typ, offset=start * typ.itemsize, count=end-start)
        
    return chunk    

def toTimestamp(serialFormat):
    return (serialFormat - 25569) * 86400.0

def toDatetime(timestamp):
    return datetime.utcfromtimestamp(timestamp)

def get_clr(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

class Channel:
    """
    Holds data of a Catman Channel.

    Information:
            APReader uses the Channel-Lengths to connect Channels together.
            Say there are two Channels with Length 100, then one of those will have "Time" in its name.
            The other one then gets a reference to the "time" one.
            
            If there is more than one channel having the same amount of entries, every channel will 
            get the same reference to the time channel.
    """        
    # data: List[float]
    verbose: bool
    # Defines if data should be filtered.
    filterData: bool
    
    # Specifies if channel entries should be loaded in parallel.
    parallelLoad: bool
    # Amount of parallel processes that can be used to load data.
    parallelProcs: int
    # The parallel pool which holds parallel processes.
    parallelPool: mpPool
    
    def __init__(self, reader: BinaryReader, fileName='unknown', filepath='', \
        verbose=False, parallelPool=None):
        """
        Creates the Channel.

        Uses a reader (BinaryReader) to read the data from the file accessed by "APReader.__init__".
        """
        
        # parallel stuff
        self.parallelLoad = parallelPool is not None
        self.parallelPool = parallelPool
        self.parallelProcs = len(mp.active_children())
        
        # defines, if the apreader should output verbose debug messages
        self.verbose = verbose

        # referenced time channel (dummy, since this may stay None)
        self.Time: Channel = None
        "Time channel."
        self.isTime = False
        # save the reader for later use
        self.reader = reader

        # get index of channel
        self.num = reader.read_int16()
        # get length of channel
        self.length = reader.read_int32()
        # get name of channel
        self.Name = reader.read_string(reader.read_int16())

        # the original file name of the group
        self.fileName = os.path.splitext(os.path.basename(fileName))[0]
        tName = self.Name.replace(' ',"_")  # temporary name
        self.fullName = f"{fileName}.{tName}"
        self.filePath = filepath
        # retrieve unit of channel                
        
        self.unit = reader.read_string(reader.read_int16())
        
        # get comment of channel                
        self.comment = reader.read_string(reader.read_int16())

        # 0: numeric, 1: string, 2: binary object
        self.format  = reader.read_int16()
        # get format of channel (8: numeric, >8: string)
        self.dw = reader.read_int16()
        # time of reading
        self.time = reader.read_double()
        self.date = toDatetime(self.time)
        # extended channel header
        self.nHdrBytes = reader.read_int32()
        self.extHeader = self.readExtHeader(reader)
        
        precDict = {0:8, 1:4, 2:2} # key: Attribute "Exportformat", value: precision in bytes
        try:
            self.precision = precDict[self.extHeader['ExportFormat']]
        except KeyError:
            print('Unexpected value of attribute "ExportFormat" in the extended header of channel {}. Assuming double precision.'.format(self.Name))
            self.precision = 8

        # linearization mode
        self.lmode = reader.read_char()
        # user scale
        self.scale = reader.read_char()
        # unknown points
        self.npoi = reader.read_byte()
        # readaway
        for i in range(self.npoi):
            reader.read_double()

        # thermo type
        reader.read_int16()

        # readaway
        self.formula = reader.read_string(reader.read_int16())
        self.sensorInfo = reader.read_string(reader.read_int32())

        # flag to indicate that everything is fine
        self.broken = False

    def readExtHeader(self, rdr: BinaryReader):
        """
        Reads the extended header of this Channel.

        NOTE: The catman binary files use byte padding, which means that all
        values are stored at byte addresses which are integer multiples of their
        width in bytes (i.e. doubles are stored on addresses divisible by eight,
        floats on addresses divisible by four etc.)
        
        See the link below for more info:        
        https://stackoverflow.com/questions/4306186/structure-padding-and-packing
        
        For this reason, I've added three bytes of padding before the attribute
        'NominalRange', which is a float.
            
        """
        pos0 = rdr.tell() # In general not a multiple of eight, which is unexpected!

        exthdr = {}
        exthdr['T0'] = rdr.read_double() # (pos0+) 8
        exthdr['dt'] = rdr.read_double() # 16
        exthdr['SensorType'] = rdr.read_int16() # 18
        exthdr['SupplyVoltage'] = rdr.read_int16() # 20
        
        exthdr['FiltChar'] = rdr.read_int16() # 22
        exthdr['FiltFreq'] = rdr.read_int16() # 24
        exthdr['TareVal'] = rdr.read_float() # 28
        exthdr['ZeroVal'] = rdr.read_float() # 32   
        exthdr['MeasRange'] = rdr.read_float() # 36
        exthdr['InChar'] = [rdr.read_float() for i in range(4)] # 40, 44, 48, 52
        
        exthdr['SerNo'] = rdr.read_string(32) # 84
        exthdr['PhysUnit'] = rdr.read_string(8) # 92
        exthdr['NativeUnit'] = rdr.read_string(8) # 100
        
        exthdr['Slot'] = rdr.read_int16() # 102
        exthdr['SubSlot'] = rdr.read_int16() # 104
        exthdr['AmpType'] = rdr.read_int16() # 106
        exthdr['APType'] = rdr.read_int16() # 108
        exthdr['kFactor'] = rdr.read_float() # 112
        exthdr['bFactor'] = rdr.read_float() # 116
        
        exthdr['MeasSig'] = rdr.read_int16() # 118
        exthdr['AmpInput'] = rdr.read_int16() # 120
        exthdr['HPFilt'] = rdr.read_int16() # 122
        exthdr['OLImportInfo'] = rdr.read_byte() # 123
        exthdr['ScaleType'] = rdr.read_byte() # 124
        exthdr['SoftwareTareVal'] = rdr.read_float() # 128        
        exthdr['WriteProtected'] = rdr.read_byte() # 129
        rdr.read_string(3) # 132
        
        exthdr['NominalRange'] = rdr.read_float() # 136 
        exthdr['CLCFactor'] = rdr.read_float() # 140
        exthdr['ExportFormat'] = rdr.read_byte() # 141
        rdr.read_string(7) # 148
        # reserve = rdr.read_string(10)        
        posN = rdr.tell()
        
        if (posN-pos0) != self.nHdrBytes:
            print("""
                  WARNING:
                  The number of bytes read in the extended header of the channel
                  '{}'
                  doesn't match its declared length.
                  This probably means that the hardcoded format definition in the method
                  'Channel.readExtHeader' is no longer valid and must be revised.
                  Leaving the extended header as-is and resetting the read position of
                  the binary reader. Assuming double precision for the data.
                  """.format(self.Name))
            rdr.seek(pos0 + self.nHdrBytes)
            exthdr['ExportFormat'] = 0
        
        return exthdr

    def readData(self):
        """
        Reads the data of this Channel.

        IMPORTANT
            The stream offset has to be set before calling this function!
        """
        # if something was wrong previously, nothing will happen here
        if self.broken:
            return
                        
        # The data is stored channelwise. We therefore only need to pass pointers to the first and last byte.
        if self.precision == 8 or self.precision == 4:
            datatype = np.dtype('f{}'.format(self.precision))                
            # parallel loading will split up the incoming bin array
            if self.parallelLoad:
                self.data = self.read_data_parallel(datatype)
                
            # default loading will load all entries at once
            else:
                self.data = np.fromfile(self.reader.buf, dtype=datatype, count=self.length)
                
        elif self.precision == 2:
            MinValue = self.reader.read_double()
            MaxValue = self.reader.read_double()
            sf = (MaxValue - MinValue)/32767 # scale factor
            self.data = np.fromfile(self.reader.buf, dtype=np.dtype('u2'), count=self.length)*sf + MinValue
    
    def __str__(self):
        """
        Default conversion to string.
        """
        return f'Channel "{self.Name}" ({self.length} Entries)'        

    def __getitem__(self, key) -> float:
        """Return the item at index key.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return self.data[key]
    
    def plot(self, governed = False, axes=None, clr='b-'):
        """
        Plot the channel over its connected time-channel.

        governed:
            States wether the call to this function will handle figures and handles.
            If False, a single figure will be shown.
        """
        # cant plot time over time
        if self.isTime:
            if self.verbose:
                print("\t[ APREAD/PLOT ] Channel is time. Not plotting.")
            return

        if self.Time is None:
            print("\t[ APREAD/PLOT ] Channel does not have time data. Not plotting.")
            return        

        plotbase = axes if axes is not None else plt
        
        
        if self.verbose:
            print(f'\t[ APREAD/PLOT ] Plotting {self.Name}')
        
        if not governed:
            plt.figure(self.Name)
            plt.xlabel('Time [s]')
            plt.ylabel(self.unit)

        line = plotbase.plot(self.Time.data, self.data, color=clr, label=self.Name )
        
        
        if not governed:
            plt.title(self.Name)
            plt.draw()
            plt.legend()        
            plt.show()
            
        return line
    
    

    def read_data_parallel(self, dtype):
        """Reads in the underlying binary data using multiple parallel tasks.

        Args:
            dtype (nd.dtype): The type of the underlying layer data entries (f4, f8, ...).

        Returns:
            ndarray: Array of the binary data.
        """
        # chunk the total length of this channel
        chunk_size = self.length // self.parallelProcs        
                
        # current location of the buffered binary reader
        cur_loc = self.reader.tell()

        # chunk the length
        chunks = [(start, min(start + chunk_size, self.length)) for start in range(0, self.length, chunk_size)]
        results = [self.parallelPool.apply_async(read_chunk_from_file, args=(self.filePath, start, end, dtype, cur_loc)) for (start, end) in chunks]

        # wait for results to finish and check if they finished successfully
        for r in results:
            r.wait()
            if not r.successful():
                print('Error in loading task!')
        
        # concatenate the data structure
        data = np.empty(self.length, dtype)
        for result, (start, end) in zip(results, chunks):
            data[start:end] = result.get()
        
        # push the underlying original reader to after the channel items
        self.reader.seek(cur_loc + self.length * dtype.itemsize)
        return data


class Group:
    """
    Groups channels together.

    Helps calling plot functions..
    """
    # all (unsorted) channels in this group
    Channels: List[Channel] 
    """List of all channels"""
    # Name of the time channel of this group
    Name: str

    # the time-channel
    ChannelX: Channel
    """Time channel only."""
    # all other data-channels
    ChannelsY: List[Channel]
    """Data channels only."""

    # the data time interval with a fitting unit
    intervalstr: str
    # the data time interval in seconds
    interval: float
    # frequency of the corresponding time
    frequency: float

    # the file this group is located in
    fileName: str
    # fully qualifying name
    fullName: str

    def __init__(self, channels: List[Channel], fileName='unknown', verbose=False):
        """Create group of channels.

        Args:
            channels (list[Channel]): The channels this group is based on.        
        """
        self.verbose = verbose
        # save all channels
        self.Channels = channels
        # get first channel which is marked as "isTime"
        timeC = next((x for x in channels if x.isTime), None)
        self.ChannelX = timeC

        if timeC is None:
            # if no time found, group cant be shown
            if self.verbose:
                print('\t[ APREAD/WARNING ] Group does not have a time-channel. Skipping...')
        elif timeC is not None:
            # get name of time channel
            self.Name = timeC.Name

        # the original file name of the group
        self.fileName = os.path.splitext(os.path.basename(fileName))[0]
        tName = self.Name.replace(' ',"_")  # temporary name
        self.fullName = f"{fileName}.{tName}"


        # get all other channels
        self.ChannelsY = []
        for chan in channels:
            if not chan.isTime:
                self.ChannelsY.append(chan)

        # determine frequency and time delta unit
        unit = 's'
        fac = 1
        if timeC.data[1] < 1:
            unit = 'ms'
            fac = 1e3
        if timeC.data[1] < 1e-3:
            unit = 'μs'
            fac = 1e6
        if timeC.data[1] < 1e-6:
            unit = 'ns'
            fac = 1e9

        self.intervalstr = f"{timeC.data[1]*fac:.3f}{unit}"
        self.interval = timeC[1]
        self.frequency = 1/timeC.data[1]

    def __getitem__(self, key):
        """Return the time and all y-channels at index.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return (self.ChannelX[key], [chan[key] for chan in self.ChannelsY])
    
    def __str__(self):        
        return f'Group "{self.Name}" ({len(self.ChannelsY)} Data-channels, {self.ChannelX.length} Entries)'
    
    def plotChannel(self, channelIndex):
        """Plot a specific channel

        Args:
            channelIndex (int): The index of the channel.
        """
        self.plotChannels(channelIndex, channelIndex)
    
    def plotChannels(self, start, end):
        """Plot a range of channels

        Args:
            start (int): Starting index, first channel is 0.
            end (int): Ending index, supports -[index] to mark index from the end.
        """
        self.plot(range(start,end))
    
    def plot(self, channelIndices=None, sameAxis = False):
        """
        Plots this group of channels.
        
        Args:
            channelIndices      The starting index of data channels to be plotted.            
            
        Examples:
            grp.plot() will plot all channels
            grp.plot([0]) will plot the first data channel
            grp.plot([0, 1, 3]) will plot the first, second and third data channel        
        """
        fig, ax1 = plt.subplots()
        ax1.set_xlabel(self.ChannelX.unit)
        
        
        if channelIndices is None:
            channels = self.ChannelsY                
        else:
            channels = [self.ChannelsY[x] for x in channelIndices]
        
        # create colormap
        cmap = get_clr(len(channels)+1)
        # save labels to retrieve them afterwards when building legend
        lns = []
        
        axis = ax1
        for i,channel in enumerate(channels):            
            if i > 0 and not sameAxis:
                axis = ax1.twinx()
                axis.spines['right'].set_position(('outward', 60*(i-1)))     
            axis.set_ylabel(channel.unit)
            axis.tick_params(axis='y', colors=cmap(i))
            axis.get_yaxis().label.set_color(cmap(i))  
                                  
            chanLine = channel.plot(governed=True, clr=cmap(i))
            
            lns += chanLine

        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        ax1.grid()
            
        plt.title(self.Name)
        plt.draw()
        plt.show()
    
