import os 
import zipfile 
import cv2 
import tkinter as tk 
from tkinter import filedialog, messagebox 
from tkinter import ttk 
from PIL import Image, ImageTk 
import pandas as pd 
from paddleocr import PaddleOCR, draw_ocr
import matplotlib.pyplot as plt
import re
root = tk.Tk() 
root.title("Авторазметка комнат") 
root.geometry("800x600") 
 
data = [] 
image_label = None   
 
def clear_table(): 
    global data 
    for item in table.get_children(): 
        table.delete(item) 
    data.clear()   
 
def add_data_to_table(new_data): 
    existing_filenames = {table.item(i, 'values')[0] for i in table.get_children()} 
    for row in new_data: 
        if row[0] not in existing_filenames:   
            table.insert("", "end", values=row) 
            data.append(row) 
 
def load_zip_file(): 
    zip_file_path = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")]) 
    if zip_file_path: 
        extract_dir = filedialog.askdirectory(title="Выберите папку для распаковки ZIP файла") 
        if extract_dir: 
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref: 
                zip_ref.extractall(extract_dir) 
            messagebox.showinfo("Успех", "ZIP файл успешно загружен и распакован!") 
            process_images(extract_dir) 
 
def load_folder(): 
    folder_path = filedialog.askdirectory(title="Выберите папку с изображениями") 
    if folder_path: 
        process_images(folder_path) 
 
def load_single_image(): 
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.jfif")]) 
    if image_path: 
        process_images(os.path.dirname(image_path), single_image=image_path) 
 
def process_images(folder, single_image=None): 
    clear_table()   
    new_data = [] 
    if single_image: 
        image_paths = [single_image] 
    else: 
        image_paths = [os.path.join(folder, filename) for filename in os.listdir(folder)  
                       if filename.endswith((".png", ".jpg", ".jpeg", ".jfif"))] 
     
    for image_path in image_paths: 
        try: 
            image = cv2.imread(image_path) 
            if image is None: 
                continue   
            else: 
                ocr = PaddleOCR(use_angle_cls=True, lang='en')
                result = ocr.ocr(image_path, cls=True)
                rooms = [];

            for line in result:
                for (text_bbox, (text)) in line:
                    txt = text[0].replace(",", ".")

                    numbers = re.findall(r'\d+\.\d+|\d+', txt)


                    numbers = [float(num) for num in numbers]

                    if numbers == []:
                        continue
                    else:
                        if numbers[0] > 1.0 and numbers[0] < 75.0 :
                            print(numbers[0])
                            x = numbers[0]
                            rooms.append(x)
                    
            total_area = sum(rooms)   
            living_rooms = len(rooms)
            new_data.append([os.path.basename(image_path), total_area, living_rooms, image_path]) 
        except Exception as e: 
            print(f"Ошибка при обработке файла {image_path}: {e}") 
 
    add_data_to_table(new_data) 
 
def display_image(event): 
    global image_label 
    selected_item = table.selection() 
    if selected_item: 
        item = table.item(selected_item) 
        image_path = item['values'][3] 
        img = Image.open(image_path) 
        img = img.resize((300, 300))   
        img_tk = ImageTk.PhotoImage(img) 
         
        if image_label: 
            image_label.config(image=img_tk) 
            image_label.image = img_tk 
        else: 
            image_label = tk.Label(root, image=img_tk) 
            image_label.image = img_tk 
            image_label.pack(pady=10) 
 
def export_to_excel(): 
    if not data: 
        messagebox.showwarning("Ошибка", "Нет данных для экспорта!") 
        return 
 
    export_file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")]) 
    if export_file_path: 
        df = pd.DataFrame(data, columns=["Имя файла", "Общая площадь (м²)", "Количество жилых комнат", "Путь к изображению"]) 
        df.to_excel(export_file_path, index=False) 
        messagebox.showinfo("Успех", f"Данные успешно экспортированы в {export_file_path}") 
 
button_frame = tk.Frame(root) 
button_frame.pack(pady=10) 
 
load_zip_button = tk.Button(button_frame, text="Загрузить ZIP файл", command=load_zip_file) 
load_zip_button.pack(side="left", padx=5) 
 
load_folder_button = tk.Button(button_frame, text="Загрузить папку", command=load_folder) 
load_folder_button.pack(side="left", padx=5) 
 
load_image_button = tk.Button(button_frame, text="Загрузить изображение", command=load_single_image) 
load_image_button.pack(side="left", padx=5) 
 
export_button = tk.Button(button_frame, text="Экспортировать в Excel",command=export_to_excel) 
export_button.pack(side="left", padx=5) 
 
style = ttk.Style() 
style.configure("Treeview.Heading", anchor="center")   
style.configure("Treeview", rowheight=25)   
 
columns = ("Имя файла", "Общая площадь (м²)", "Количество жилых комнат") 
table = ttk.Treeview(root, columns=columns, show="headings") 
table.heading("Имя файла", text="Имя файла") 
table.heading("Общая площадь (м²)", text="Общая площадь (м²)") 
table.heading("Количество жилых комнат", text="Количество жилых комнат") 
 
table.column("Общая площадь (м²)", anchor="center") 
table.column("Количество жилых комнат", anchor="center") 
table.pack(pady=20, fill="x") 
 
table.bind("<ButtonRelease-1>", display_image) 
 
root.mainloop()