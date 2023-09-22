from __future__ import annotations

import multiprocessing as mp
import os
import re

# binary imports
from os import SEEK_SET
from typing import List

from matplotlib import pyplot as plt
from tqdm import tqdm
import numpy as np
import numpy.typing as nptyp
from typing import Tuple
# binary reader to read binary files
from apread.binaryReader import BinaryReader

# channel definition
from apread.entries import Channel, Group

def get_cmap(n, name='jet'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.get_cmap(name, n)

def plot_multiple_datasets(datasets: list[Tuple[nptyp.NDArray, nptyp.NDArray, str, str, str]]\
        , plt_title = ''):
    """
    Plots multiple datasets on the same plot with separate y-axes.

    Parameters:
    datasets (list of tuples): Each tuple should contain (x, y, color, ylabel, title)
    """
    fig, ax = plt.subplots()
    cmap = get_cmap(len(datasets)+5, name='Set1')
    lbs = []
    for i, data in enumerate(datasets):
        x, y, style, ylabel, title = data

            
        if i == 0:
            ax1 = ax
        else:
            ax1 = ax.twinx()
            ax1.spines['right'].set_position(('outward', 60*(i-1)))

        if style is None: 
            l = ax1.plot(x, y, color=cmap(i), label=title)[0]
        else:
            l = ax1.plot(x, y, style, label=title)[0]
            
        ax1.set_ylabel(ylabel, color=l.get_color())
        ax1.tick_params(axis='y', colors=l.get_color())
        lbs.append((l, ylabel))

    ax.legend([x[0] for x in lbs], [x[1] for x in lbs])
    ax.set_title(plt_title)
    fig.tight_layout()
    plt.show()
    return fig,ax

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

    def __init__(self, path, verbose=False, parallelPool = None):
        """Creates a new APReader based on a .binary file (path).

        Args:
            path (str): path to a catmanAP binary file.
            verbose (boolean): Show debug output.
            parallelPool (multiprocessing.Pool): If passed, the loading of files will be
                done on the threads in the pool.
        """
        self.verbose = verbose
        self.filepath = path
        self.fileName = os.path.splitext(os.path.basename(path))[0]
        self.parallelLoad = parallelPool is not None
        self.parallelPool = parallelPool
        self.Channels = []
        self.Groups = []
        
        if self.parallelLoad:
            print(f'INFO: Using {len(mp.active_children())} processes to load data.')
        
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
            if channel.length not in channelGroups:
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
                if re.match(r"([T|t]ime)|([Z|z]eit)",channel.Name) is not None:
                    timeChannel = channel
                    # there is only one time-channel
                    break

                # instead of assuming, ask the user if the timechannel is the one with "seconds"
                if "s" == channel.unit:
                    # this should be uncommented for the testing timing functions to be usable
                    # timeChannel = channel
                    # break
                
                    if input(f"Is '{channel.Name}' your time/reference channel? [y/n] ") == "y":
                        timeChannel = channel
                        break
                                
            # set the time-channel on every channel but itself
            if timeChannel != None:
                for channel in group:
                    if channel is not timeChannel:
                        channel.Time = timeChannel
                        channel.isTime = False
                    else:
                        channel.isTime = True
            else:
                print("\t [ERROR] Channel-group does not contain a time-channel!")
                print("\t  The current group will not be included in this output.")
                continue
            
            # create new group based on the groups listed
            self.Groups.append(Group(group, self.fileName, self.verbose))
        
        if len(self.Channels) > 0:
            self.date = self.Channels[0].date
        
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
                _ = reader.read_string(lresakt)

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
            _ = reader.read_int32()

            # loop channels
            for i in range(self.numChannels):
                # create new channel on top of reader
                #! be careful with current stream position
                channel = Channel(reader, self.fileName, self.filepath,\
                    self.verbose, self.parallelPool)

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
       
    def collectChannels(self, channel_names: list[str]) -> list[Channel] | Channel:
        chans = []
        
        for cname in channel_names:
            for c in self.Channels:
                if c.Name == cname:
                    chans.append(c)
        # for c in self.Channels:
        #     if any([x in c.Name for x in channel_names]):
        #         chans.append(c)
                
        return chans if len(chans) > 1 else chans[0]
      
    def collectDatasets(self, channel_names: list[str]) -> list[Tuple[nptyp.NDArray, nptyp.NDArray, str, str, str]]:
        chans = []
        for c in self.Channels:
            if any([x in c.Name for x in channel_names]):
                chans.append((c.Time.data, c.data, None, f'{c.Name}[{c.unit}]', c.Name))
                
        return chans
              
    def plot(self, groupIndices=None, sameAxis = False):
        """Plots the complete file.
        """
        for group in self.Groups:
            group.plot(sameAxis = sameAxis)     
            
    def plotGroup(self, channelIndex):
        """Plot a specific channel

        Args:
            channelIndex (int): The index of the channel.
        """
        for group in self.Groups:
            group.plotChannels(channelIndex, channelIndex)
    
    def plotGroups(self, start, end):
        """Plot a range of channels

        Args:
            start (int): Starting index, first channel is 0.
            end (int): Ending index, supports -[index] to mark index from the end.
        """
        for group in self.Groups:
            group.plot(range(start,end))                         
            
            
    def printSummary(self):
        for group in self.Groups:
            print('---------')
            print(group.Name)
            for channel in group.ChannelsY:
                print(f'\t{channel.Name} ({len(channel.data)})')