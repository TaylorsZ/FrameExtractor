import configparser
import os
import sys
import time
from typing import Optional

import cv2
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from loguru import logger

from ExtractorThread import ExtractorThread
from start import Ui_MainWindow

config_file_name = "config.ini"
config_section_name = "Video"

class MyMainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        # 创建 ConfigParser 实例
        self.config = configparser.ConfigParser()
        # 初始化保存间隔为5秒
        self.save_interval:int = 5
        self.extractor_thread:Optional[ExtractorThread] = None
        self.update_ui()
        self.spinBox.valueChanged.connect(self.spinbox_changed)
        # logger.info("\033[3mHello, world!\033[0m")
        # logger.debug("\033[1m\033[42mHello, world!\033[0m")
        # time.sleep(1)
        # QMessageBox.about(self, "提示", "欢迎使用视频抽帧工具，本工具仅供学习交流使用，请勿用于商业用途。")
    def spinbox_changed(self, value):
        self.save_interval = value
        self.config.set(config_section_name, 'saveInterval', str(value))
        with open(config_file_name, 'w') as configfile:
            self.config.write(configfile)
            logger.info("配置已更新")
    def update_ui(self):
        self.config.read(config_file_name)
        if self.config.has_section(config_section_name):
            logger.info("读取项目配置")
            self.exportDir = self.config.get(config_section_name, 'exportDir')
            if self.exportDir == '':
                self.exportDir = os.path.join(os.path.expanduser("~"), "Desktop")
                self.config.set(config_section_name, 'exportDir', self.exportDir)
                with open(config_file_name, 'w') as configfile:
                    self.config.write(configfile)
                    logger.info("配置已更新")
            self.save_interval = self.config.getint(config_section_name, 'saveInterval')
        else:
            logger.info("无项目配置")
        self.exportLE.setText(self.exportDir)
        self.spinBox.setValue(self.save_interval)
    def selectVideoFiles(self):
        files = QFileDialog.getOpenFileNames(self, '选择视频文件', '', '视频文件 (*.flv *.mp4 *.avi *.mkv)')
        logger.info(files)
        if files[0]:
            self.lineEdit.setText(files[0][0])
    def selectSaveDir(self):
        folder_path = QFileDialog.getExistingDirectory(None, "选择文件夹", "")
        if folder_path:  # 用户选择了文件夹
            print("选中的文件夹路径:", folder_path)
            self.config.set(config_section_name, 'exportDir', folder_path)
            with open(config_file_name, 'w') as configfile:
                self.config.write(configfile)
                logger.info("配置已更新")
            self.update_ui()
    def startExtractor(self):
        if self.startBT.isChecked():
            self.startBT.setText('停止抽帧')
            video_path = self.lineEdit.text()
            logger.info(f'开始解析:{video_path}')
            if not video_path:
                self.show_info_message('请选择视频文件')
                self.reset()
                return
            if not self.exportLE.text():
                self.show_info_message('请选择保存目录')
                self.reset()
                return
            self.extractor_thread = ExtractorThread(video_path, self.exportLE.text(), self.spinBox.value())
            self.extractor_thread.trigger.connect(self.update_export_result)
            self.extractor_thread.progress_signal.connect(self.update_progress)
            self.extractor_thread.start()
            self.spinBox.setEnabled(False)
            self.exportLE.setEnabled(False)
            self.lineEdit.setEnabled(False)
            self.openBT.setEnabled(False)
            self.exportBT.setEnabled(False)
        else:
            self.startBT.setText('开始抽帧')
            if self.extractor_thread:
                self.extractor_thread.stop_extractor()
    def update_export_result(self, is_success, message, file_path):
        self.reset()
        if is_success:
            self.show_alert(title='文件操作',message= message,ok_title="打开文件所在位置",ok_callback= lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(file_path)))
        else:
            self.show_info_message(message)
    def reset(self):
        if self.extractor_thread:
            self.extractor_thread.stop_extractor()
        self.extractor_thread = None
        self.progressL.setText('解析进度')
        self.progressBar.setValue(0)
        self.startBT.setChecked(False)
        self.startBT.setText('开始抽帧')
        self.spinBox.setEnabled(True)
        self.exportLE.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.openBT.setEnabled(True)
        self.exportBT.setEnabled(True)

    def update_progress(self, progress, message):
        self.progressBar.setValue(progress)
        self.progressBar.setFormat(f'{progress}%')
        self.progressL.setText(f'解析进度:[{message}]')
        # logger.info(f'解析进度:{progress}%')
    def show_alert(self, title,message,ok_title:str = "好的",ok_callback = None):
        # 创建消息框
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Question)
        # 添加按钮
        open_button = msg_box.addButton(ok_title, QMessageBox.AcceptRole)
        msg_box.addButton("取消", QMessageBox.RejectRole)
        # 显示对话框并等待用户选择
        msg_box.exec_()

        # 检测用户的选择
        if msg_box.clickedButton() == open_button and ok_callback:
            ok_callback()
    def show_info_message(self, message):
        QMessageBox.information(None, "提示", message, QMessageBox.Ok)

if __name__ == '__main__':

    # log_date = time.strftime('%Y_%m_%d', time.localtime())
    # log_file_name = time.strftime('%H_%M_%S', time.localtime())
    # logger.add(f'log/{log_date}/{log_file_name}.log')
    # 让 Nuitka 知道 OpenCV 的库在哪里
    # cv2_path = os.path.dirname(cv2.__file__)
    # sys.path.append(cv2_path)

    # print("CV2 Path:", cv2_path)  # 确保 Nuitka 可以找到 OpenCV

    # 强制 OpenCV 预加载核心模块
    # cv2.ocl.setUseOpenCL(False)

    app = QApplication(sys.argv)
    ui = MyMainForm()
    ui.show()
    sys.exit(app.exec_())