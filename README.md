<div align="center">
   <img src="logo.svg" height="200">
</div>

<div align="center">
  <h1>
  apread
  </h1>
  <h3>
  previously: Catman Reader
  </h3>
</div>


[![PyPi Upload](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml/badge.svg)](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml)
![pyPI - Version](https://img.shields.io/pypi/v/apread?label=package%20version)
![PyPI - Downloads](https://img.shields.io/pypi/dm/apread?color=green&label=PyPi%20Downloads&style=plastic)
[![Downloads](https://static.pepy.tech/personalized-badge/apread?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Total%20Downloads)](https://pepy.tech/project/apread)


## Support this project
<a href="https://www.buymeacoffee.com/leonbohmann" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

## Cite this project

If you use this software in any of your work, please cite it using the "Cite this repository" button in the right sidebar or use this:

```
@software{leonbohmann_APReader,
   author = {Bohmann, Leon},
   doi = {10.5281/zenodo.8369804},
   month = sep,
   title = {{leonbohmann/APReader: v1.1.2}},
   url = {https://github.com/leonbohmann/APReader},
   version = {v1.1.2},
   year = {2023}
}
```

## General

> Read binary files produced from catmanAP projects directly into python.

CatmanAP procudes .bin files after each measurement. While it is possible to export as a different format (i.e. txt or asc) it's not efficient because one has to change the export format after every measurement. Here comes the treat: Just export as binary and use this package to work with binary files directly.

After reading all channels from the binary file, the channels are analyzed and every measure-channel will receive a reference to a time channel, depending on the amount of entries in the channels and the fact, that the time-channel has to contain "time" or "zeit" in its name. What that means is, that a channel with x entries and the name "time - 1" will be regarded as the time-channel of any other channel with x Data Entries.

Here is an example plot, generated directly from a binary file:
![apread_demo_out_1](https://user-images.githubusercontent.com/13386367/169707732-240a916e-228f-4ef9-8c3c-e560a2647c97.png)

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

### External Header

Thanks to ([hakonbars PR13](https://github.com/leonbohmann/APReader/pull/13)) you are now able to access external header information using `channel.exthdr`, a dicitionary containing all keys as described in [this sheet](https://github.com/leonbohmann/APReader/blob/dev-2/test/catmanBinaryFormat.xls).

```python
['T0']                 # ACQ timestamp info (NOW format)
['dt']                 # ACQ delta t in ms
['SensorType']         # IDS code of sensor type
['SupplyVoltage']      # IDS code supply voltage
['FiltChar']           # IDS code of filter characteristics
['FiltFreq']           # IDS code of filter frequency
['TareVal']            # Current value in tare buffer
['ZeroVal']            # Current value in zero adjustment buffer
['MeasRange']          # IDS code of measuring range
['InChar']             # Input characteristics (0=x1,1=y1,2=x2,3=y2)
['SerNo']              # Amplifier serial number
['PhysUnit']           # Physical unit (if user scaling in effect, this is the user unit!)
['NativeUnit']         # Native unit
['Slot']               # Hardware slot number
['SubSlot']            # Sub-channel, 0 if single channel slot
['AmpType']            # IDS code of amplifier type
['APType']             # IDS code of AP connector type (MGCplus only)
['kFactor']            # Gage factor used in strain gage measurements
['bFactor']            # Bridge factor used in strain gage measurements
['MeasSig']            # IDS code of measurement signal (e.g. GROSS, NET) (MGCplus only)
['AmpInput']           # IDS code of amplifier input (ZERO,CAL,MEAS)
['HPFilt']             # IDS code of highpass filter
['OLImportInfo']       # Special information used in online export file headers
['ScaleType']          # 0=Engineering units, 1=Electrical
['SoftwareTareVal']    # Software tare (zero) for channels carrying a user scale
['WriteProtected']     # If true, write access is denied
['NominalRange']       # CAV value
['CLCFactor']          # Cable length compensation factor (CANHEAD only)
['ExportFormat']       # 0=8-Byte Double, 1=4-Byte Single, 2=2-Byte Integer (FOR CATMAN BINARY EXPORT ONLY!)
```

### Parallel reading of data

> Only available from version `v1.1.1-alpha1` and above

See `test/testing.py` for a full example. Modify the following around your `APReader` call:

```python
import multiprocessing as mp
...


if __name__ == '__main__': # this line has to be included!
    # without 'processes=...'!
    pool = mp.Pool()

    # pass the pool to the reader
    reader = APReader(file, parallelPool=pool)

    # make sure to close the pool after you are done with it
    mp.close()
    mp.join()
```

For the parallel loading to work, you have to define a parallel pool of processes in your top-level script. These processes will be accessed from within `APReader`-Functions. When passing no arguments to `mp.Pool()` it will automatically create as many processes as possible, according to the amount of threads your CPU allows (cores + virtual cores). It does not make sense to pass in more, since the `APReader` spawns the same amount of processes as there are CPU Threads. Increasing the amount of processes in your pool does not increase the amount of parallelism. It is fixed.

> Keep in mind, that parallelisation is not always faster. Spawning of processes is expensive and can be wasteful for small files.

The results from `APReader` stay the same and you can continue your analysis.

## Release History

### Version 1.1.1-alpha1

* Added converted timestamp property on channels (`Channel.date`)
  * *Property `Channel.time` will be deleted at some point in the future...*
* Parallel reading of binary files
  * Max degree of parallelism is automatically set to amount of available cores
* ----------------------------
* ----------------------------

#### Version 1.1

##### Breaking changes

* Removed saving functions, this will be up to the user
    > Since these function change a lot based on current needs, I decided to remove the post-processing functionality completely. The user now needs to do the post-processing on his own, meaning the creation of plots using time and data channels...

##### Changes

* ([hakonbar PR13](https://github.com/leonbohmann/APReader/pull/13)) Differentiate floating point precision
* ([hakonbar PR13](https://github.com/leonbohmann/APReader/pull/13)) Reading additional header information
* ([hakonbar PR13](https://github.com/leonbohmann/APReader/pull/13)) Supplying binary format reference
* Fixed null returning string conversion function
* Using regex to find time channels
* Improved plotting with multiple axes
* Printing channels and groups will now give a summary instead of all data

#### Version 1.0.22

* Fixed an issue with groups where time channels are not recognized
* now, user is prompted, when suspected time channel is found
* plotting is not possible when there is no time-channel found
* save groups and channels even when there is no time channel

#### Version 1.0.21

* Updated serialisation-procedures to always encode in `UTF-8`

#### Version 1.0.20

* Switched to explicit type hinting with `typing` package (compatibility issues with python <3.9.x)

#### Version 1.0.15/16

* Fixed an issue with saving and non-existent directories
* Added `getas` to generate formatted string without saving

#### Version 1.0.14

* Output file-names updated

#### Version 1.0.12/13

* Group channels with their time-channel into "groups"
* Multiple plot modes:
  * Whole file
  * Channel/Group only
* Output data
  * json
  * csv

#### Version 1.0.11

* Progressbars indicate read-progress of files
* Multiple plot modes

#### Version 1.0.0

* Convert catman files to channels

## Meta

Leon Bohmann – mail@leonbohmann.de

Distributed under the MIT license. See ``LICENSE`` for more information.

This software comes with no warranty, expressed or implied. Use at your own risk!

[https://github.com/leonbohmann/apreader](https://github.com/leonbohmann/apreader)
