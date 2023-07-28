from datetime import datetime
from apread.apreader import APReader
import os
import multiprocessing as mp

if __name__ == '__main__':
    pool = None # default value, do not change

    # find current directory
    dirname = os.path.dirname(__file__)
    file = os.path.join(dirname, 'Example_Catman_Data.bin')

    outdir = os.path.join(dirname, 'output')

    # specify wether to use parallel loading of channel data
    loadInParallel = False
    speedTest = False
    
    if loadInParallel:
        pool = mp.Pool()        
    
    # t0 = datetime.now()
    # # create a reader
    # for i in range(1,1000):
    #     reader = APReader(file, parallelPool=pool)

    # t1 = datetime.now()
    
    # print(t1-t0)

    t0 = datetime.now()
    # create a reader
    for i in range(1,1000 if speedTest else 1):
        reader = APReader(file, parallelPool=pool)

    t1 = datetime.now()
    
    print(t1-t0)

    if loadInParallel:
        pool.close()
        pool.join()
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

def channel_dates():
    reader = APReader("file.bin")
    
    for channel in reader.Channels:
        print(channel.date) # 12.1.2023: 18:08 ...

def test2():
    reader = APReader("file.bin")

    for group in reader.Groups:
        # alle channels in der gruppe
        channels = group.Channels
        # X-Channel der Gruppe (Zeit)
        channelX = group.ChannelX
        # alle Y channels, also Messreihen der Gruppe
        channelsY = group.ChannelsY
        
        # data in z.B. der ersten Messreihe
        channel1 = channelsY[0]
        # das ist das numpy-array mit den tatsächlichen Werten drin
        data = channel1.data
        print(data)
        
    # ALTERNATIV (alle channels in der bin Datei):
    for channel in reader.Channels:
        print(channel.data)
        