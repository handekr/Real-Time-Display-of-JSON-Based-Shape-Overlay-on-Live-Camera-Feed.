# -*- coding: utf-8 -*-
import gxipy as gx
import numpy as np
import cv2
import json

# --- Kamera & JSON Ayarları ---
CAMERA_SN = "FDC24100405"
json_file_path = "api_get_20250514_094755.json"  # Aynı klasördeki JSON dosyası

# --- Gerçek Ölçüler (şekil için) ---
real_width_cm = 107   # X eksenindeki gerçek uzunluk
real_height_cm = 30   # Y eksenindeki gerçek yükseklik

# --- Kamera Görüş Alanı Gerçek Boyutları ---
camera_width_px = 1920
camera_height_px = 1200
camera_real_width_cm = 139
camera_real_height_cm = 86

# --- Ölçekleme Hesabı ---
scale_px_per_cm_x = camera_width_px / camera_real_width_cm
scale_px_per_cm_y = camera_height_px / camera_real_height_cm

# --- JSON'dan Noktaları Yükle ---
with open(json_file_path, "r") as f:
    data = json.load(f)

shape_points = data[0]['points']

# --- Ham bounding box & ölçek çıkar ---
x_coords, y_coords = zip(*shape_points)
min_x, max_x = min(x_coords), max(x_coords)
min_y, max_y = min(y_coords), max(y_coords)

raw_width = max_x - min_x
raw_height = max_y - min_y

shape_scale_x_cm = real_width_cm / raw_width
shape_scale_y_cm = real_height_cm / raw_height

# Toplam px ölçekleme
final_scale_x = shape_scale_x_cm * scale_px_per_cm_x
final_scale_y = shape_scale_y_cm * scale_px_per_cm_y

# Şekil merkezini hesapla (cm cinsinden)
shape_center_x = (min_x + max_x) / 2
shape_center_y = (min_y + max_y) / 2

# --- Kamera Aç ve Şekli Göster ---
def show_daheng_realtime(camera_sn):
    device_manager = gx.DeviceManager()
    dev_num, dev_info_list = device_manager.update_device_list()

    if dev_num == 0:
        print("Hiçbir kamera bulunamadı.")
        return

    cam = device_manager.open_device_by_sn(camera_sn)
    cam.stream_on()
    print(f"Kamera {camera_sn} ile bağlantı kuruldu. Görüntü başlatılıyor...")

    try:
        while True:
            raw_image = cam.data_stream[0].get_image()
            if raw_image is None:
                print("Görüntü alınamadı.")
                continue

            rgb_image = raw_image.convert("RGB")
            if rgb_image is None:
                print("RGB'ye dönüşüm başarısız.")
                continue

            frame = rgb_image.get_numpy_array()
            if frame is None:
                print("NumPy dizisine dönüşüm başarısız.")
                continue

            # Görüntü merkezini hesapla
            image_center_x = frame.shape[1] // 2
            image_center_y = frame.shape[0] // 2

            offset_x = image_center_x - int(shape_center_x * final_scale_x)
            offset_y = image_center_y - int(shape_center_y * final_scale_y)

            # Aynalanmış noktalar (Y ekseninde)
            mirrored_pixel_points = []
            for x_cm, y_cm in shape_points:
                mirrored_y_cm = (max_y + min_y) - y_cm
                px = int((x_cm * final_scale_x) + offset_x)
                py = int((mirrored_y_cm * final_scale_y) + offset_y)
                mirrored_pixel_points.append((px, py))

            for i in range(1, len(mirrored_pixel_points)):
                cv2.line(frame, mirrored_pixel_points[i - 1], mirrored_pixel_points[i], (0, 255, 0), 1)

            cv2.namedWindow("Daheng Realtime Görüntü", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Daheng Realtime Görüntü", 1000, 800)
            cv2.imshow("Daheng Realtime Görüntü", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cam.stream_off()
        cam.close_device()
        cv2.destroyAllWindows()
        print("Kamera kapatıldı ve pencere kapatıldı.")

if __name__ == "__main__":
    show_daheng_realtime(CAMERA_SN)