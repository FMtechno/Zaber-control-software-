#python standard libraries
from time import sleep
import sys as sys
import asyncio #asynchronous programming library -> to run multiple tasks at the same time (move things and update position readings)
# import socket #network library to communicate with the raspberry pi
#qt GUI libraries
from PyQt5.QtWidgets import (QApplication,QWidget,QListWidget,QListWidgetItem,QDockWidget,QLabel,QHBoxLayout,QMainWindow,QTextEdit,QLineEdit,QPushButton,QGridLayout,QDesktopWidget,QRadioButton,QMessageBox)
from PyQt5.QtGui import QFont,QRegExpValidator
from PyQt5.QtCore import QRegExp,Qt,QThread,pyqtSignal,QObject
#zaber API libraries
from zaber_motion import Library, Units
from zaber_motion.binary import Connection, CommandCode

Library.enable_device_db_store()

class ZaberControlUI(QMainWindow):
    def __init__(self,connection):
        super().__init__()
        self.connection = connection
        self.rotstage = connection.detect_devices()[6]
        angle = self.rotstage.get_position(Units.ANGLE_DEGREES)

        self.rotDockState = 1
        self.transDockState = 0
        self.cameraDockState = 0

        self.initUI(angle)

    def initUI(self,angle):
        self.setObjectName("main")

        layout = QHBoxLayout()

        self.statusBMain = self.statusBar()
        self.statusBMain.setObjectName("statusMain")
        self.statusBMain.showMessage("Device idle")

        self.Mbar = self.menuBar()
        self.Mbar.setObjectName("mainMenu")
        file = self.Mbar.addMenu('File')
        file.addAction('New')
        file.addAction('Save')
        file.addAction('quit')

        self.selectionDock = QListWidget()
        item_text_list = ["rotation","translation","camera"]
        for item_text in item_text_list:
            item = QListWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignCenter)
            self.selectionDock.addItem(item)

        self.tab1 = QDockWidget('Dock rotation',self)
        self.tab1.setFloating(False)
        self.tab1.setObjectName("tabrot")
        self.tab1.setFixedWidth(430)
        self.setCentralWidget(self.selectionDock)
        self.addDockWidget(Qt.RightDockWidgetArea,self.tab1)
        # self.setLayout(layout)
        self.tab1UI2(angle)
        # self.tab2UI()
        # self.tab3UI()


        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.setFixedSize(600,450)
        self.setWindowTitle("Zaber control")
        self.show()

    #part of the ui controlling the motor for the rotation
    def tab1UI2(self,angle):
        self.tab1.stateBTN = 1
        self.tab1.rotFlag = 1

        def btnstate(button):
            if button.isChecked == True:
                self.tab1.stateBTN = 1
            else:
                self.tab1.stateBTN = 0

        def setVelocity():
            qlinetext = float(self.dockwidget1.AngleVelocityAction.text())
            self.dockwidget1.angleVelocity = qlinetext

        def updateAngle():
            self.dockwidget1.label_ActualAngle.setText("Angle: {0:.4f}".format(self.rotstage.get_position(Units.ANGLE_DEGREES)))

        def updateAngle2(text):
            self.dockwidget1.label_ActualAngle.setText("Angle: {0:.4f}".format(text))

        #The motion of the motor is done in a separate thread, in order to not freeze the gui during the motion
        #it also allows to run the event loop of asyncio separetely from the main event loop of Qt
        def startRotThread():
            def update_finished():
                self.dockwidget1.btnRot.setEnabled(True)
                self.dockwidget1.btnAngVel.setEnabled(True)
                self.statusBMain.showMessage("device idle")

            doitornot = QMessageBox.question(self,"message","Are you sure?",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            if doitornot == QMessageBox.Yes:
                qlinetext = float(self.dockwidget1.AngleAction.text())
                self.statusBMain.showMessage("device moving")
                self.thread = QThread()
                self.worker = Worker(self.rotstage,self.tab1.stateBTN,qlinetext,self.dockwidget1.angleVelocity)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.worker.progress.connect(updateAngle2)
                self.thread.start()

                self.dockwidget1.btnRot.setEnabled(False)
                self.dockwidget1.btnAngVel.setEnabled(False)

                self.thread.finished.connect(lambda:update_finished())
                self.thread.finished.connect(lambda:updateAngle())
            else:
                self.statusBMain.showMessage("Move canceled")
                sleep(1)
                self.statusBMain.showMessage("device idle")

        def stopMove():
            self.rotstage.stop()

        #seriously man, go home
        def goHome():
            self.statusBMain.showMessage("device moving")
            self.rotstage.home()
            updateAngle()
            self.statusBMain.showMessage("device idle")

        self.dockwidget1 = QWidget()
        self.dockwidget1.setObjectName("dockRotWidget")

        self.dockwidget1.setObjectName("tab1")
        self.dockwidget1.angleVelocity = 1

        grid = QGridLayout(self.dockwidget1)
        position = [(i,j) for i in range(5) for j in range(3)]
        grid.setSpacing(25)

        label_rot = QLabel('Set angle :')
        label_rot.setFixedWidth(100)
        grid.addWidget(label_rot,*position[0])

        self.dockwidget1.AngleAction = QLineEdit()
        # self.dockwidget1.AngleAction.returnPressed.connect(changeAngle)
        self.dockwidget1.AngleAction.setObjectName("rot")
        self.dockwidget1.AngleAction.setFixedWidth(150)
        self.dockwidget1.AngleAction.setValidator(QRegExpValidator(QRegExp("^[+ -]?[0-9]{1,2}([.][0-9]{,3})?$"),self.dockwidget1.AngleAction))
        grid.addWidget(self.dockwidget1.AngleAction,*position[1])
        # self.dockWidget1.angleAction.setPlaceholderText("Angle (deg)")

        label_setvitesse = QLabel("Set velocity :")
        label_setvitesse.setFixedWidth(130)
        grid.addWidget(label_setvitesse,*position[3])

        self.dockwidget1.AngleVelocityAction = QLineEdit()
        # self.dockwidget1.AngleVelocityAction.returnPressed.connect(setVelocity)
        self.dockwidget1.AngleVelocityAction.setObjectName("rot")
        self.dockwidget1.AngleVelocityAction.setFixedWidth(150)
        self.dockwidget1.AngleVelocityAction.setValidator(QRegExpValidator(QRegExp("^[+ -]?[0-9]{,1}([.][0-9]{,3})?$"),self.dockwidget1.AngleVelocityAction))
        grid.addWidget(self.dockwidget1.AngleVelocityAction,*position[4])

        self.dockwidget1.btnRot = QPushButton("Go")
        self.dockwidget1.btnRot.setObjectName("btnRot")
        grid.addWidget(self.dockwidget1.btnRot,*position[2])
        self.dockwidget1.btnRot.setFixedWidth(40)
        self.dockwidget1.btnRot.clicked.connect(startRotThread)
        self.dockwidget1.btnAngVel = QPushButton("set")
        self.dockwidget1.btnAngVel.setObjectName("btnAngVel")
        self.dockwidget1.btnAngVel.setFixedWidth(40)
        grid.addWidget(self.dockwidget1.btnAngVel,*position[5])
        self.dockwidget1.btnAngVel.clicked.connect(setVelocity)

        self.dockwidget1.label_ActualAngle = QLabel("Angle: {0:.4f}".format(angle))
        self.dockwidget1.label_ActualAngle.setObjectName("angleReading")
        self.dockwidget1.label_ActualAngle.setAlignment(Qt.AlignCenter)
        self.dockwidget1.label_ActualAngle.setFixedWidth(140)
        self.dockwidget1.label_ActualAngle.setFixedHeight(70)
        grid.addWidget(self.dockwidget1.label_ActualAngle,*position[7])

        labelTypeRot = QLabel("Type of\n motion:")
        labelTypeRot.setAlignment(Qt.AlignRight)
        grid.addWidget(labelTypeRot,*position[9])

        widgetRbRot = QWidget()
        widgetRbRot.setObjectName("RadioButtonRot")
        widgetRbRot.setFixedHeight(70)
        # fontRBROT = QFont("Consolas",17)
        # fontRBROT.setBold(True)
        # widgetRbRot.setFont(fontRBROT)
        layoutRbRot = QHBoxLayout()
        self.rb1 = QRadioButton("Relative",self)
        self.rb1.setObjectName("leftButton")
        self.rb1.setChecked(True)
        self.rb1.toggled.connect(lambda:btnstate(self.rb1))
        # grid.addWidget(self.rb1,*position[10])
        layoutRbRot.addWidget(self.rb1)
        self.rb2 = QRadioButton("Absolute",self)
        # grid.addWidget(self.rb2,*position[11])
        layoutRbRot.addWidget(self.rb2)
        widgetRbRot.setLayout(layoutRbRot)
        grid.addWidget(widgetRbRot,3,1,1,2)

        btn_stop = QPushButton("Stop")
        btn_stop.clicked.connect(stopMove)
        btn_stop.setObjectName("stop")
        btn_stop.setFixedWidth(100)
        grid.addWidget(btn_stop,*position[13])

        btn_home = QPushButton("Home")
        btn_home.clicked.connect(goHome)
        btn_home.setObjectName("home")
        btn_home.setFixedWidth(100)
        grid.addWidget(btn_home,*position[14])

        self.dockwidget1.setLayout(grid)
        self.tab1.setWidget(self.dockwidget1)

    def tab2UI(self):
        return 0

    def tab3UI(self):
        return 0

#worker class that allows to read angle while doing the rotation of the stage -> parallelisation
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(float)
    # go = pyqtSignal()

    def __init__(self,rotStage,stateBTN,targetAngle,velocity):
        super().__init__()
        self.rotStageAsync = rotStage
        self.BTNstate = stateBTN
        self.targetAngle = targetAngle
        self.angVel = velocity

    def run(self):
        async def rotationAsyncAbs():
            await self.rotStageAsync.move_absolute_async(self.targetAngle,Units.ANGLE_DEGREES)

        async def rotationAsyncRel():
            await self.rotStageAsync.move_relative_async(self.targetAngle,Units.ANGLE_DEGREES)

        async def returnPosition():
            return self.rotStageAsync.get_position(Units.ANGLE_DEGREES)

        async def updateAngleAsync(extTask):
            while True:
                if extTask.done():
                    break
                task = asyncio.create_task(returnPosition())
                await task
                self.progress.emit(task.result())
                #refresh every 0.02sec
                await asyncio.sleep(0.02)

        async def mainRel():
            task1 = asyncio.create_task(rotationAsyncRel())
            task2 = asyncio.create_task(updateAngleAsync(task1))
            await task1
            await task2

        async def mainAbs():
            task1 = asyncio.create_task(rotationAsyncAbs())
            task2 = asyncio.create_task(updateAngleAsync(task1))
            await task1
            await task2

        self.rotStageAsync.generic_command_with_units(CommandCode.SET_TARGET_SPEED,self.angVel,Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND)
        if self.BTNstate == 1:
            asyncio.run(mainRel())
        elif self.BTNstate == 0:
            asyncio.run(mainAbs())
        else:
            print("there is a problem with the radio button program, you need to fix it!!!!")
        self.finished.emit()

#starting the pyqt app and the opening the connection with the motors
def main():
    with Connection.open_serial_port("COM5") as connection:
        with open("style.css") as f:
            app = QApplication(sys.argv)
            appFont = QFont("Consolas",17,QFont.Light)
            app.setFont(appFont)
            app.setStyleSheet(f.read())
        Zaber = ZaberControlUI(connection)
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
