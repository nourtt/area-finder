import cv2
import numpy as np
import easyocr
from paddleocr import PaddleOCR

# Initialize OCR models

paddle_ocr_reader = PaddleOCR(use_angle_cls=True, lang='en')  # Using PaddleOCR

# Load YOLO model for object detection (furniture)
net = cv2.dnn.readNetFromDarknet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Load the class names of objects YOLO can detect
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Define categories to exclude
exclude_categories = ["kitchen", "bathroom", "hall", "corridor"]

def detect_furniture(img):
    """
    Detects furniture in the image using YOLO.
    """
    # Prepare the image for YOLO detection
    height, width, channels = img.shape
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    furniture_detections = []
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            # Filter by confidence threshold
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                
                # Save the detection if it's relevant
                furniture_detections.append((classes[class_id], (x, y, w, h)))
    
    return furniture_detections

def detect_text_and_area(img):
    """
    Detects room labels and areas from the blueprint using OCR.
    """
    results = paddle_ocr_reader.readtext(img)  # Can switch between EasyOCR or PaddleOCR
    
    room_areas = []
    
    for (bbox, text, prob) in results:
        text = text.lower()
        if any(category in text for category in exclude_categories):
            continue  # Exclude kitchens, bathrooms, halls, etc.
        
        # Try to extract area if it's present
        area = None
        for token in text.split():
            try:
                area = float(token.replace(",", "."))
                break
            except ValueError:
                continue

        if area:
            room_areas.append((text, area))
    
    return room_areas

def process_blueprint(image_path):
    """
    Main function to process the blueprint image, detect living rooms, and calculate areas.
    """
    # Load blueprint image
    img = cv2.imread(image_path)
    
    # Step 1: Detect furniture
    furniture_detections = detect_furniture(img)
    
    # Step 2: Filter and identify living rooms
    living_rooms = []
    for item, bbox in furniture_detections:
        if item in exclude_categories:
            continue
        living_rooms.append((item, bbox))
    
    # Step 3: Detect text and calculate areas
    room_areas = detect_text_and_area(img)
    
    # Step 4: Calculate total area of living rooms
    total_area = sum(area for _, area in room_areas)
    
    # Step 5: Display the result
    print(f"Detected {len(living_rooms)} living rooms.")
    print(f"Total area of the apartment: {total_area} square meters")
    
    # Optional: Draw detected bounding boxes and labels on the image
    for item, (x, y, w, h) in living_rooms:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, item, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Blueprint", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage
process_blueprint("Picture0.png")