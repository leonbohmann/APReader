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
    for i in range(1,1000 if speedTest else 2):
        reader = APReader(file, parallelPool=pool)

    t1 = datetime.now()

    print(t1-t0)

    if loadInParallel:
        pool.close()
        pool.join()




def example1():
    """Example function showcasing quick usage of the APReader class with multiprocessing support."""
    with mp.Pool() as pool:
        reader = APReader("input.bin", parallelPool=pool)