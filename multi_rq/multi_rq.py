import rq
from redis import Redis
import time

def default_check(jobs,mode='results'):
    '''
    the default checking function

    - until all the jobs are finished or failed:
        - check whether each is failed or finished
    - when all are finished:
        - return the list of jobs
    '''
    done = set()
    jobs_set = set(range(len(jobs)))    
    while True:
        for i,job in enumerate(jobs):
            if job.is_finished or job.is_failed:
                done.add(i)
                if done==jobs_set:
                    return jobs

def default_proc(jobs,mode):
    '''
    the default processing function
    '''
    if mode=='results':
        return [j.result for j in jobs]
    else:
        return jobs




class MultiRQ:
    '''
    multi-rq: Simple async multiprocessing with RQ
    
    - useful when you can't use normal multiprocessing, e.g. running long-running functions from gunicorn (the inspiring use case)
    - thread- and process-safe (I think)

    init args (optional):
        q, rq.Queue: an RQ Queue; default is the default rq queue
        modes, list: a list of strings of possible modes that check and proc can use
    '''

    def __init__(self, queue=rq.Queue(connection=Redis()),modes=['jobs','results'],check=None,proc=None):
        '''
        optional - specify the default queue, modes, check function, and proc function
        '''
        self.queue = queue
        self.modes = modes
        
        # check
        if check is None:
            self.check = self._default_check
        else:
            self.check = check
        
        # proc
        if proc is None:
            self.proc = self._default_proc
        else:
            self.proc = proc


    def apply_async(self,target,args=(),kwargs={}, check=None, proc=None, queue=None, timeout=1000, mode='results'):
        '''
        returns a list of results or jobs computed with function <target> by workers of self.queue

        parameters:
            required:
            - target, str or function: name of function or function that RQ will execute
            - args_list, iterable: iterable of iterables of function arguments
            
            optional:
            - queue, rq.Queue: the queue used to apply this function; default is self.queue
            - timeout, int: seconds
            - mode, str: 'results' or 'jobs',
            - check, class or function: something that checks the list of jobs for completion; default is self.check
            - proc, class or function: something that processes the output of check; default is self.proc

        does roughly the same thing as multiprocessing.Pool.apply_async
        '''
        # check and proc
        if check is None:
            check = self.check
        if proc is None:
            proc = self.proc
        if queue is None:
            queue = self.queue

        self._mode_check(mode)

        # if args is not iterable or kwargs is not an iterable or dict, raise an error
        k_type = type(kwargs)
        assert k_type==dict or k_type==tuple or k_type==list , "MultiRQ: kwargs must be a dict, list or tuple of dicts"
        if k_type!=dict:
            assert type(kwargs[0])==dict, "MultiRQ: kwargs must be a dict, list or tuple of dicts"

        a_type = type(args)
        assert a_type==tuple or a_type==list , "MultiRQ: args must be a list or tuple"
        
        # enqueue the jobs
        # get the length of args; if len_a is 1, then we can apply the same args to all jobs but only if kwargs is an iterable of dicts
        a_len = len(args)
        if a_len==0 or a_len==1:
            # if args is empty, then kwargs has all the inputs
            if k_type==dict:
                jobs = [queue.enqueue(target,args=args,kwargs=kwargs)]
            else:
                jobs = [queue.enqueue(target,args=args,kwargs=k_) for k_ in kwargs]
        elif a_len>1:
            if k_type==dict:
                jobs = [queue.enqueue(target,args=a_,kwargs=kwargs) for a_ in args]
            else:
                assert a_len==len(kwargs), 'MultiRQ: if both args and kwargs are iterables, they must be the same length'
                jobs = [queue.enqueue(target,args=a_,kwargs=k_) for a_,k_ in zip(args,kwargs)]


        # apply check and proc
        t = time.time()
        while time.time()-t < timeout:
            jobs = check(jobs)
            return proc(jobs,mode)
        raise TimeoutError('MultiRQ: timeout error')


    def _mode_check(self,mode):
        '''
        checks mode validity
        '''
        if mode not in self.modes:
            raise Exception('multi_rq.apply_async: invalid mode "{}"; available modes are: {}'.format(mode,str(self.modes)))
        else:
            return None

    def _default_check(self,jobs):
        '''
        the default checking function

        - until all the jobs are finished or failed,
            - for each job,
                - if it is finished or failed,
                    - add its index position to the completion set
                    - if all the index positions are in the completion set,
                        - return the list of jobs
        '''
        done = set()
        jobs_set = set(range(len(jobs)))    
        while True:
            for i,job in enumerate(jobs):
                if job.is_finished or job.is_failed:
                    done.add(i)
                    if done==jobs_set:
                        return jobs


    def _default_proc(self,jobs,mode):
        '''
        the default processing function
        '''
        if mode=='results':
            return [j.result for j in jobs]
        else:
            return jobs
