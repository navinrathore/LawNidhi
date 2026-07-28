import pytesseract
from PIL import Image

def test_ocr():
    try:
        img = Image.open('scripts/captcha.png')
        text = pytesseract.image_to_string(img)
        print(f"Raw OCR Output: '{text.strip()}'")
    except Exception as e:
        print(f"OCR Error: {e}")

if __name__ == "__main__":
    test_ocr()
