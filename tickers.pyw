import sys, math,json, os.path, hashlib
import requests
from functools import reduce

from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, QSize
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
            self.position = [float(x) for x in i[2].split("@")]
        self.label = None
        # self.url = ""
        # if (self.ticker.split(":")[0]=="BINANCE"):
        #     self.url = "https://www.binance.com/en/trade/"+self.name
        # else:
        #     self.url = "https://finance.yahoo.com/quote/"+self.name

        self.tabs = "\t"*(3-math.ceil(len(self.name)/6))
        self.price = price
        self.profit = None
        # self.toString = "<a href='"+self.url+"'>"+self.name+"</a>"+self.tabs
        self.toString = self.name+self.tabs+self.price
    def update_label(self):
        self.label.setText(self.toString)
        if (self.position_exists):
            self.label.setToolTip("@".join([str(x) for x in self.position])+" tot: "+str(self.position[0]*float(self.price))+" USD")
    def update_price(self, price):
        self.price = price
        self.toString = self.name+self.tabs+self.price
        if (self.position_exists):
            self.profit = (float(price)-self.position[1])*self.position[0]
            self.toString = self.name+self.tabs+self.price+"\t"+str(round(self.profit))+" USD"
        self.update_label()

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    
    def __init__(self, callback, tickers):
        super().__init__()
        self.callback = callback
        self.tickers = tickers

    def on_message(self, message):
        try:
            message = json.loads(message)
            # print(message)
            self.callback(message["data"][-1]["s"],str(format(message["data"][-1]["p"], '.6f')))
        except:
            pass

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
        ws.on_open = lambda ws : [ws.send('{"type":"subscribe","symbol":"'+ticker.ticker+'"}') for ticker in self.tickers]
        ws.run_forever()

class cssden(QMainWindow):

    def __init__(self, tickers, bg):
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
        
        if self.position_exists: tickers.sort(key=lambda x: x.position[0]*x.position[1], reverse=True)
        for i,ticker in enumerate(tickers):
            label = QLabel(self)
            label.setStyleSheet("QLabel{color: white; font: 18pt 'Segoe WP';}")
            label.setText(ticker.toString)
            label.setToolTip("@".join([str(x) for x in ticker.position])+" tot: "+str(reduce(lambda x, y: x*y, ticker.position))+" USD")
            vbox.addWidget(label)
            # label.setGeometry(5, 35*i, width, 40)
            ticker.label = label
            self.tickers[ticker.ticker]= ticker

        if (self.position_exists):
            seperator_horizontal = QHSeperationLine()
            vbox.addWidget(seperator_horizontal)
            
            self.profit_label = QLabel(self)
            self.profit_label.setStyleSheet("QLabel{color: white; font: 18pt 'Segoe WP';}")
            self.profit_label.setText("Profit"+"\t"*(4-math.ceil(len("Profit")/6))+"\t0")
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
    def calc_profit(self):
        return str(format(sum(ticker.profit for ticker in list(filter(lambda x: isinstance(x.profit, float),self.tickers.values()))), '.1f'))
    # Listens for updates from tickers
    def start_listener(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(self.update_label,self.tickers.values())
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.start_listener)
        # Step 6: Start the thread
        self.thread.start()

    def update_label(self,ticker,price):
        self.tickers[ticker].update_price(price)
        if (self.position_exists):
            self.profit_label.setText("Profit"+"\t"*(5-math.ceil(len("Profit")/6))+self.calc_profit()+" USD")
        
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
    txt = open("config.txt")
    bg = txt.readline().split("=")[-1].strip()
    tickers = [Stock(i.strip()) for i in txt.readlines()]
    app = QApplication(sys.argv)
    ex = cssden(tickers,bg)

    sys.exit(app.exec_())