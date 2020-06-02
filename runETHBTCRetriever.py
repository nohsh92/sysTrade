import time
import sys
from twisted.internet import reactor
from binance.client import Client # Import the Binance Client
from binance.websockets import BinanceSocketManager # Import the Binance Socket Manager
from datetime import datetime
from pynput import keyboard

PUBLIC = 'zYO4K26EluiKCRbgOvmn5cfPXGYNTCU8FSaVkeBJOnzYPVeaq7c2Fm7xmGVycVqM'

SECRET = 'Pggyt3KuoTkykoIoBjAcxagyhAa0pUvz2zD2ljogvoGLMEigNDmwqZvy9qBbbCkR'

# Instantiate a Client
client = Client(api_key=PUBLIC, api_secret=SECRET)

# Instantiate a BinanceSocketManager, passing in the client that you instantiated
bm = BinanceSocketManager(client)

logFilename = ''

break_program = False

conn_key = ''

def on_press(key):
    global break_program
    print(key)
    if key == keyboard.Key.end:
        print('end pressed')
        end_program()
        return False

def create_file():
    global logFilename
    dateTimeObj = datetime.now()
    timeStampStr = dateTimeObj.strftime("%y%m%d_%H%M")
    logFilename = 'ETHBTCLog' + timeStampStr +'.txt'
    return logFilename

def write_to_file(newTradeData):
    global logFilename
    tradeLog = open(logFilename, 'a')
    tradeLog.write(newTradeData)
    tradeLog.close()

# This is our callback function. For now, it just prints messages as they come.
def handle_message(msg):
    # If the message is an error, print the error
    if msg['e'] == 'error':
        print(msg['m'])

    # If the message is  a trade: print time, symbol, price and quantity
    else:
        dataAsString = "Time: {} Symbol: {} Price: {} Quantity: {} \n". format(msg['T'], msg['s'], msg['p'], msg['q'])
        write_to_file(dataAsString)
        print(dataAsString)
    
def end_program():
    global conn_key
    print("ending retrieval:")
    # stop the socket manager
    reactor.stop()
    bm.stop_socket(conn_key)
    bm.close()
    print("stopped program")
    sys.exit("Quitting now...")



def __main__():
    global logFilename, conn_key
    with keyboard.Listener(on_press=on_press) as listener:
        while break_program == False:
            logFilename = create_file()
            # Start trade socket with 'ETHBTC' and use handle_message to... handle the message.
            conn_key = bm.start_trade_socket('ETHBTC', handle_message)
            # then start the socket manager
            bm.start()
            print("starting retrieval:")
            # let some data flow...
            # time.sleep(10)

            # end_program()
        listener.join



__main__()

