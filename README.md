# multi-rq
Simple async multiprocessing with RQ.

Think `multiprocessing.Pool.apply_async`, plus modular modes, queues, completion checking and processing as advanced options. Inspired by launching long CPU-intensive tasks from gunicorn.

```
# basic_test.py
import time
def wait(i,j):
    print(i)
    return sum((i,j))
```
```
import rq
from multi_rq import MultiRQ
from basic_test import wait

mrq = MultiRQ()
mrq.apply_async(wait, [(i,j) for i,j in zip(range(10),range(10))] )
# >>> [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

---

This is an extension of [rq](https://github.com/rq/rq) that emulates the `Pool.apply_async` behavior in `multiprocessing` with a task queue. I use it with [Supervisor](http://supervisord.org/) (see below for guide).

Fundamentally it just 
- queues all your tasks
- repeatedly checks whether all the jobs are finished or failed (using the `check` function)
- returns the results (`'results'` mode) or the job objects (`'jobs'` mode) (or using custom modes)

Please raise issues or pull requests if you have any!

**Setup**

Install dependencies
```
# command line
pip install rq
git clone https://github.com/russellromney/multi-rq.git
cd multi-rq
```

**Basic use**

Launch redis-server and RQ workers
``` 
# command line
redis-server &
rq worker &
rq worker &
rq worker &
```
basic_test.py
```
import time
def wait(i,j):
    print(i)
    return sum((i,j))
```
Python
```
import rq
from basic_test import wait
from multi_rq import MultiRQ

mrq = MultiRQ()
nums = [[(i,j)] for i,j in zip(range(0,20,2),range(11,21))]
mrq.apply_async(wait,nums)
# >>> [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

## Tips

The biggest problem people have with RQ is making sure the module containing their function is available for import. The best way to do this is just by [arranging your python projects as packages](https://stackoverflow.com/questions/7732685/python-local-modules). e.g.
```
myproject/
    __init__.py
    mymodules/
        __init__.py
        myfunctions.py
```
```
from mymodules import myfunctions
...
mrq.apply_async(myfunctions.func,...)
```

This will save you many headaches.

## Advanced use - custom queue, modes, _check_ and _proc_ function**
As `multi-rq` is very simple at heart, the power lies in the _processing function_ `proc` and the _checking function_ `check` used to check job status and process the results in some way.

**Custom queue**
You can specify the queue you want to use, with various options, in the class call or later: 
```
# set queue in class instantiation
mrq = MultiRQ(queue = rq.Queue('myqueue',connection=Redis(...))
# change attribute
mrq.queue = rq.Queue('newqueue',connection=Redis(...))
```
The default queue is just the Redis `'default'` queue.

**Custom modes**
Processing can depend on the mode. Add modes in the class instance or by changing the attribute:
```
mrq = MultRQ(...,modes=['mymode','othermode'])
mrq.modes = ['newmode','funmode']
```

**`check` function**
The `check` function allows you to set your own logic for determinining completion. The default check function is `MultiRQ._default_check`, which just checks whether each is failed or finished and returns the list of jobs when done. If `check` is not specified in the function call, the current self.check is used

Change this by passing your custom check function with requirements:
- accepts a list of jobs
- checks when your jobs are done
- when done, returns a list of jobs or other things (depending on your `proc` function)
e.g.
```
def my_check_func(jobs):
    do_something_to_check_completion
    return jobs

results = mrq.apply_async(target, args, check=my_check_func)
mrq = MultiRQ(...check=my_check_func)
mrq.check = my_check_func
```

**`proc` function**
The processing (`proc`) accepts the output of the `check` function and the `mode` and does some processing steps before returning the output. The default processing function is `MultiRQ._default_proc` which just returns the results or jobs depending on the mode. If `proc` is not specified in the function call, the current self.proc is used.

Change this by passing your custom proc function with requirements:
- accepts output of `check` function and the mode
- processes ouput
- returns your output
e.g.
```
def my_proc_func(jobs,mode):
    if mode=='mymode':
        return [job.do_this for job in jobs]
    elif mode=='othermode':
        return ...
results = mrq.apply_async(target, args, proc=my_proc_func)
mrq = MultiRQ(...proc=my_proc_func)
mrq.proc = my_proc_func
```
---
## Using with Supervisor

Supervisor is a great way to keep things running in the background for Python with minimal effort. This quick guide assumes you're using Ubuntu.

You need some things to make supervisord work well with redis:
- redis running as a service (easiest) [great setup guide here](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04)
- path to your Python distribution `bin`. Mine is `.../anaconda/envs/py35/bin`
- rqsettings.py file; a basic settings file for RQ workers (see example)
- rqworker.py file; the launch script for your workers (see example)
- supervisord.conf file; the config for supervior

Redis as a service
```
sudo apt update
sudo apt install redis-server
sudo nano /etc/redis/redis.conf
```
/etc/redis/redis.conf (only need to edit/add this line)
```
...
supervised systemd
...
```
Restart redis or check status
```
sudo systemctl restart redis.service
sudo systemctl status redis
```

Install supervisor and check path to python dist
```
pip install supervisor
which python
# >>> /path/to/python/bin/python
```
supervisord.conf (copy the rest from example file)
```
[program:defaultworker]
...
command=/path/to/python/bin/rq worker -c rqsettings default
...
; This is the directory from which RQ is ran. Be sure to point this to the
; directory where your source code is importable from
; and where rqsettings and rqworker python files are
directory=/path/to/directory
...
```
Launch supervisord (with your python bin path)
```
/path/to/anaconda/envs/py35/bin/supervisord -c /path/to/supervisord.conf
```
Check status or reload
```
supervisorctl status
# >>> defaultworker:defaultworker-0    RUNNING   pid 43378, uptime 0:00:04 
...

supervisorctl reload
# >>> Restarted supervisord
```

With all that set up, you now have 5 rq workers on your default Redis queue waiting to work for you at anytime! 
