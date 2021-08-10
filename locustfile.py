import time
import json
import gevent

from uuid import uuid4

from locust import HttpUser, TaskSet, task, events, User
import websocket

import logging

# Gets or creates a logger
logger = logging.getLogger(__name__)  

# set log level
logger.setLevel(logging.INFO)

# define file handler and set formatter
file_handler = logging.FileHandler('logfile.log')
formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)




all_socs = []

@events.quitting.add_listener
def on_quit(environment, **kwargs):
    for socs in all_socs:
        socs.on_close()

    

class SocketClient(object):
    def __init__(self, host):
        self.host = host
        self.session_id = uuid4().hex
        self.connect()

    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.settimeout(10)
        self.ws.connect(self.host)
        logger.info('New Socket Connection Created')



    def send_with_response(self, payload):
        json_data = json.dumps(payload)

        g = gevent.spawn(self.ws.send, json_data)
        g.get(block=True, timeout=2)
        g = gevent.spawn(self.ws.recv)
        try:
            result = g.get(block=True, timeout=60)

            json_data = json.loads(result)
        except:
            json_data = {}
        return json_data

    def on_close(self):
        logger.info('Socket Connection Closed')
        self.ws.close()


    def send(self, payload):
        start_time = time.time()
        e = None
        try:
            data = self.send_with_response(payload)
            assert 'error' not in data
        except AssertionError as exp:
            e = exp
        except Exception as exp:
            e = exp
            self.ws.close()
            self.connect()
        elapsed = int((time.time() - start_time) * 1000)
        if e:
            events.request_failure.fire(request_type='sockjs', name='send',
                                        response_time=elapsed, response_length=0,exception=e)
        else:
            events.request_success.fire(request_type='sockjs', name='send',
                                        response_time=elapsed,
                                        response_length=0)
    

        
class WSBehavior(TaskSet):
    @task(1)
    def action(self):
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "programSubscribe",
            "params": [
                "Vote111111111111111111111111111111111111111",
                {
                    "encoding": "base64",
                    "commitment": "finalized"

                }
            ]
        }
        self.client.send(data)
    
  

class WSUser(User):
    task_set = WSBehavior
    min_wait = 1000
    max_wait = 3000
    tasks = {WSBehavior:1}

    def __init__(self, *args, **kwargs):
        super(WSUser, self).__init__(*args, **kwargs)
        self.client = SocketClient('ws://%s' % self.host)
        all_socs.append(self.client)

    def on_start(self):
        logger.info('New User Spawned')
    
    def on_stop(self):
        logger.info('User Deleted')
        self.client.on_close()
        
        
        

