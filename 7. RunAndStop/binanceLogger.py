        
import datetime
import queue
import logging
import signal
import time
import threading
import tkinter as tk
import os
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W

import sys
from twisted.internet import reactor
from binance.client import Client # Import the Binance Client
from binance import ThreadedWebsocketManager # Import the Binance Socket Manager
from datetime import datetime
from pynput import keyboard
from config import PUBLIC, SECRET


logger = logging.getLogger(__name__)

# Instantiate a Client
client = Client(api_key=PUBLIC, api_secret=SECRET)

# Instantiate a BinanceSocketManager, passing in the client that you instantiated
bm = ThreadedWebsocketManager(PUBLIC, SECRET)      

logFilename = ''

break_program = False

conn_key = ''


def create_file():
    global logFilename
    print("creating file: ")
    dateTimeObj = datetime.now()
    timeStampStr = dateTimeObj.strftime("%y%m%d_%H%M")
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    logFilename = './logs/BTCUSDTLog' + timeStampStr +'.txt'
    return logFilename

def write_to_file(newTradeData):
    global logFilename
    print("writing to file: ")
    tradeLog = open(logFilename, 'a')
    tradeLog.write(newTradeData)
    tradeLog.close()

def print_message(msg):
    global displayMessage
    # breakpoint()
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
    displayMessage = "{} - {} - {} - {} - Price: {} - Qty: {} Qty in USD: {}\n". format(timestamp, event_side, msg['t'], msg['s'], ((msg['p'])[0:7]), msg['q'], ((str(bitcoins_exchanged))[0:16]))
    # write_to_file(dataAsString)
    print(displayMessage)
    
    # breakpoint()

# This is our callback function. For now, it just prints messages as they come.
def handle_message(msg):
    global displayMessage
    print_message(msg)
    # If the message is an error, print the error
    if msg['e'] == 'error':
        print(msg['m'])
    elif msg['m'] == True:
        rawMessageT = "{} {} {} {} {} {} {} {}\n". format(msg['E'], msg['T'], msg['t'], msg['a'], msg['b'], ((msg['p'])[0:7]), msg['q'], msg['m'])
        print(rawMessageT)
        levelT = logging.CRITICAL
        logger.log(levelT,displayMessage)
        write_to_file(rawMessageT)
        # print_message(msg)
    # If the message is  a trade: print time, symbol, price and quantity
    else:
        rawMessageF = "{} {} {} {} {} {} {} {}\n". format(msg['E'], msg['T'], msg['t'], msg['a'], msg['b'], ((msg['p'])[0:7]), msg['q'], msg['m'])
        print(rawMessageF)
        levelF = logging.INFO
        logger.log(levelF, displayMessage)
        write_to_file(rawMessageF)
        # print_message(msg)
    # breakpoint()
    
def end_program():
    global conn_key
    print("ending retrieval:")
    # stop the socket manager
    reactor.stop()
    bm.stop_socket(conn_key)
    bm.close()
    print("stopped program")
    sys.exit("Quitting now...")



class BinanceRetriever(threading.Thread):
    """Class to display the time every seconds
    Every 5 seconds, the time is displayed using the logging.ERROR level
    to show that different colors are associated to the log levels
    """
    
    global logFilename

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        # global logFilename
        logger.debug('Binance started')
        logFilename = create_file()
        startMessage = "Event Time / Trade Time / Trade ID / Seller Order ID / Buyer Order ID / Price / Quantity / Buyer=MarketMaker?\n"
        write_to_file(startMessage)

        bm.start()
        conn_key = bm.start_trade_socket(handle_message, 'BTCUSDT')
        bm.join()
        
        # while not self._stop_event.is_set():
            
        #     # run_logger()
    def stop(self):
        self._stop_event.set()


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleBinace:
    def __init__(self,frame):
        self.frame = frame
        
        # ScrolledText Widget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=20)
        self.scrolled_text.grid(row=0,column=0,sticky=(N,S,W,E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='blue')
        
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)
        
        
class MenuButtons:
    def __init__(self,frame):
        self.frame = frame
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        self.quitButton = tk.Button(self, text='Quit', command=self.quit)
        self.quitButton.grid()
        

class App:

    def __init__(self, root):
        self.root = root
        root.title('Binance Retriever')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # Create the panes and frames
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)
        
        # binance frame
        binance_frame = ttk.Labelframe(horizontal_pane, text="Binance")
        binance_frame.columnconfigure(0, weight=1)
        binance_frame.rowconfigure(0, weight=1)
        horizontal_pane.add(binance_frame, weight=1)
        
        # add button layout at the bottom
        # form_frame = ttk.Labelframe(horizontal_pane, text="MyForm")
        # form_frame.columnconfigure(1, weight=1)
        # horizontal_pane.add(form_frame, weight=1)
        
        
        # Initialize all frames
        self.binanceConsole = ConsoleBinace(binance_frame)
        # self.buttonMenu = MenuButtons(form_frame)
        self.binance = BinanceRetriever()
        self.binance.start()
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        self.binance.stop()
        self.root.destroy()
        end_program()


def main():
    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == '__main__':
    main()
