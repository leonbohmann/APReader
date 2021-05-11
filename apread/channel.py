# binary reader import
from apread.binaryReader import BinaryReader

# plotting
import matplotlib.pyplot as plt
import plotly.express as px
import scipy.signal as sig

from tqdm import tqdm
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

    

    def __init__(self, reader: BinaryReader):
        """
        Creates the Channel.

        Uses a reader (BinaryReader) to read the data from the file accessed by "APReader.__init__".
        """
        # referenced time channel (dummy, since this may stay None)
        self.Time = None
        self.isTime = False
        # save the reader for later use
        self.reader = reader

        # get index of channel
        self.num = reader.read_int16()
        # get length of channel
        self.length = reader.read_int32()
        try:
            # get name of channel
            self.name = reader.read_string(reader.read_int16())

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
            # extended channel header (mostly unused)
            self.header = reader.read(reader.read_int32())
            # linearization mode
            self.lmode = reader.read_char()
            # user scale
            self.scale = reader.read_char()
            # unknown points
            self.npoi = reader.read_single()
            # readaway
            for i in range(self.npoi):
                reader.read_double()

            # thermo type
            reader.read_int16()

            # readaway
            self.formula = reader.read_chars(reader.read_int16())
            self.sensorInfo = reader.read_chars(reader.read_int32())

            # flag to indicate that everything is fine
            self.broken = False
        except:
            # flag to indicate that there is something wrong
            self.broken = True


    def readData(self):
        """
        Reads the data of this Channel.

        IMPORTANT
            The stream offset has to be set before calling this function!
        """
        # if something was wrong previously, nothing will happen here
        if self.broken:
            return

        # initialize data
        self.data = []
        # read all channel data
        for i in tqdm(range(self.length), leave=False):
            self.data.append(self.reader.read_double())                


    def plot(self, mode = 'ply'):
        """
        Plot the channel over its connected time-channel.

        mode:
            'ply'   Plotly
            'mat'   matplotlib
        """
        # cant plot time over time
        if self.isTime:
            print("\t[ APREAD/PLOT ] Channel is time. Not plotting.")
            return

        print(f'\t[ APREAD/PLOT ] Filtering plot for {self.name}')
        # filter data
        datay = sig.wiener(self.data)

        print(f'\t[ APREAD/PLOT ] Plotting {self.name}')
        if 'ply' in mode:
            fig = px.line(x = self.Time.data, y = datay, title = f'{self.name}')
            fig.show()
        elif 'mat' in mode:
            fig = plt.figure(self.name)
            plt.plot(self.Time.data, datay)
            plt.draw()
            plt.show()

    def __str__(self):
        """
        Default conversion to string.
        """
        print(self.name)
        for d in self.data:
            print(d)