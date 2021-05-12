import apread
import os

# find current directory
dirname = os.path.dirname(__file__)
file = os.path.join(dirname, 'testinput.bin')

# create a reader
reader = apread.APReader(file)

# plot every channel
for chan in reader.Channels:
    chan.plot('mat')

