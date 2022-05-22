
[![PyPi Upload](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml/badge.svg)](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml)
![pyPI - Version](https://img.shields.io/pypi/v/apread?label=package%20version)
![PyPI - Downloads](https://img.shields.io/pypi/dm/apread?color=green&label=PyPi%20Downloads&style=plastic)

# **apread** (Catman AP Reader)
> Read binary files produced from catmanAP projects directly into python.

CatmanAP procudes .bin files after each measurement. While it is possible to export as a different format (i.e. txt or asc) it's not efficient because one has to change the export format after every measurement. Here comes the treat: Just export as binary and use this package to work with binary files directly.

After reading all channels from the binary file, the channels are analyzed and every measure-channel will receive a reference to a time channel, depending on the amount of entries in the channels and the fact, that the time-channel has to contain "time" or "zeit" in its name. What that means is, that a channel with x entries and the name "time - 1" will be regarded as the time-channel of any other channel with x Data Entries.

Here is an example plot, generated directly from a binary file:
![apread_demo_out_1](https://user-images.githubusercontent.com/13386367/118563304-9dffba80-b76e-11eb-8730-c982c2ece7db.png)

## Installation/Update

Anywhere with python (note the uppercase U):

```sh
pip install -U apread
```

## How it works
The workflow of the package is straight-forward. You supply a binary file created with CatmanAP and the script will read that into python.

First of all, the binary data is analyzed and packaged into seperate `Channel` objects. When all `Channels` are created, each `Channel.Name` will be checked against `([T|t]ime)|([Z|z]eit)`, which mark time channels which usually are the reference.

These `Channels` marked as `istime` are the basis for `Groups`. Inside a group you will find the `ChannelX` (time channel) and a bunch of other channels in `ChannelsY`, which are the channels containing data in that time domain. The corresponding channels inside a `Group` are found by analyzing their length. Since the total time measured is the same for all groups, it is assumed that `Channels` with the same data-length belong to the same group. Connecting the matching channels to the group give a structured representation of your measurement data.

Now that the Data is available in python you are free to do with that whatever you want. Until Version `1.0.x` there were some features in which you can save the data but that feature has been removed.

## Usage

Lets say you produced a file called `measurements.bin` and you put it in the directory of your python script, then you can create the `APReader` on that file. It's that simple. The Initialization may take some time depending on how large your .bin-File is. 

```python
from apread import APReader

reader = APReader('measurements.bin')   # this will read in the file
``` 

### Print channels
Afterwards you can access the `Channels` by accessing the `APReader.Channels` Member. `Channel` and `Group` implement `__str__` which will return the name and the length of data inside it.

```python
for channel in reader.Channels:
    print(channel)

# "Timechannel 1 - Standard" (120341 Entries)
# "T12_ref" (120341 Entries)
# "T33" (120341 Entries)
# "Timechannel 1 - Quick" (3022344 Entries)
# "F1" (3022344 Entries)
# "ast089" (3022344 Entries)
``` 

```python
for group in reader.Groups:
    print(group)

# "Timechannel 1 - Standard" (2 Data-channels, 120341 Entries)
# "Timechannel 1 - Quick" (2 Data-channels, 3022344 Entries)
``` 

### Plot Channels/Groups
To review your data on the fly, you can plot every entity in the data structure by calling `.plot()`. When plotting, every group will get its own figure window, in which all connected channels are plotted.

```python
# plot the readers data
reader.plot()
# plot all groups
for group in reader.Groups:
    group.plot()
# plot all channels
for channel in reader.Channels:
    channel.plot()
``` 

As you can see, you can access the channels from the reader, which contains all channels (including time channels) or you can access them from the groups.

There are some more functions to plot specific data. When plotting multiple channels each channel gets its own y-axis.
```python
group.plotChannel(0)           # specific channel
group.plotChannels(0,3)        # channel 1 to 3 (1,2,3)
group.plot([0, 2, 4])          # channel 1, 3 and 5
``` 

The same can be applied to the `APReader`. The only difference is that you can plot specific groups instead of channels.
```python
reader.plotGroup(0)           # specific group
reader.plotGroups(0,3)        # group 1 to 3 (1,2,3)
reader.plot([0, 2, 4])        # group 1, 3 and 5
``` 

## Release History
### **Version 1.1**

#### Breaking changes

* Removed post-processing functions, this will be up to the user
    > Since these function change a lot based on current needs, I decided to remove the post-processing functionality completely. The user now needs to do the post-processing on his own, meaning the creation of plots using time and data channels...

#### Changes
* ([hakonbar](https://github.com/leonbohmann/APReader/pull/13)) Added a 'fastload' mode, which takes advantage of the fact that consecutive data points in a measurement channel are stored as a contiguous "byte chunk" in the catman binary format instead of blockwise. You therefore only need to pass a pointer to the first byte as well as the length of the chunk.
* ([hakonbar](https://github.com/leonbohmann/APReader/pull/13)) Added the method "Channel.readExtHeader", in order to get at the attribute "ExportFormat". This attribute indicates the byte depth or precision of the measurement file, allowing the algorithm to differentiate.
* ([hakonbar](https://github.com/leonbohmann/APReader/pull/13)) Added the method "BinaryReader.read_float", which reads in 4-byte floating point numbers.
* ([hakonbar](https://github.com/leonbohmann/APReader/pull/13)) Changed the name of the method "read_single" to "read_byte" to avoid confusion with the newly added method.
* ([hakonbar](https://github.com/leonbohmann/APReader/pull/13)) Added some sample data from HBK with 2-, 4- and 8-byte data.
* Fixed null returning string conversion function
* Using regex to find time channels


### Version 1.0.22
* Fixed an issue with groups where time channels are not recognized
*  now, user is prompted, when suspected time channel is found
*  plotting is not possible when there is no time-channel found
*  save groups and channels even when there is no time channel
### Version 1.0.21
* Updated serialisation-procedures to always encode in `UTF-8`
### Version 1.0.20
* Switched to explicit type hinting with `typing` package (compatibility issues with python <3.9.x)  
### Version 1.0.15/16
* Fixed an issue with saving and non-existent directories
* Added `getas` to generate formatted string without saving
### Version 1.0.14
* Output file-names updated
### Version 1.0.12/13
* Group channels with their time-channel into "groups"
* Multiple plot modes:
    * Whole file
    * Channel/Group only
* Output data
    * json
    * csv

### Version 1.0.11
* Progressbars indicate read-progress of files
* Multiple plot modes

### Version 1.0.0
* Convert catman files to channels

## Meta

Leon Bohmann – mail@leonbohmann.de

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/leonbohmann/apreader](https://github.com/leonbohmann/apreader)
