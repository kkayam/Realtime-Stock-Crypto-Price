import sys, math,json, os.path, hashlib, time
import requests
from functools import reduce

from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QDesktopWidget, QFrame, QSizePolicy
from PyQt5.QtGui import QColor, QMovie
import websocket
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout)

class QHSeperationLine(QFrame):
  '''
  a horizontal seperation line\n
  '''
  def __init__(self):
    super().__init__()
    self.setMinimumWidth(1)
    self.setFixedHeight(20)
    self.setFrameShape(QFrame.HLine)
    self.setFrameShadow(QFrame.Sunken)
    self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    return

class Stock():
    def __init__(self,i,price="-"):
        i = i.split(":")
        self.ticker = ":".join(i[:2])
        self.name = i[1]
        self.position_exists = False
        if (len(i)>2):
            self.position_exists = True
            positions = i[2].split(",")
            self.position = [0,0]
            for x in positions:
                a = x.split("@")
                self.position[0] += float(a[0])
                self.position[1] += float(a[1])*float(a[0])
            self.position[1] = self.position[1]/self.position[0]


        self.label = None
        # self.url = ""
        # if (self.ticker.split(":")[0]=="BINANCE"):
        #     self.url = "https://www.binance.com/en/trade/"+self.name
        # else:
        #     self.url = "https://finance.yahoo.com/quote/"+self.name

        self.tabs = "\t"*(3-math.ceil(len(self.name)/6))
        self.price = price
        self.profit = None
        self.total = 0
        # self.toString = "<a href='"+self.url+"'>"+self.name+"</a>"+self.tabs
        self.toString = self.name+self.tabs+self.price
    def update_label(self):
        self.label.setText(self.toString)
        if (self.position_exists):
            try:
                self.total = self.position[0]*float(self.price)
            except:
                pass
            self.label.setToolTip("@".join([str(x) for x in self.position])+" tot: "+str(self.total)+" USD")
    def update_price(self, price):
        self.price = price
        self.toString = self.name+self.tabs+self.price
        if (self.position_exists and price!="-"):
            self.profit = (float(price)-self.position[1])*self.position[0]
            if (len(str(round(self.profit)))>3):
                self.toString = self.name+self.tabs+self.price+"\t"+str(round(self.profit))+" USD\t"+str(format(100*(float(self.price)-self.position[1])/self.position[1],".1f"))+"%"
            else:
                self.toString = self.name+self.tabs+self.price+"\t"+str(round(self.profit))+" USD\t\t"+str(format(100*(float(self.price)-self.position[1])/self.position[1],".1f"))+"%"
        self.update_label()

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    started = pyqtSignal()
    emitted_start = False
    
    def __init__(self, callback, tickers):
        super().__init__()
        self.callback = callback
        self.tickers = tickers

    def on_message(self, message):
        message = json.loads(message)
        # print(message)
        if "data" in message:
            for i in message["data"]:
                if i["s"] in self.tickers:
                    self.tickers[i["s"]].price = str(format(i["p"], '.6f'))
        if not self.emitted_start:
            self.started.emit()
            self.emitted_start = True
    def on_error(self,ws, err):
        print("error---------------------------------")
        self.finished.emit()

    def on_close(self):
        print("closed---------------------------------")
        self.finished.emit()

    def run(self):
        # yliveticker.YLiveTicker(on_ticker=self.callback, ticker_names=tickers)
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=c0jbko748v6vejlec51g",
                                on_message = self.on_message,
                                on_error = self.on_error,
                                on_close = self.on_close)
        ws.on_open = lambda ws : [ws.send('{"type":"subscribe","symbol":"'+ticker.ticker+'"}') for ticker in self.tickers.values()]
        ws.run_forever()

