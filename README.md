# multi-rq
Simple async multiprocessing with RQ. Inspired by launching long CPU-intensive tasks from gunicorn.

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
- repeatedly checks whether all the jobs are finished or failed (using the _check function_)
- returns the results (_results mode_) or the job objects (_jobs mode_). 

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
Python
```
import rq
from basic_test import wait
from multi_rq import MultiRQ

mrq = MultiRQ()
nums = [[(i,j)] for i,j in zip(range(0,20,2),range(11,21))]
mrq.apply_async(np.mean,nums)
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

## Advanced usage
As `multi-rq` is very simple, the power lies in the _check function_ used to check job status. This function allows you to return what you want, do custom manipulation, etc. The default check function is `default_check` in `rq-multi/rq_multi/rq_multi.py`. 

You can also specify the queue you want to use, with various options, in the class call: 
```
mrq = MultiRQ(queue = rq.Queue('myqueue',connection=Redis('redis://url',...))
```


## Using with Supervisor

Supervisor is a great way to keep things running in the background for Python with minimal effort. This quick guide assumes you're using Ubuntu.

You need some things to make supervisord work well with redis:
- redis running as a service (easiest) [great guide here](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04)
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

/etc/redis/redis.conf
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
