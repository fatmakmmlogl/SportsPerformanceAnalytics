"""
VideoProcessor: Webcam veya video dosyasından frame okuma işlemlerini yöneten yardımcı sınıf.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Generator


class VideoProcessor:
    """
    OpenCV üzerinden webcam veya video dosyası akışını yöneten sınıf.
    
    Attributes:
        source: Kaynak (0 = varsayılan webcam, dosya yolu = video)
        cap: OpenCV VideoCapture nesnesi
        fps: Saniyedeki kare sayısı
        width, height: Frame boyutları
    """

    def __init__(self, source: int | str = 0, width: int = 640, height: int = 480):
        """
        Args:
            source: Kamera indeksi (0, 1, ...) veya video dosya yolu
            width: İstenilen frame genişliği
            height: İstenilen frame yüksekliği
        """
        self.source = source
        self._width  = width
        self._height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.fps:    float = 30.0
        self.width:  int   = width
        self.height: int   = height

    def open(self) -> bool:
        """
        Kaynağı açar.
        
        Returns:
            bool: Başarıyla açıldıysa True
        """
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            return False

        # Çözünürlük ayarla
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

        # Gerçek değerleri oku
        self.width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps    = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Bir sonraki frame'i okur.
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (başarı durumu, frame)
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
        ret, frame = self.cap.read()
        return ret, frame

    def frame_generator(self) -> Generator[np.ndarray, None, None]:
        """
        Frame üreteci (generator). Kaynak bitene kadar frame üretir.
        
        Yields:
            np.ndarray: Okunan frame
        """
        if self.cap is None:
            self.open()

        while True:
            ret, frame = self.read_frame()
            if not ret or frame is None:
                break
            yield frame

    def get_total_frames(self) -> int:
        """Video dosyaları için toplam kare sayısını döndürür."""
        if self.cap is None:
            return 0
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_current_position(self) -> int:
        """Mevcut kare konumunu döndürür."""
        if self.cap is None:
            return 0
        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def is_opened(self) -> bool:
        """Kaynağın açık olup olmadığını kontrol eder."""
        return self.cap is not None and self.cap.isOpened()

    def release(self):
        """VideoCapture nesnesini serbest bırakır."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
