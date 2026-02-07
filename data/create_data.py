import tkinter as tk
from tkinter import messagebox, ttk
import pyaudio
import wave
import threading
import os
import csv

class AudioRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Ovoz Yozish Dasturi")
        self.root.geometry("850x500")
        
        # O'zgaruvchilar
        self.is_recording = False
        self.frames = []
        self.current_index = 0
        self.start_number = 1
        self.texts = []
        self.selected_device_index = None
        
        # Audio sozlamalari
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        # PyAudio obyekti
        self.audio = pyaudio.PyAudio()
        
        # Papka yaratish
        if not os.path.exists("audio"):
            os.makedirs("audio")
        
        # Mavjud mikrofonlarni olish
        self.get_audio_devices()
        
        # GUI yaratish
        self.create_widgets()
        
        # text.csv faylini o'qish
        self.load_texts()
    
    def load_texts(self):
        """text.csv faylidan textlarni o'qish"""
        try:
            with open('text.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.texts = [row['text'].strip() for row in reader]
            
            if not self.texts:
                messagebox.showerror("Xato", "text.csv faylida textlar yo'q!")
        except FileNotFoundError:
            messagebox.showerror("Xato", "text.csv fayli topilmadi!")
            self.texts = []
        except Exception as e:
            messagebox.showerror("Xato", f"Faylni o'qishda xato: {e}")
            self.texts = []
    
    def get_audio_devices(self):
        """Mavjud audio qurilmalarni olish"""
        self.audio_devices = []
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        
        for i in range(0, numdevices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            # Faqat input qurilmalarni olish
            if device_info.get('maxInputChannels') > 0:
                self.audio_devices.append({
                    'index': i,
                    'name': device_info.get('name')
                })
        
        # Default qurilmani tanlash
        if self.audio_devices:
            self.selected_device_index = self.audio_devices[0]['index']
    
    def create_widgets(self):
        """GUI elementlarini yaratish"""
        
        # Mikrofon tanlash
        mic_frame = tk.Frame(self.root)
        mic_frame.pack(pady=10)
        
        tk.Label(mic_frame, text="Mikrofon:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.mic_var = tk.StringVar()
        if self.audio_devices:
            device_names = [f"{d['index']}: {d['name']}" for d in self.audio_devices]
            self.mic_var.set(device_names[0])
        else:
            device_names = ["Mikrofon topilmadi"]
            self.mic_var.set(device_names[0])
        
        self.mic_dropdown = ttk.Combobox(mic_frame, textvariable=self.mic_var, 
                                         values=device_names, width=50, state="readonly")
        self.mic_dropdown.pack(side=tk.LEFT, padx=5)
        self.mic_dropdown.bind("<<ComboboxSelected>>", self.on_mic_select)
        
        # Boshlang'ich raqam kiritish
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=15)
        
        tk.Label(top_frame, text="Boshlang'ich raqam (N):", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.start_entry = tk.Entry(top_frame, width=10, font=("Arial", 12))
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="Boshlash", command=self.set_start_number, 
                 font=("Arial", 12), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Text ko'rsatish
        text_frame = tk.Frame(self.root)
        text_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(text_frame, text="O'qish uchun text:", font=("Arial", 12, "bold")).pack()
        
        self.text_display = tk.Text(text_frame, height=5, font=("Arial", 16), wrap=tk.WORD)
        self.text_display.pack(fill=tk.BOTH, expand=True, pady=10)
        self.text_display.config(state=tk.DISABLED)
        
        # Hozirgi fayl nomi
        self.filename_label = tk.Label(self.root, text="", font=("Arial", 12, "italic"))
        self.filename_label.pack(pady=5)
        
        # Yozish tugmasi
        self.record_button = tk.Button(self.root, text="⬤ Yozishni Boshlash", 
                                      command=self.toggle_recording,
                                      font=("Arial", 14, "bold"), 
                                      bg="#f44336", fg="white",
                                      height=2, width=25)
        self.record_button.pack(pady=20)
        
        # Navigatsiya tugmalari
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)
        
        self.prev_button = tk.Button(nav_frame, text="◀ Orqaga", command=self.previous_text,
                                     font=("Arial", 12), width=15, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = tk.Button(nav_frame, text="Oldinga ▶", command=self.next_text,
                                     font=("Arial", 12), width=15, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        # Status
        self.status_label = tk.Label(self.root, text="Boshlang'ich raqamni kiriting va 'Boshlash' ni bosing", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=5)
    
    def set_start_number(self):
        """Boshlang'ich raqamni o'rnatish"""
        try:
            self.start_number = int(self.start_entry.get())
            if self.start_number < 1:
                messagebox.showerror("Xato", "Raqam 1 dan katta bo'lishi kerak!")
                return
            
            self.current_index = self.start_number - 1
            
            if self.current_index >= len(self.texts):
                messagebox.showerror("Xato", f"Faylda faqat {len(self.texts)} ta text bor!")
                return
            
            self.show_current_text()
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.start_entry.config(state=tk.DISABLED)
            self.status_label.config(text="Textni o'qing va yozish tugmasini bosing", fg="green")
            
        except ValueError:
            messagebox.showerror("Xato", "Iltimos, to'g'ri raqam kiriting!")
    
    def on_mic_select(self, event):
        """Mikrofon tanlanganda"""
        selected = self.mic_var.get()
        if selected and ":" in selected:
            device_index = int(selected.split(":")[0])
            self.selected_device_index = device_index
            device_name = selected.split(":")[1].strip()
            self.status_label.config(text=f"Tanlandi: {device_name}", fg="blue")
    
    def show_current_text(self):
        """Hozirgi textni ko'rsatish"""
        if 0 <= self.current_index < len(self.texts):
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, self.texts[self.current_index])
            self.text_display.config(state=tk.DISABLED)
            
            filename = f"utt_{self.current_index + 1:04d}.wav"
            self.filename_label.config(text=f"Fayl nomi: {filename}")
        else:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, "Textlar tugadi!")
            self.text_display.config(state=tk.DISABLED)
    
    def toggle_recording(self):
        """Yozishni boshlash/to'xtatish"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Ovoz yozishni boshlash"""
        if self.current_index >= len(self.texts):
            messagebox.showwarning("Ogohlantirish", "Textlar tugadi!")
            return
        
        self.is_recording = True
        self.frames = []
        self.record_button.config(text="⬛ Yozishni To'xtatish", bg="#4CAF50")
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.status_label.config(text="🔴 Yozilmoqda...", fg="red")
        
        # Yozishni alohida threadda boshlash
        self.recording_thread = threading.Thread(target=self.record)
        self.recording_thread.start()
    
    def record(self):
        """Ovoz yozish"""
        try:
            stream = self.audio.open(format=self.FORMAT,
                                    channels=self.CHANNELS,
                                    rate=self.RATE,
                                    input=True,
                                    input_device_index=self.selected_device_index,
                                    frames_per_buffer=self.CHUNK)
            
            while self.is_recording:
                data = stream.read(self.CHUNK)
                self.frames.append(data)
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.is_recording = False
            messagebox.showerror("Xato", f"Ovoz yozishda xato: {e}\n\nBoshqa mikrofon tanlang!")
    
    def stop_recording(self):
        """Yozishni to'xtatish va saqlash"""
        self.is_recording = False
        self.record_button.config(text="⬤ Yozishni Boshlash", bg="#f44336")
        self.status_label.config(text="Saqlanyapti...", fg="orange")
        
        # Faylni saqlash
        filename = f"utt_{self.current_index + 1:04d}.wav"
        filepath = os.path.join("audio", filename)
        
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        # metadata.csv ga qo'shish
        self.save_metadata(filename, self.texts[self.current_index])
        
        self.prev_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"✓ Saqlandi: {filename}", fg="green")
        
        # Avtomatik keyingi textga o'tish
        if self.current_index < len(self.texts) - 1:
            self.current_index += 1
            self.show_current_text()
            self.status_label.config(text=f"✓ Saqlandi va keyingi textga o'tildi", fg="green")
        else:
            messagebox.showinfo("Tugadi", "Barcha textlar tugadi! Tabriklaymiz!")
    
    def save_metadata(self, filename, transcript):
        """metadata.csv ga yozish"""
        file_exists = os.path.exists('metadata.csv')
        
        with open('metadata.csv', 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['filename', 'transcript'])
            writer.writerow([filename, transcript])
    
    def previous_text(self):
        """Oldingi textga o'tish"""
        if self.current_index > self.start_number - 1:
            # Hozirgi faylni o'chirish
            current_filename = f"utt_{self.current_index + 1:04d}.wav"
            current_filepath = os.path.join("audio", current_filename)
            if os.path.exists(current_filepath):
                os.remove(current_filepath)
            
            # metadata.csv dan o'chirish
            self.remove_from_metadata(current_filename)
            
            # Oldingi textga o'tish
            self.current_index -= 1
            self.show_current_text()
            
            self.status_label.config(text="Oldingi textga qaytildi", fg="blue")
        else:
            messagebox.showinfo("Ma'lumot", "Bu birinchi text!")
    
    def next_text(self):
        """Keyingi textga o'tish"""
        if self.current_index < len(self.texts) - 1:
            self.current_index += 1
            self.show_current_text()
            self.status_label.config(text="Keyingi textga o'tildi", fg="blue")
        else:
            messagebox.showinfo("Ma'lumot", "Bu oxirgi text!")
    
    def remove_from_metadata(self, filename):
        """metadata.csv dan ma'lum qatorni o'chirish"""
        if not os.path.exists('metadata.csv'):
            return
        
        # Barcha qatorlarni o'qish
        rows = []
        with open('metadata.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Kerakli qatorni o'chirish
        rows = [row for row in rows if len(row) < 2 or row[0] != filename]
        
        # Qayta yozish
        with open('metadata.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def __del__(self):
        """PyAudio ni yopish"""
        self.audio.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorder(root)
    root.mainloop()