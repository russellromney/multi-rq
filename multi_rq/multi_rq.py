import rq
from redis import Redis
import time

def default_check(jobs,mode='results'):
    '''
    the default evaulation function

    - until all the jobs are finished or failed,
        - for each job,
            - if it is finished or failed,
                - add its index position to the completion set
                - if all the index positions are in the completion set,
                    - if in results mode,
                        - return the result of every job
                    - if in jobs mode,
                        - return each job itself and deal with it on your own
    '''
    done = set()
    jobs_set = set(range(len(jobs)))    
    while True:
        for i,job in enumerate(jobs):
            if job.is_finished or job.is_failed:
                done.add(i)
                if done==jobs_set:
                    return None



def mode_check(mode):
    if mode not in ['results','jobs']:
        raise BaseException('multi_rq.apply_async: invalid mode "{}"'.format(mode))
    else:
        return None



class MultiRQ:
    '''
    multi-rq: Simple async multiprocessing with RQ
    
    - useful when you can't use normal multiprocessing, e.g. running long-running functions from gunicorn (the inspiring use case)
    - thread- and process-safe (I think)

    init args (optional):
        q, rq.Queue: an RQ Queue; default is the default rq queue
    '''

    def __init__(self,queue=rq.Queue(connection=Redis())):
        self.queue = queue


    def apply_async(self,target,args_list, check=default_check, timeout=1000, mode='results'):
        '''
        returns a list of results or jobs computed with function <target> by workers of self.q

        parameters:
            required:
            - target, str or function: name of function or function that RQ will execute
            - args_list, iterable: iterable of iterables of function arguments
            
            optional:
            - timeout, int: seconds
            - mode, str: 'results' or 'jobs'

        - modes:
            - results: return only the results of the function + args
            - jobs: return a list containing all the job objects

        roughly similar to multiprocessing.Pool.apply_async
        '''
        mode_check(mode)

        jobs = [self.queue.enqueue(target,*args_) for args_ in args_list]
        t = time.time()
        while time.time()-t < timeout:
            output = check(jobs)
            if mode=='results':
                return [j.result for j in jobs]
            else:
                return jobs
        raise TimeoutError('multi_rq.apply_async: timeout error')