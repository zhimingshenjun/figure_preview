import sys
from PyQt5 import QtCore, QtGui, QtWidgets                          # Qt5三大模块 为了方便同学看清楚模块来源 使用完整导入的写法
import pyqtgraph as pg                                              # 一个基于Qt实现的python第三方绘图库 用于绘制立绘身后的力场
import numpy as np                                                  # 一个经典老牌的python科学计算库
import pyaudio                                                      # python音频库 可以进行录音 播放等功能 用于读取话筒音量
import audioop                                                      # 一个高性能的音频计算库
pg.setConfigOptions(antialias=True, background='#00000000')         # pyqtgraph设置抗锯齿+背景透明


class DetectSound(QtCore.QThread):                                  # 创建QThread类来实时获取麦克风说话音量
    volume = QtCore.pyqtSignal(list)                                # 初始化pyqtSignal类属性 发射类型为list

    def __init__(self):                                             # 构造函数
        super(DetectSound, self).__init__()                         # 继承QThread

    def run(self):                                                  # QThread内建的run函数 所有耗时长的操作都写在这里面 防止卡死界面
        p = pyaudio.PyAudio()                                       # 初始化PyAudio实例
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True)  # 打开音频流对象 读取话筒输入缓冲区
        volume = []                                                 # 用于存放响度值的列表
        while 1:                                                    # 无限循环读取话筒音频流 必须在run()里面实现 否则UI界面会卡死
            data = stream.read(3)                                   # 每次读取3个采样点
            volume.append(audioop.rms(data, 2) ** 0.8 / 4000 + 1)   # 使用audioop.rms计算音量响度 然后通过开方和除法缩小数值
            if len(volume) == 180:                                  # 当列表长度到达180个时
                self.volume.emit(volume)                            # 用pyqtSignal将响度列表发射给主窗口线程
                volume = []                                         # 清空列表 重新采样


class HairLabel(QtWidgets.QLabel):                                  # 用于显示假发的QLabel类
    def __init__(self, w, h, parent):                               # w, h参数接受宽高 parent接受的是主窗口对象
        super(HairLabel, self).__init__(parent)                     # 将主窗口传给parent后 通过super()将假发部件嵌入主窗口界面
        pixmap = QtGui.QPixmap('figure/假发.png')                    # 加载本地假发png文件
        pixmap = pixmap.scaled(w, h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)  # 抗锯齿缩放至指定大小
        self.setPixmap(pixmap)                                      # 用setPixmap将假发展示到QLabel上

    def mousePressEvent(self, QEvent):                              # 响应鼠标点击
        self.start_pos = QEvent.pos()                               # 记录第一下鼠标点击的坐标

    def mouseMoveEvent(self, QEvent):                               # 响应鼠标移动
        self.move(self.pos() + QEvent.pos() - self.start_pos)       # 移动至当前坐标加上鼠标移动偏移量


