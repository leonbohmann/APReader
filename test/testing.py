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

    if loadInParallel:
        pool = mp.Pool()        
        
    # create a reader
    reader = APReader(file, parallelPool=pool)

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