class cssden(QMainWindow):

    def __init__(self, tickers, bg, fontsize):
        super().__init__()

        # <MainWindow Properties>
        width = 360
        height = 5+(35*len(tickers))
        self.position_exists = any(x.position_exists for x in tickers)
        if (self.position_exists):
            width = 520
            height+=35
        
        vbox = QVBoxLayout()
        # vbox.setSpacing(10)

        # self.setFixedSize(width, height)
        self.setStyleSheet("QMainWindow{background-color: black;border: 1px solid black}")
        
        # Background
        if not bg.startswith("resources"):
            bg_name = "resources\\"+str(hash(bg))+".gif"
            if not (os.path.isfile(bg_name)):
                r = requests.get(bg, allow_redirects=True)
                open(bg_name,"wb").write(r.content)
        else:
            bg_name = bg

        self.movie = QMovie(bg_name)        

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.7)
        self.center()
        # </MainWindow Properties>

        # <Label Properties>
        self.tickers={}
        self.initial_investment = 0

        tickers = sorted(list(filter(lambda x: x.position_exists,tickers)),key=lambda x: x.position[0]*x.position[1], reverse=True)+list(filter(lambda x: (not x.position_exists),tickers))
        for i,ticker in enumerate(tickers):
            label = QLabel(self)
            label.setStyleSheet("QLabel{color: white; font: "+fontsize+"pt 'Segoe WP';}")
            label.setText(ticker.toString)
            if (ticker.position_exists):
                self.initial_investment += reduce(lambda x, y: x*y, ticker.position)
                label.setToolTip("@".join([str(x) for x in ticker.position])+" tot: "+str(reduce(lambda x, y: x*y, ticker.position))+" USD")
            vbox.addWidget(label)
            # label.setGeometry(5, 35*i, width, 40)
            ticker.label = label
            self.tickers[ticker.ticker]= ticker

        if (self.position_exists):
            seperator_horizontal = QHSeperationLine()
            vbox.addWidget(seperator_horizontal)
            
            self.profit_label = QLabel(self)
            self.profit_label.setStyleSheet("QLabel{color: white; font: "+fontsize+"pt 'Segoe WP';}")
            self.profit_label.setText("Profit"+"\t\t0"+"\t"*(2-math.ceil(len("Profit")/6))+"\t0")
            vbox.addWidget(self.profit_label)
            # self.profit_label.setGeometry(5, 35*len(tickers), width, 40)

        widget = QWidget()
        self.background = QLabel(self)
        self.background.setGeometry(0,0,widget.width(),widget.height())
        self.background.setMovie(self.movie)
        self.movie.setScaledSize(QSize(widget.width(),widget.height()))
        self.movie.start()
        widget.setLayout(vbox)
        widget.resizeEvent = lambda x: self.background.setGeometry(0,0,widget.width(),widget.height())
        self.setCentralWidget(widget)
        # </Label Properties>
        self.start_listener()
    
        self.oldPos = self.pos()
        self.show()
    
    def start_updateTimer(self):
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(500)
        self.updateTimer.timeout.connect(self.update)
        self.updateTimer.start()

    def calc_profit(self):
        return str(format(sum(ticker.profit for ticker in list(filter(lambda x: isinstance(x.profit, float),self.tickers.values()))), '.1f'))
    # Listens for updates from tickers
    def start_listener(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(self.update_label,self.tickers)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        
        self.worker.started.connect(self.start_updateTimer)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.start_listener)
        # Step 6: Start the thread
        self.thread.start()

    def update_label(self,ticker,price):
        self.tickers[ticker].update_price(price)
        if (self.position_exists):
            total = 0
            for value in self.tickers.values():
                total += value.total
            growth = format(total/self.initial_investment*100-100,".1f")
            total = format(total,".1f")
            self.profit_label.setText("Profit"+"\t\t"+str(total)+" USD"+"\t"*(2-math.ceil(len("Profit")/6))+self.calc_profit()+" USD"+"\t"+growth+"%")
    
    def update(self):
        self.tickers=self.worker.tickers
        for ticker in self.tickers:
            self.update_label(ticker, self.tickers[ticker].price)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def wheelEvent(self, event):
        opacity = max(self.windowOpacity()+(event.angleDelta().y() / 1020),0.015)
        self.setWindowOpacity(opacity)


if __name__ == '__main__':
    sys._excepthook = sys.excepthook 
    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback) 
        sys.exit(1) 
    sys.excepthook = exception_hook 
    txt = open("config.txt")
    bg = txt.readline().split("=")[-1].strip()
    fontsize = txt.readline().split("=")[-1].strip()
    tickers = [Stock(i.strip()) for i in txt.readlines()]
    app = QApplication(sys.argv)
    ex = cssden(tickers,bg,fontsize)

    sys.exit(app.exec_())