class MainWindow(QtWidgets.QWidget):                                # 主窗口 继承自QWidgets
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 720)                                       # 将窗口大小缩放成800x720分辨率
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)       # 设置主窗口背景透明
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)           # 设置主窗口无边框
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)          # 设置主窗口置顶显示

        self.graph = pg.PlotWidget(self)                            # 在主窗口创建一个pyqtgraph画布
        self.graph.setStyleSheet('background-color:#00000000')      # 画布背景透明
        self.graph.setGeometry(0, 0, 800, 720)                      # 将画布移动至坐标(0, 0) 设置宽高为(800, 720)
        plotItem = self.graph.getPlotItem()                         # 获取画布里的plotItem对象
        plotItem.hideAxis('left')                                   # 隐藏左侧y轴
        plotItem.hideAxis('bottom')                                 # 隐藏底部x轴
        self.theta = np.linspace(0, np.pi, 180)                     # 用numpy生成一个从0到π 180等分的等差数列
        x = np.cos(self.theta)                                      # 按等差数列计算对应的x值 既半圆曲线的x轴数组
        y = np.sin(self.theta)                                      # 按等差数列计算对应的y值 既半圆曲线的y轴数组
        color = '#B3DCFD'                                           # 选择一个好看的颜色用来画曲线 这里我选了天蓝色
        self.line = self.graph.plot(x, y,                           # 绘制半圆曲线
            pen=pg.mkPen(color + '80', width=5),                    # 将画笔设为天蓝色 透明度80/FF 粗细=5 样式=实线
            fillLevel=0, brush=color + '20')                        # 填充曲线和直线y=0之间的区域 笔刷设为天蓝色 透明度20/FF
        self.dotLine = self.graph.plot(x, y,                        # 再绘制一个新的半圆曲线
            pen=pg.mkPen(color, width=1.5, style=QtCore.Qt.DotLine))  # 画笔天蓝色 粗细=1.5 样式=点虚线

        self.detectSound = DetectSound()                            # 实例化DetectSound(QThread对象) 来检测话筒音量
        self.detectSound.volume.connect(self.setWave)               # 接收DetectSound传回来的信号并连接到self.setWave函数
        self.detectSound.start()                                    # 调用start执行DetectSound.run()里面的代码

        figLabel = QtWidgets.QLabel(self)                           # 创建一个QLabel用于展示立绘图
        pixmap = QtGui.QPixmap(r'figure/光头.png')                   # 用QPixmap加载本地png图片
        pixmap = pixmap.scaled(800, 720, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)  # 抗锯齿缩放至800x720
        figLabel.setPixmap(pixmap)                                  # 用setPixmap将立绘展示到QLabel上
        figLabel.setGeometry(0, 0, 800, 720)                        # 将QLabel覆盖到graph上面

        self.hairX, self.hairY = 261, 82                            # 假发初始坐标
        self.hairW, self.hairH = 280, 280                           # 假发宽高
        self.hairLabel = HairLabel(self.hairW, self.hairH, self)    # 实例化hairLabel 并将宽高和主窗口对象传给它 将它嵌入主窗口
        self.hairLabel.move(self.hairX, self.hairY)                 # 移动至指定坐标处

    def keyPressEvent(self, QEvent):                                # 响应键盘按下事件
        if QEvent.key() == QtCore.Qt.Key_Space:                     # 判断按下的键是否为空格键 是的话就创建动画让假发飞回来
            hairAnimation = QtCore.QPropertyAnimation(self.hairLabel, b'geometry', self)  # 给hairLabel创建一个动画 类型为geometry
            hairAnimation.setDuration(1000)                         # 设置动画持续时长为1000毫秒
            hairAnimation.setEndValue(QtCore.QRect(self.hairX, self.hairY, self.hairW, self.hairH))  # 动画结束位置为假发初始位置
            hairAnimation.setEasingCurve(QtCore.QEasingCurve.OutElastic)  # 设置动画插值类型为“来回弹跳”
            hairAnimation.start()                                   # 开始动画效果

    def mousePressEvent(self, QEvent):                              # 响应鼠标点击
        self.start_pos = QEvent.pos()                               # 记录第一下鼠标点击的坐标

    def mouseMoveEvent(self, QEvent):                               # 响应鼠标移动
        self.move(self.pos() + QEvent.pos() - self.start_pos)       # 移动至当前坐标加上鼠标移动偏移量

    def setWave(self, volume):                                      # 接收DetectSound发射回来的长度为180的响度列表
        x = volume * np.cos(self.theta)                             # 将响度作为新半径来计算新的x值
        y = volume * np.sin(self.theta)                             # 将响度作为新半径来计算新的y值
        self.dotLine.setData(x, y)                                  # 刷新点虚线

    def contextMenuEvent(self, QEvent):                             # 响应鼠标右键菜单事件
        menu = QtWidgets.QMenu()                                    # 实例化一个QMenu对象
        exit = menu.addAction('退出')                                # 往QMenu添加一个文本为“退出”的action 存放在exit变量里
        action = menu.exec_(self.mapToGlobal(QEvent.pos()))         # 将QEvent.pos()映射为屏幕全局坐标 然后在此坐标弹出菜单
        if action == exit: self.close()                             # 判断用户点击哪个action 如果是exit就调用self.close()退出


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)                          # Qt主进程后台管理
    mainWindow = MainWindow()                                       # 实例化主窗口
    mainWindow.show()                                               # 显示主窗口
    sys.exit(app.exec_())                                           # 启动Qt主进程循环直到收到退出信号
