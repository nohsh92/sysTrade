import time, sys, os
from twisted.internet import reactor
from binance.client import Client # Import the Binance Client
from binance import ThreadedWebsocketManager # Import the Binance Socket Manager
from datetime import datetime
from pynput import keyboard
from config import PUBLIC, SECRET
from os import path


# tutorial @ https://livedataframe.com/live-cryptocurrency-data-python-tutorial/ #

# Instantiate a BinanceSocketManager, passing in the client that you instantiated


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
    print("Creating File")
    dateTimeObj = datetime.now()
    timeStampStr = dateTimeObj.strftime("%y%m%d_%H%M")
    if(path.isdir('./Logs')):
        print("Folder exists")
        logFilename = './Logs/BTCUSDTLog' + timeStampStr +'.txt'
    else:
        print("Folder doesn't exist, creating...")
        os.mkdir('./Logs')
        logFilename = './Logs/BTCUSDTLog' + timeStampStr +'.txt'

    return logFilename

def write_to_file(newTradeData):
    global logFilename
    # print("Writing to file" + logFilename)
    tradeLog = open(logFilename, 'a')
    tradeLog.write(newTradeData)
    tradeLog.close()

def print_message(msg):
    # calculate total bitcoins exchanged
    bitcoins_exchanged = float(msg['p']) * float(msg['q']) 
    
    # change datetime
    timestamp = msg['T']/1000
    timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    # check buy/sell
    if msg['m'] == True:
        event_side = 'SELL'
    else:  
        event_side = 'BUY '
       
    #dataAsString = "Time: {} Symbol: {} Price: {} Quantity: {} \n". format(msg['T'], msg['s'], msg['p'], msg['q'])
    dataAsString = "{} - {} - {} - {} - Price: {} - Qty: {} BTC Qty: {}\n". format(timestamp, event_side, msg['t'], msg['s'], float((msg['p'])[0:7]), msg['q'], bitcoins_exchanged)
    print(dataAsString)
    

# This is our callback function. For now, it just prints messages as they come.
def handle_message(msg):
    # If the message is an error, print the error
    if msg['e'] == 'error':
        print(msg['m'])

    # If the message is  a trade: print time, symbol, price and quantity
    else:
        rawMessage = "{} {} {} {} {} {} {} {}\n". format(msg['E'], msg['T'], msg['t'], msg['a'], msg['b'], ((msg['p'])[0:7]), msg['q'], msg['m'])
        
        write_to_file(rawMessage)
        print_message(msg)
    
def end_program():
    global conn_key
    print("ending retrieval:")
    # stop the socket manager
    reactor.stop()
    bm.stop_socket(conn_key)
    bm.close()
    print("stopped program")
    sys.exit("Quitting now...")

def run_logger():
    global logFilename, conn_key

    # Start the socket manager
    bm.start()

    # Start trade socket with 'ETHBTC' and use handle_message to... handle the message.
    conn_key = bm.start_trade_socket(handle_message, 'BTCUSDT')
                
    print("starting retrieval:")

    bm.join()


if __name__ == "__main__":
    logFilename
    logFilename = create_file()
    startMessage = "Event Time / Trade Time / Trade ID / Seller Order ID / Buyer Order ID / Price / Quantity / Buyer=MarketMaker?\n"
    
    write_to_file(startMessage)

    bm = ThreadedWebsocketManager(PUBLIC, SECRET)        

    run_logger()
