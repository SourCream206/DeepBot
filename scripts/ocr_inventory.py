import cv2
import numpy as np
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

os.makedirs("debug_boxes", exist_ok=True)


def extract_items(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([5, 10, 80])
    upper = np.array([40, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    print("TOTAL CONTOURS FOUND:", len(contours))

    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)

        print(f"[{i}] box size: {w}x{h}")

        crop = img[y:y+h, x:x+w]

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Save RAW crop
        cv2.imwrite(f"debug_boxes/{i}_raw.png", crop)

        # Save grayscale
        cv2.imwrite(f"debug_boxes/{i}_gray.png", gray)

    print("Saved ALL boxes to debug_boxes/")


if __name__ == "__main__":
    extract_items("inventoryExample.png")
