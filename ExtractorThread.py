from loguru import logger
import os
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger


class ExtractorThread(QThread):
    trigger = pyqtSignal(bool, str,str)  # 用于最终结果通知
    progress_signal = pyqtSignal(int,str)  # 新增进度信号，传递 int 类型的进度百分比

    def __init__(self, video_path, export_dir: str, save_interval: int):
        super().__init__()
        self.video_path = video_path
        self.export_dir = export_dir
        self.save_interval = save_interval
        self.saved_frame_count = 0
        self.frame_count = 0
        self.is_running = False
        self.cap = None

    def stop_extractor(self):
        self.is_running = False

    def run(self):
        self.is_running = True
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.trigger.emit(False, "无法打开视频文件","")
            return

        # 获取视频总帧数
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_export_frames = total_frames // self.save_interval
        if total_frames <= 0:
            self.trigger.emit(False, "视频帧数获取失败","")
            return

        # 获取视频文件名称(去除扩展名)
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        export_path = os.path.join(self.export_dir, video_name)
        os.makedirs(export_path, exist_ok=True)

        logger.info(f"保存路径：{export_path}")

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # 仅在每隔 save_interval 帧时保存图像
            if self.frame_count % self.save_interval == 0:
                save_path = os.path.join(export_path, f"{self.saved_frame_count:04d}.jpg")
                cv2.imwrite(save_path, frame)
                # logger.info(f"Saved {save_path}")
                self.saved_frame_count += 1
            # 计算进度并发送信号
            progress = int((self.frame_count / total_frames) * 100)
            self.progress_signal.emit(progress,f"{self.saved_frame_count+1}/{total_export_frames}")  # 发送进度信号
            self.frame_count += 1  # 递增帧数
        self.trigger.emit(True, f"抽帧完成，共计 {self.saved_frame_count} 张图片！",export_path)

        # 释放资源
        if self.cap:
            self.cap.release()
        self.cap = None
        self.frame_count = 0
        self.saved_frame_count = 0
        self.is_running = False

