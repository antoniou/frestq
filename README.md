frestq - Federated REST Task Queue
==================================

Introduction
------------

frestq implements a federated rest task queue. It allows the orchestration of
tasks with different peers with no central coordination authority.

It's developed in python with flask and sqlalchemy. It uses REST Message Queuing
Protocol (RESTQP) for communication of tasks and updates between any two peers.

Installation
------------

The easiest way to install frestq is to do "pip install frestq".  You can also
install it manually if you downloaded it:

1. Install requirements.txt

```
    $ pip install -r requirements.txt
```

2. Install the frestq in the system
```
    $ sudo ./install.py
```

Tutorial
--------

In this simple hello world in frestq, you will need two running frestq server
instances. This due to the fact that frestq is based on the asumption that all
communication is between two peers.

So, you will have launch two different shell sessions. In one of them we will
execute a frestq http server in http://127.0.0.1:5000/ and the other in port
5001. For server A we will just use default settings, but for server B we will
configure port 5001.

First let's see an overall description of how our frestq based service will
work:

    1. user calls to POST http://localhost:5000/say/hello/<username> in server
       A.
    2. flask view in /say/<message> creates a simple task "hello_world" in queue
      "say_queue" to be executed in server B.
    3. server B receives the "say_hello" task, which is executed by an action
      handler.
    4. After the execution of the action handler, server B sends a "finished"
       status update notification to server A, along with the tasks results, if
       any.

So some notes and observations about this:
 * In frestq, the standard way to launch a task is to launch it within a flask
   view in a frestq server. This reduces the complexity of implementation
   because frestq itself is written with flask, so frestq in fact can be used
   as a library without any out of process comunication going on between the
   flask view code and frestq task sender.

   This also needed because the server receiving a task (in this case, server B)
   asumes that he can communicate the updates to the task sender, which must be
   also a frestq server. So to bootstrap, we need to create tasks to be sent
   within server A frestq process itself. Note that this is not design flaw,
   it's a deliberated design choice for a peer to peer task queue.

 * Tasks are created in a "sender server" (A) and executed in "receiver server"
   (B). What task is to be executed is set by the sender server by specifying
   an "action" to be executed, and a "queue" where that action belongs. This is
   simply a way to dispatch different tasks. The receiving server must have a
   python function that acts as an "action handler". The sender can also send
   some input data to be processed.

 * The communication between servers is completely asynchronous. When the task
   is sent from server A to server B, server B immediately processes the
   incoming message with the task data, and without executing the tasks, returns
   the call to server A just saying "task received". Only after doing that the
   task is executed in a thread in server B. When the task finishes whatever it
   needs to do, then server B contacts back with server A sending a task update
   marking the task as finished and also transferring the output result of the
   task.

 * Because everything is executed asynchronously, the initial
   POST http://localhost:5000/say/hello/<username> call is executed also in this
   manner. The task is created, sent, and then the flask view returns without
   waiting for the task to finish.

The code of server_a.py is this:

```
from flask import Blueprint, make_response

from frestq.tasks import SimpleTask
from frestq.app import app, run_app

say_api = Blueprint('say', __name__)

@say_api.route('/hello/<username>', methods=['POST'])
def post_hello(username):
    task = SimpleTask(
        receiver_url='http://localhost:5001/api/queues',
        action="hello_world",
        queue="say_queue",
        data={
            'username': username
        }
    )
    task.create_and_send()
    return make_response("", 200)

app.register_blueprint(say_api)

if __name__ == "__main__":
    run_app()
```

The post_hello is the flask view that initiates the frestq task. This code will
be executed in server A. The "receiver_url" parameter of the SimpleTask created
corresponds with the ROOT_URL of server B.

The code server_b.py is:

```
from frestq import decorators
from frestq.app import app, run_app

# configuration:

SQLALCHEMY_DATABASE_URI = 'sqlite:///db2.sqlite'

SERVER_NAME = 'localhost:5001'

SERVER_PORT = 5001

ROOT_URL = 'http://localhost:5001/api/queues'


# action handler:

@decorators.task(action="hello_world", queue="say_queue")
def hello_world(task):
    print "I'm sleepy!..\n"

    # simulate we're working hard taking our time
    from time import sleep
    sleep(5)

    username = task.task_model.input_data['username']
    task.task_model.output_data = "hello %s!" % username

if __name__ == "__main__":
    run_app(config_object=__name__)
```

You can create each of these two files in the same folder "example/". Asuming
you have already installed frestq requirements (see Step 1 of Install
procedure), you can create the db of both servers this way:

```
    $ ./server_a.py --createdb
    $ ./server_b.py --createdb
```

To launch each server, **run in different terminals** the following two commands:

```
    $ ./server_a.py
    INFO:apscheduler.threadpool:Started thread pool with 0 core threads and 20 maximum threads
    INFO:apscheduler.scheduler:Scheduler started
    INFO:werkzeug: * Running on http://127.0.0.1:5000/
    DEBUG:apscheduler.scheduler:Looking for jobs to run
    DEBUG:apscheduler.scheduler:No jobs; waiting until a job is added
```


```
    $ ./server_b.py
    INFO:apscheduler.threadpool:Started thread pool with 0 core threads and 20 maximum threads
    INFO:apscheduler.scheduler:Scheduler started
    INFO:werkzeug: * Running on http://127.0.0.1:5001/
    DEBUG:apscheduler.scheduler:Looking for jobs to run
    DEBUG:apscheduler.scheduler:No jobs; waiting until a job is added
```

And to launch the hello job, execute in another **new third terminal** the
following command:

```
    $ curl -X POST http://localhost:5000/say/hello/richard.stallman --header "Content-Type:application/json"
```

