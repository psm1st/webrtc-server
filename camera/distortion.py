import cv2
import numpy as np

def crop_to_square(image):
    height, width = image.shape[:2]
    size = min(width, height)
    x_center, y_center = width // 2, height // 2
    x_start = max(0, x_center - size // 2)
    y_start = max(0, y_center - size // 2)
    return image[y_start:y_start + size, x_start:x_start + size]

def apply_barrel_distortion(image):
    square_image = crop_to_square(image)
    height, width = square_image.shape[:2]

    camera_matrix = np.array([[width, 0, width / 2],
                              [0, height, height / 2],
                              [0, 0, 1]], dtype=np.float32)
    distortion_coefficients = np.array([0.3, 0.1, 0, 0], dtype=np.float32)

    new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coefficients, (width, height), 1)
    map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, distortion_coefficients, None, new_camera_matrix,
                                             (width, height), cv2.CV_32FC1)
    return cv2.remap(square_image, map1, map2, cv2.INTER_LINEAR)
