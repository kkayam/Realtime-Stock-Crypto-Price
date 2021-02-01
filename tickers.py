import sys, math,json
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QDesktopWidget
from PyQt5.QtGui import QColor, QMovie
import websocket


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
            self.callback(message["data"][0]["s"].split(":")[-1], message["data"][0]["p"])
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
        ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=c0bha8748v6to0rp299g",
                                on_message = self.on_message,
                                on_error = self.on_error,
                                on_close = self.on_close)
        ws.on_open = lambda ws : [ws.send('{"type":"subscribe","symbol":"'+ticker+'"}') for ticker in self.tickers]
        ws.run_forever()

class cssden(QMainWindow):

    def __init__(self, tickers):
        super().__init__()

        # <MainWindow Properties>
        width = 350
        height = 5+(35*len(tickers))
        self.setFixedSize(width, height)
        self.setStyleSheet("QMainWindow{background-color: black;border: 1px solid black}")
        self.movie = QMovie("bg.gif")
        self.background = QLabel(self)
        self.background.setGeometry(0,0,width,height)
        self.background.setMovie(self.movie)
        self.movie.setScaledSize(QSize(width,height))
        self.movie.start()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.7)
        self.center()
        # </MainWindow Properties>

        # <Label Properties>
        self.tickers = tickers
        self.labels={}
        for i,ticker in enumerate(tickers):
            label = QLabel(self)
            label.setStyleSheet("QLabel{color: white; font: 18pt 'Segoe WP';}")
            label.setText(ticker.split(":")[-1]+"\t"*(3-math.ceil(len(ticker.split(":")[-1])/6))+"-")
            label.setGeometry(5, 35*i, width, 40)
            self.labels[ticker.split(":")[-1]]= label

        # </Label Properties>
        self.start_listener()

        self.oldPos = self.pos()
        self.show()

    
    def start_listener(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(self.update_label,self.tickers)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.start_listener)
        # Step 6: Start the thread
        self.thread.start()

    def update_label(self, ticker,price):
        self.labels[ticker].setText(ticker+"\t"*(3-math.ceil(len(ticker)/6))+str(format(price, '.6f')))
        
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
        opacity = max(self.windowOpacity()+(event.angleDelta().y() / 1020),0.05)
        self.setWindowOpacity(opacity)


if __name__ == '__main__':
    tickers = [i.strip() for i in open("tickers.txt").readlines()]
    app = QApplication(sys.argv)
    ex = cssden(tickers)

    sys.exit(app.exec_())