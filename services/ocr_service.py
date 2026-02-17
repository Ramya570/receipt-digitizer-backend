import pytesseract
from PIL import Image
import cv2
import re


# DO NOT hardcode Windows tesseract path here
# Render/Linux will use system-installed tesseract


def extract_text_from_image(image_path):
    try:
        img = cv2.imread(image_path)

        if img is None:
            return "OCR Error: Unable to read image."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        thresh = cv2.medianBlur(thresh, 3)

        pil_img = Image.fromarray(thresh)

        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(pil_img, config=custom_config)

        return text

    except Exception as e:
        return f"OCR Error: {str(e)}"


def parse_receipt(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    data = {
        "store": None,
        "phone": None,
        "subtotal": None,
        "tax": None,
        "total": None,
        "items": []
    }

    # ---------- STORE NAME ----------
    for line in lines:
        lower = line.lower()

        if (
            re.search(r"\d", line[:3]) or
            "," in line or
            "store:" in lower or
            "register:" in lower or
            "consultant:" in lower or
            re.search(r"\b\d{5,}\b", line)
        ):
            continue

        data["store"] = line
        break

    # ---------- PHONE ----------
    phone_match = re.search(
        r"\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2,4}(?:[\s\-]?\d{2,4})?",
        text
    )
    if phone_match:
        data["phone"] = phone_match.group()

    # ---------- SUBTOTAL / TAX / TOTAL ----------
    for line in lines:
        lower = line.lower()
        amounts = re.findall(r"\d+\.\d{2}", line)

        if "subtotal" in lower and amounts:
            data["subtotal"] = amounts[-1]

        elif "tax" in lower and amounts:
            data["tax"] = amounts[-1]

        elif "total" in lower and amounts:
            data["total"] = amounts[-1]

    # ---------- ITEMS ----------
    temp_items = {}

    for line in lines:
        match = re.match(r"(.+?)\s+(\d+)\s+\$?(\d+\.\d{2})", line)
        if match:
            name = match.group(1).strip()
            quantity = int(match.group(2))
            price = float(match.group(3))

            key = (name, price)

            if key in temp_items:
                temp_items[key]["quantity"] += quantity
            else:
                temp_items[key] = {
                    "name": name,
                    "quantity": quantity,
                    "price": price
                }

    data["items"] = list(temp_items.values())

    # ---------- AUTO CALCULATE SUBTOTAL ----------
    calculated_subtotal = 0
    for item in data["items"]:
        calculated_subtotal += item["price"] * item["quantity"]

    data["calculated_subtotal"] = round(calculated_subtotal, 2)

    # ---------- VALIDATE TOTAL ----------
    if data["total"]:
        try:
            total_value = float(data["total"])
            data["total_matches"] = (
                round(total_value, 2) ==
                round(calculated_subtotal, 2)
            )
        except:
            data["total_matches"] = False
    else:
        data["total_matches"] = False

    return data


# =====================================================
# 🔥 THIS WAS MISSING — MAIN FUNCTION USED BY app.py
# =====================================================

def extract_receipt_data(image_path):
    text = extract_text_from_image(image_path)

    if text.startswith("OCR Error"):
        return {
            "success": False,
            "error": text
        }

    structured_data = parse_receipt(text)

    return {
        "success": True,
        "raw_text": text,
        "structured_data": structured_data
    }
