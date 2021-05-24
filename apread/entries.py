# binary reader import
import os
from time import time
from apread.binaryReader import BinaryReader

# plotting
import matplotlib.pyplot as plt
import plotly.express as px
import scipy.signal as sig

# serialization
import json

from tqdm import tqdm
from apread.loader import Loader

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
            self.Name = reader.read_string(reader.read_int16())

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


    def plot(self, mode = 'ply', governed = False):
        """
        Plot the channel over its connected time-channel.

        mode:
            'ply'   Plotly,
            'mat'   matplotlib

        governed:
            States wether the call to this function will handle figures and handles.
            If False, a single figure will be shown.
        """
        # cant plot time over time
        if self.isTime:
            print("\t[ APREAD/PLOT ] Channel is time. Not plotting.")
            return

        print(f'\t[ APREAD/PLOT ] Filtering plot for {self.Name}')
        # filter data
        datay = sig.wiener(self.data)

        print(f'\t[ APREAD/PLOT ] Plotting {self.Name}')
        if 'ply' in mode:
            fig = px.line(x = self.Time.data, y = datay, title = f'{self.Name}')
            if not governed:
                fig.show()
            else:
                print('Cant handle governed mode and plotly.')
                return
        elif 'mat' in mode:
            if not governed:
                fig = plt.figure(self.Name)
                plt.xlabel('Time [s]')
                plt.ylabel(self.unit)

            plt.plot(self.Time.data, datay, label=self.Name)

            if not governed:
                plt.title(self.Name)
                plt.draw()
                plt.legend()        
                plt.show()

    def __str__(self):
        """
        Default conversion to string.
        """
        print(self.Name)
        for d in self.data:
            print(d)

    def __getitem__(self, key) -> float:
        """Return the item at index key.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return self.data[key]
    def save(self, mode, path):
        """Save group as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """

        if self.isTime:
            print('Channel cant be saved since it is a Time-Channel')
            return

        if self.length == 0:
            print('Channel has no data and cant be saved.')
            return

        # get total length
        length = self.length
        length1 = 1

        # ensure destination exists
        dest = os.path.join(path, self.Name + '.json')

        # check if path is a path
        if not os.path.isdir(path):
            raise Exception(f'To save a group, supply a path. {path} is not path.')
        # then, check if the path exists and create if necessary
        elif not os.path.exists(path):
            os.makedirs(path)

        # check, which mode to use as save
        if mode == 'csv':
            # write content to file
            with open(dest, 'w') as file:
                for i in tqdm(range(length), desc=f'Writing CSV: {self.Name}'):
                    file.write(f'{self.Time.data[i]}')

                    for j in range(length1):
                        file.write(f'\t{self.data[i]}')

                    file.write('\n')
            print('\t[ APREAD/Save CSV ] Done.')

        elif mode == 'json':
            # write content to file
            with open(dest, 'w') as file:
                data = {}
                data['X'] = self.Time.data
                for j in range(length1):
                    data[f'Y'] = self.data
                
                # output json
                with Loader(f'Writing JSON: {self.Name}', end='\t[ APREAD/Save JSON ] Done.'):
                    json.dump(data, file, indent=4)

        else:
            raise Exception(f"Unknown mode: {mode}")        


class Group:
    """
    Groups channels together.

    Helps calling plot functions..
    """
    Channels: list[Channel]
    # Name of the time channel of this group
    Name: str

    # the time-channel
    ChannelX: Channel
    # all other data-channels
    ChannelsY: list[Channel]

    # the data time interval with a fitting unit
    intervalstr: str
    # the data time interval in milliseconds
    interval: float
    # frequency of the corresponding time
    frequency: float
    def __init__(self, channels: list[Channel]):
        """Create group of channels.

        Args:
            channels (list[Channel]): The channels this group is based on.        
        """
        # save all channels
        self.Channels = channels
        # get first channel which is marked as "isTime"
        timeC = next((x for x in channels if x.isTime), None)
        self.ChannelX = timeC

        if timeC is None:
            # if no time found, group cant be shown
            print('\t[ APREAD/WARNING ] Group does not have a time-channel. Skipping...')
        else:
            # get name of time channel
            self.Name = timeC.Name

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
            unit = 'ns'
            fac = 1e6
        if timeC.data[1] < 1e-6:
            unit = 'μs'
            fac = 1e9

        self.intervalstr = f"{timeC.data[1]*fac:.3f}{unit}"
        self.interval = timeC[1]/1e3
        self.frequency = 1/timeC.data[1]

    def plot(self, governed=False):
        """Plots this group of channels

        Args:
            governed (bool, optional): States wether this plot-function is called from another plot-function. When nesting plot functions, the base function has to call plt.show. Defaults to False.
        """
        if not governed:
            fig = plt.figure(self.Name)

        for channel in self.ChannelsY:
            channel.plot(mode='mat', governed=True)

        if not governed:
            plt.title(self.Name)
            plt.draw()
            plt.legend()
            plt.show()

    def __getitem__(self, key):
        """Return the time and all y-channels at index.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return (self.ChannelX[key], [chan[key] for chan in self.ChannelsY])

    def save(self, mode, path):
        """Save group as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """
        # get total length
        length = len(self.ChannelX.data)
        length1 = len(self.ChannelsY)

        # ensure destination exists
        dest = os.path.join(path, self.Name + '.json')

        # check if path present
        if not os.path.exists(path):
            os.makedirs(path)

        # check, which mode to use as save
        if mode == 'csv':
            # write content to file
            with open(dest, 'w') as file:
                for i in tqdm(range(length), desc=f'Writing CSV: {self.Name}'):
                    file.write(f'{self.ChannelX.data[i]}')

                    for j in range(length1):
                        file.write(f'\t{self.ChannelsY[j].data[i]}')

                    file.write('\n')
            print('\t[ APREAD/Save CSV ] Done.')

        elif mode == 'json':
            # write content to file
            with open(dest, 'w') as file:
                data = {}
                data['X'] = self.ChannelX.data
                for j in range(length1):
                    data[f'Y{j}'] = self.ChannelsY[j].data
                
                # output json
                with Loader(f'Writing JSON: {self.Name}', end='\t[ APREAD/Save JSON ] Done.'):
                    json.dump(data, file, indent=4)

        else:
            raise Exception(f"Unknown mode: {mode}")        