"""
Tools to handle Raspberry Pi connection to clients.
"""
import bluetooth
import json
import websockets
import asyncio 
from threading import Thread
import socket
import time
from queue import Queue
import requests

from Logger import Logger

# TODO queue in connections
# make client input and output queue, 
# so that each client can communicate bidirectionally. 
def wifi_connected():
    "return true if wifi is connected."
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        res = True
    except:
        res = False
    finally:
        s.close()
    return res


def get_ip():
    "Get host ip."
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        # IP = '127.0.0.1'
        IP = '192.168.0.1' # default serve here.
    finally:
        s.close()
    return IP

def internet_connected():
    try:
        res = requests.get('https://www.google.com',timeout=3)
        return res.status_code==200
    except:
        return False

class WebsocketServer():
    """
    WebsocketServer listen to websocket connections.
    Can only respond to incoming json serilized string.
    """
    def __init__(self, ip, port=8765, logger=None):
        "Start websocket server at ip:port"
        self.IP = ip
        self.port = port
        self.clients = set()
        self.logger = logger
        self.websocketAddr = f"ws://{self.IP}:{self.port}"
        self.websocketServer = None
        self.Q = Queue()

    def send(self,json_data):
        "send a dictionary to clients"
        self.Q.put_nowait(json.dumps(json_data, separators=(',', ':')))

    def stopServer(self):
        "Disconnect all clients before exit."
        self.logger.websocketStatus = 'stopped'
        if self.websocketServer:
            self.websocketServer.close()
            self.websocketServer=None
        # print((self.websocketServer.sockets))
        
        
    def startInLoop(self,loop):
        "run websocket server in a loop"
        asyncio.run_coroutine_threadsafe(self.startServer(),loop)
        asyncio.run_coroutine_threadsafe(self.notify_clients(),loop)
    
    def getClients(self):
        "return connected clients"
        return [i.remote_address for i in self.clients]

    async def startServer(self):
        self.logger.debug(f'Started WebsocketServer on ws://{self.IP}:{self.port}')
        self.logger.websocketStatus = 'running'
        self.websocketServer = await websockets.server.serve(
            self.ws_handler, self.IP, self.port, ping_interval=None
        ) 
    async def ws_handler(self, ws, uri):
        "Websocket connection handler."
        self.clients.add(ws)
        self.logger.debug(f'Websocket connection from {ws.remote_address}. Total clients: {len(self.clients)}.')
        try:
            async for msg in ws:
                # self.logger.main.peripheral.led.show('wifi',[100,1],1,)
                try:
                    msg = json.loads(msg)
                except json.decoder.JSONDecodeError:
                    self.logger.error(
                        f'Websocket Client {ws.remote_address} sent non-json message, msg: <{str(msg)[0:100]}>')
                    await ws.send(json.dumps({'status': 'error', 'data': 'Message not json.'}, separators=(',', ':')))
                    continue
                response = self.logger.messageHandler(msg) 

                if response:
                    await ws.send(json.dumps(response, separators=(',', ':'))) 
        except Exception as e:
            self.logger.error(
                f'Websocket client {ws.remote_address} Exception: {e}')
        finally:
            self.clients.remove(ws)

    async def notify_clients(self):
        "notify clients with information Q data."
        while True:
            # send messages immediately. even if there is no clients.
            while not self.Q.empty():
                msg = self.Q.get()                
                if len(self.clients) > 0:                    
                    await asyncio.wait([client.send(msg) for client in self.clients])
            await asyncio.sleep(0.1)






class ClientModule(Thread,Logger):
    "Serving connection via bluetooth or wifi, via websockets."
    def __init__(self,main):
        self.main = main
        super().__init__()
        Logger.__init__(self,'client',fileHandler=main.fileHandler)
        
    def initialize(self,**kwargs):
        ""
        
        self.websocketIP = get_ip()
        self.websocketPort = '8877'
        try:
            self.websocketServer = WebsocketServer(ip=self.websocketIP,port=self.websocketPort, logger=self,)
        except Exception as e:
            self.error(f'Initiate websocket server error:{e}')
            self.websocketStatus = 'error'

        self.bluetoothStatus = 'disabled'
        # self.bluetoothStatus = 'starting'
        # try:
        #     self.bluetoothServer = BluetoothServer(port=bluetoothPort, uuid=bluetoothUUID,listen=bluetoothListen, logger=self)
        # except Exception as e:
        #     self.error(f"initiate bluetooth server error:{e}")
        #     self.bluetoothStatus = 'error'
    
    def run(self):
        self.initialize()
        try:
            self.websocketServer.startInLoop(self.main.mainLoop) 
        except Exception as e:
            self.logger.error(f"ClientModule.run: start websocket error: {e}")
            self.websocketStatus = 'error'

    
    def stop(self):
        self.cleanUp()

    def restartWebsocketServer(self):
        "restart websocket server"
        def restartWs():
            "restart module"
            try:
                time.sleep(1)
                self.websocketServer.stopServer()
                time.sleep(1)
                self.websocketIP = get_ip()
                self.websocketServer = WebsocketServer(ip=self.websocketIP,port=self.websocketPort, logger=self,)
                self.websocketServer.startInLoop(self.main.mainLoop) 
                self.debug(f'Restarted ws on {self.websocketServer.websocketAddr}.')
            except Exception as e:
                self.error(f"Restart ws {self.websocketIP}-{self.websocketPort} error : {e}")
        Thread(name='restart WS server',target=restartWs).start()
        self.debug('Websocket Server restarted.')

    def cleanUp(self): 
        "clean up"
        try:
            self.websocketServer.stopServer()
            self.debug('Websocket Server stop.')
        except Exception as e:
            self.error(f'Stop websocket server error: {e}')
     
       
    def messageHandler(self,msg):
        """
        handle message from clients
        msg format: {
            action: moduleName.attr.attr, 
            other key:value pairs to pass to actuion function.
        }
        return value format: {
            action: same as msg.
            status: 'error' or 'ok'.
            data: response. 
        }
        """
        action = msg.pop('action',None) 
        if not action:
            self.error(f"Client Invalid message {msg}")
            return {'status':'error', 'data': 'Invalid Message','action':action}
        target = self.main
        for chain in action.split('.'):
            target = getattr(target,chain.strip(),'__NON_EXISTING_MODULE__')
        try:
            if callable(target): 
                try:
                    return {'status':'ok', 'data': target(**msg),'action':action}
                except Exception as e:
                    return {'status':'error', 'data': str(e),'action':action} 
            elif target == '__NON_EXISTING_MODULE__':
                return {'status': 'error', 'data': f"Module {action} doesn't exist.",'action':action}
            else:
                return {'status':'ok', 'data': target,'action':action}
        except Exception as e:
            self.error(f'Message handling error on <{action}>, msg:<{msg}>, error: {e}')
            return {'status':'error','data':str(e),'action':action}

        
    
        

