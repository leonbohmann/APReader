from apread.apreader import APReader
import os

# find current directory
dirname = os.path.dirname(__file__)
file = os.path.join(dirname, 'Example_Catman_Data.bin')

outdir = os.path.join(dirname, 'output')

# create a reader
reader = APReader(file)

## print all single channels
#for channel in reader.Channels:    
#    print (f"{channel.Name}: {len(channel.data)} Entries")

for group in reader.Groups:
    print("--------------")
    print (f"Group ({group.ChannelX.Name})")

    for channel in group.Channels:
        print (f"\t{channel.Name:20}: {len(channel.data)} Entries")        

    print("--------------")
    
    
reader.plot()
