import time
import json
import gevent

from uuid import uuid4

from locust import HttpUser, TaskSet, task, events, User
import websocket

class SocketClient(object):
    def __init__(self, host):
        self.host = host
        self.session_id = uuid4().hex
        self.connect()

    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.settimeout(10)
        self.ws.connect(self.host)

##        events.quitting += self.on_close


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
        print("closed connection")
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