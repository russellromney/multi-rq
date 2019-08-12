import rq
from basic_test import wait
from multi_rq.multi_rq import MultiRQ
import numpy as np

mrq = MultiRQ()
nums = [[(i,j)] for i,j in zip(range(0,20,2),range(11,21))]
assert mrq.apply_async(np.mean,nums) == [5.5, 7.0, 8.5, 10.0, 11.5, 13.0, 14.5, 16.0, 17.5, 19.0]

assert mrq.apply_async

print('multi-rq: all tests passed')


