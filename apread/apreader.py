import os
# binary imports
from os import SEEK_SET
from typing import List
# import this to show warnings
import warnings
import random
from matplotlib import pyplot as plt
from tqdm import tqdm

# channel definition
from apread.entries import Channel, Group
# binary reader to read binary files
from apread.binaryReader import BinaryReader

def align_yaxis(ax1, v1, ax2, v2):
    """adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1"""
    _, y1 = ax1.transData.transform((0, v1))
    _, y2 = ax2.transData.transform((0, v2))
    inv = ax2.transData.inverted()
    _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
    miny, maxy = ax2.get_ylim()
    ax2.set_ylim(miny+dy, maxy+dy)

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

class APReader:
    
    """
    All channels unsorted.    
    """
    Channels: List[Channel]
    """
    Grouped channels.    
    """
    Groups: List[Group]

    def __init__(self, path, verbose=False, filterData=False):
        """Creates a new APReader based on a .binary file (path).

        Args:
            path (str): path to a catmanAP binary file.
            verbose (boolean): Show debug output.
            filterData (boolean): Filter input data.
        """
        self.verbose = verbose
        self.filterData = filterData
        self.filepath = path
        self.fileName = os.path.splitext(os.path.basename(path))[0]
        self.Channels = []
        self.Groups = []
        self.read()
        self.connect()

    def connect(self):
        """
        Find channels with equal data length and filter the name for "time" to 
        connect the time-channel with every value-channel (Channel -> channel.Time).
        """
        # no channels no connection
        if len(self.Channels) == 0:
            return

        # create dictionary entries for every length of channels
        # Dictionary: [int: channel.Length, List: Channels]
        channelGroups = {}
        # loop through channels
        for channel in self.Channels:
            # if the current channel length has not been analyzed yet
            if not channel.length in channelGroups:
                # add a new dictionary entry
                channelGroups[channel.length] = []
            
            # append the channel to the dictionary's entry
            channelGroups[channel.length].append(channel)
                
        # now, for each channel-group find the time-channel (only if length of the gorup > 0)
        for group in [channelGroups[groupLen] for groupLen in channelGroups if groupLen > 0]:
            # sometimes only one channel is in the group
            if len(group) < 2:
                for chan in group:
                    chan.broken = True
                    self.Channels.remove(chan)
                continue
            
            
            # find the time channel in the group
            timeChannel = None            
            for channel in group:
                # condition: channel name has to contain "Zeit"
                if str.upper("Zeit") in str.upper(channel.Name) or str.upper("Time") in str.upper(channel.Name):
                    timeChannel = channel
                    # there is only one time-channel
                    break
            #%% sdasd
            # set the time-channel on every channel but itself
            if timeChannel != None:
                for channel in group:
                    if channel is not timeChannel:
                        channel.Time = timeChannel
                        channel.isTime = False
                    else:
                        channel.isTime = True
            elif self.verbose:
                print("\t [WARNING] Channel-group does not contain a time-channel")            

            # create new group based on the groups listed
            self.Groups.append(Group(group, self.fileName, self.verbose))
        pass

    def __iter__(self):
        """Iterates over everything in this reader.

        Yields:
            Any(Channel, Group): Yields all channels and groups.
        """
        for channel in self.Channels:
            yield channel
        for group in self.Groups:
            yield group


    def saveplot(self, path = None, mode='stack'):
        """Saves a plot of the complete binary file.

        Args:
            path (str, optional): The path in which the plot should be saved. Defaults to None.
            mode (str, optional): The plotting mode.
                single     On top of each other.
                stack      Stacked in subplots.
        """
        if path == None:
            path = os.path.dirname(self.filepath)

        # generate destination path
        dest = os.path.join(path, self.fileName+ f'.pdf')
        
        # create path if not exist
        if not os.path.exists(path):
            os.makedirs(path)

        nChannels = len([x for x in self.Channels if not x.isTime])
        cmap = get_cmap(nChannels*10)

        # create figure
        c = 0
        # plot channels in one figure
        if mode == 'single':
            fig, ax = plt.subplots()
        # stack channels on top of each other
        elif mode == 'stack':
            fig,ax = plt.subplots(nChannels,1,sharex=True)

        # add hint that data is filtered!
        fig.suptitle(self.fileName + "(filtered)" if self.filterData else "")
        fig.set_size_inches(30/2.54, 20/2.54)
        xUsed = False
        # plot all channels with their respective time-channels
        for chan in self.Channels:
            if not chan.isTime:   
                # stack in subplots
                if mode == 'stack':
                    # get current axis from subplots
                    #   if nChannels equals 1, there is only one axes
                    if nChannels != 1:
                        ax1 = ax[c]
                    else:
                        ax1 = ax
                    ax1.set_ylabel(f'{chan.Name} [{chan.unit}]')                    
                    ax1.plot(chan.Time.data, chan.data, color=cmap(c*10))
                    c+=1      

                    # label last x-axis
                    if c >= nChannels:
                        
                        ax1.set_xlabel('Time [s]')

                # other mode is single
                elif xUsed:
                    ax1 = ax.twinx()
                    ax1.set_ylabel(f'{chan.Name} [{chan.unit}]')
                    # align_yaxis(ax,0, ax1,0)
                    ax1.plot(chan.Time.data, chan.data, color=cmap(c*10))
                    c+=1
                else:
                    ax.set_ylabel(f'{chan.Name} [{chan.unit}]')
                    ax.plot(chan.Time.data, chan.data, color=cmap(c*10))
                    xUsed = True
                    c+=1
        
        plt.draw()
        plt.savefig(dest, format='pdf')

    def save(self, mode, path = None):
        """Save reader as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """
        if path == None:
            path = os.path.dirname(self.filepath)
        
        for thing in self:
            thing.save(mode,path)

    def read(self):
        """
        Read the binary file.

        Creates channels which can be later accessed.
        """        
        # start by opening a binary stream on the filepath
        with open(self.filepath, 'rb') as f:
            # create a binary reader to simplify inputs
            reader = BinaryReader(f)
            # get the file ID (usually >= 5012)
            self.fileID = reader.read_int16()
            # this is the byte offset, at which the data starts
            self.dataOffset = reader.read_int32()
            # read comment
            self.comment = reader.read_string(reader.read_int16())

            # readaway
            for i in range(32):
                lresakt = reader.read_int16()
                resString = reader.read_string(lresakt)

            # total number of channels
            self.numChannels = reader.read_int16()
            if self.verbose:
                print(f"\t[ {self.fileName} ] Found {self.numChannels} Channels.")
            # maximum channel length (usually 0 meaning unlimited)
            self.maxLength = reader.read_int32()

            # readaway
            for i in range(self.numChannels):
                reader.read_int32()
            
            # reduced factor (unused)
            redfac = reader.read_int32()

            # loop channels
            for i in range(self.numChannels):
                # create new channel on top of reader
                #! be careful with current stream position
                channel = Channel(reader, self.fileName, self.verbose, self.filterData)

                if not channel.broken and channel.length > 0:                    
                    self.Channels.append(channel)
                elif self.verbose:
                    print(f'\t[ {self.fileName} ] Skipping channel (zero length or invalid data)')

            # seek stream pointer to start of data
            reader.seek(self.dataOffset, SEEK_SET)

            if self.verbose:
                print(f'\t[ {self.fileName} ] Reading Channels...')

            # loop through channels again and access data one after another
            for channel in tqdm(self.Channels, leave=False):
                channel.readData()

            if self.verbose:
                print(f'\t[ {self.fileName} ] Done. {len(self.Channels)} Channels left after filtering.')

                    
            
    def plot(self):
        """Plots the complete file.
        """
        name = os.path.basename(self.filepath)
        fig = plt.figure(name)

        for group in self.Groups:
            group.plot(governed=True)

        plt.draw()
        plt.title(name)
        plt.legend()
        plt.show()