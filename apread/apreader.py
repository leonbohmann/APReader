import os
# binary imports
from os import SEEK_SET
from typing import List
# import this to show warnings
import warnings
from matplotlib import pyplot as plt
from tqdm import tqdm

# channel definition
from apread.entries import Channel, Group
# binary reader to read binary files
from apread.binaryReader import BinaryReader

class APReader:
    
    """
    All channels unsorted.    
    """
    Channels: List[Channel]
    """
    Grouped channels.    
    """
    Groups: List[Group]

    def __init__(self, path):
        """Creates a new APReader based on a .binary file (path).

        Args:
            path (str): path to a catmanAP binary file.
        """
        self.filepath = path
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
            else:
                print("\t [WARNING] Channel-group does not contain a time-channel")            

            # create new group based on the groups listed
            self.Groups.append(Group(group))
        pass

        

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
            print(f"\t[ APREAD ] Found {self.numChannels} Channels in {os.path.basename(self.filepath)}.")
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
                # be careful with current stream position
                channel = Channel(reader)

                if not channel.broken and channel.length > 0:                    
                    self.Channels.append(channel)
                else:
                    print(f'\t[ APREAD ] Skipping channel (zero length or invalid data)')

            # seek stream pointer to start of data
            reader.seek(self.dataOffset, SEEK_SET)


            print('\t[ APREAD ] Reading Channels...')
            # loop through channels again and access data one after another
            for channel in tqdm(self.Channels, leave=False):
                channel.readData()

            print(f'\t[ APREAD ] Done. {len(self.Channels)} Channels left after filtering.')

                    
            
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