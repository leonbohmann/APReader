from apread.apreader import APReader
import os

# find current directory
dirname = os.path.dirname(__file__)
file = os.path.join(dirname, 'testinput.bin')

outdir = os.path.join(dirname, 'output')

# create a reader
reader = APReader(file)

# plot every channel
#for channel in reader.Channels:
#    channel.plot('mat')

# plot every group
# for group in reader.Groups:
#     group.plot()

#reader.plot()

for group in reader.Groups:
    group.save('json', outdir)
for channel in reader.Channels:
    channel.save('json', outdir)


