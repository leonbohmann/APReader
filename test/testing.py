from apread.apreader import APReader
import os
import multiprocessing as mp

# find current directory
dirname = os.path.dirname(__file__)
file = os.path.join(dirname, 'Example_Catman_Data.bin')

outdir = os.path.join(dirname, 'output')

# create parallel pool

mp.freeze_support()
if __name__ == '__main__':
    pool = mp.Pool(12)
    # create a reader
    reader = APReader(file, parallelLoad=True, parallelPool=pool)

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
