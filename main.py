import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from pathlib import Path
import sys

# Add the current directory to the Python path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import FFmpegHandler, VideoProcessor

class VideoConverterApp:
    def __init__(self):
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Video Converter Pro")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Initialize components
        self.ffmpeg_handler = FFmpegHandler()
        self.video_processor = VideoProcessor()
        self.selected_files = []
        self.output_folder = ""
        self.conversion_threads = []
        
        # Setup UI
        self.setup_ui()
        
        # Check FFmpeg installation on startup
        self.check_ffmpeg_status()
    
    def setup_ui(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Video Converter Pro", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # FFmpeg status frame
        self.ffmpeg_frame = ctk.CTkFrame(main_frame)
        self.ffmpeg_frame.pack(fill="x", pady=(0, 15))
        
        self.ffmpeg_status_label = ctk.CTkLabel(
            self.ffmpeg_frame, 
            text="Checking FFmpeg installation...",
            font=ctk.CTkFont(size=12)
        )
        self.ffmpeg_status_label.pack(side="left", padx=15, pady=10)
        
        self.install_ffmpeg_btn = ctk.CTkButton(
            self.ffmpeg_frame,
            text="Install FFmpeg",
            command=self.install_ffmpeg,
            state="disabled"
        )
        self.install_ffmpeg_btn.pack(side="right", padx=15, pady=10)
        
        # File selection frame
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            file_frame, 
            text="Select Video Files:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        select_btn = ctk.CTkButton(
            file_frame,
            text="📁 Select Files",
            command=self.select_files,
            height=35
        )
        select_btn.pack(padx=15, pady=(0, 10))
        
        # Selected files listbox
        self.files_listbox = tk.Listbox(
            file_frame,
            height=6,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            font=("Arial", 9)
        )
        self.files_listbox.pack(fill="x", padx=15, pady=(0, 15))
        
        # Format selection frame
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            format_frame, 
            text="Output Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.format_dropdown = ctk.CTkComboBox(
            format_frame,
            values=["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v"],
            state="readonly"
        )
        self.format_dropdown.set("mp4")
        self.format_dropdown.pack(padx=15, pady=(0, 15))
        
        # Output folder frame
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            output_frame, 
            text="Output Folder:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        folder_select_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        folder_select_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.output_folder_label = ctk.CTkLabel(
            folder_select_frame,
            text="No folder selected",
            anchor="w"
        )
        self.output_folder_label.pack(side="left", fill="x", expand=True)
        
        select_folder_btn = ctk.CTkButton(
            folder_select_frame,
            text="📂 Browse",
            command=self.select_output_folder,
            width=100
        )
        select_folder_btn.pack(side="right", padx=(10, 0))
        
        # Conversion controls frame
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", pady=(0, 15))
        
        self.convert_btn = ctk.CTkButton(
            controls_frame,
            text="🚀 Start Conversion",
            command=self.start_conversion,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.convert_btn.pack(pady=15)
        
        # Progress frame
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            progress_frame, 
            text="Conversion Progress:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Progress text area
        self.progress_text = ctk.CTkTextbox(
            progress_frame,
            height=150,
            font=ctk.CTkFont(size=10)
        )
        self.progress_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def check_ffmpeg_status(self):
        """Check if FFmpeg is installed and update UI accordingly"""
        def check_thread():
            is_installed = self.ffmpeg_handler.is_ffmpeg_installed()
            self.root.after(0, self.update_ffmpeg_status, is_installed)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def update_ffmpeg_status(self, is_installed):
        """Update FFmpeg status in UI"""
        if is_installed:
            self.ffmpeg_status_label.configure(
                text="✅ FFmpeg is installed and ready",
                text_color="green"
            )
            self.install_ffmpeg_btn.configure(state="disabled")
            self.check_conversion_ready()
        else:
            self.ffmpeg_status_label.configure(
                text="❌ FFmpeg not found - required for video conversion",
                text_color="red"
            )
            self.install_ffmpeg_btn.configure(state="normal")
    
    def install_ffmpeg(self):
        """Install FFmpeg"""
        self.install_ffmpeg_btn.configure(state="disabled", text="Installing...")
        self.log_progress("Installing FFmpeg... This may take a few minutes.")
        
        def install_thread():
            try:
                success = self.ffmpeg_handler.install_ffmpeg()
                self.root.after(0, self.ffmpeg_install_complete, success)
            except Exception as e:
                self.root.after(0, self.ffmpeg_install_error, str(e))
        
        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()
    
    def ffmpeg_install_complete(self, success):
        """Handle FFmpeg installation completion"""
        if success:
            self.log_progress("✅ FFmpeg installed successfully!")
            self.check_ffmpeg_status()
        else:
            self.log_progress("❌ FFmpeg installation failed. Please install manually.")
            self.install_ffmpeg_btn.configure(state="normal", text="Install FFmpeg")
    
    def ffmpeg_install_error(self, error_msg):
        """Handle FFmpeg installation error"""
        self.log_progress(f"❌ FFmpeg installation error: {error_msg}")
        self.install_ffmpeg_btn.configure(state="normal", text="Install FFmpeg")
    
    def select_files(self):
        """Open file dialog to select video files"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv *.m4v *.3gp *.mpg *.mpeg"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files to convert",
            filetypes=filetypes
        )
        
        if files:
            self.selected_files = list(files)
            self.update_files_listbox()
            self.check_conversion_ready()
    
    def update_files_listbox(self):
        """Update the files listbox with selected files"""
        self.files_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            # Show filename and detected format
            filename = os.path.basename(file_path)
            detected_format = self.video_processor.detect_format(file_path)
            self.files_listbox.insert(tk.END, f"{filename} ({detected_format})")
    
    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = folder
            self.output_folder_label.configure(text=folder)
            self.check_conversion_ready()
    
    def check_conversion_ready(self):
        """Check if all requirements are met for conversion"""
        ffmpeg_ready = self.ffmpeg_handler.is_ffmpeg_installed()
        files_selected = len(self.selected_files) > 0
        folder_selected = bool(self.output_folder)
        
        if ffmpeg_ready and files_selected and folder_selected:
            self.convert_btn.configure(state="normal")
        else:
            self.convert_btn.configure(state="disabled")
    
    def log_progress(self, message):
        """Add message to progress log"""
        self.progress_text.insert("end", f"{message}\n")
        self.progress_text.see("end")
        self.root.update_idletasks()
    
    def start_conversion(self):
        """Start the video conversion process"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to convert.")
            return
        
        if not self.output_folder:
            messagebox.showwarning("No Output Folder", "Please select an output folder.")
            return
        
        # Disable convert button during conversion
        self.convert_btn.configure(state="disabled", text="Converting...")
        
        # Clear previous progress
        self.progress_text.delete("1.0", "end")
        
        output_format = self.format_dropdown.get()
        
        def conversion_thread():
            try:
                for i, input_file in enumerate(self.selected_files):
                    filename = os.path.basename(input_file)
                    self.root.after(0, self.log_progress, f"Converting {filename}...")
                    
                    # Generate output filename
                    base_name = os.path.splitext(filename)[0]
                    output_file = os.path.join(self.output_folder, f"{base_name}.{output_format}")
                    
                    # Progress callback
                    def progress_callback(percent):
                        self.root.after(0, self.log_progress, f"  Progress: {percent:.1f}%")
                    
                    # Convert file
                    success = self.video_processor.convert_video(
                        input_file, 
                        output_file, 
                        output_format,
                        progress_callback
                    )
                    
                    if success:
                        self.root.after(0, self.log_progress, f"✅ {filename} converted successfully!")
                    else:
                        self.root.after(0, self.log_progress, f"❌ Failed to convert {filename}")
                
                # Conversion complete
                self.root.after(0, self.conversion_complete)
                
            except Exception as e:
                self.root.after(0, self.conversion_error, str(e))
        
        # Start conversion in separate thread
        thread = threading.Thread(target=conversion_thread, daemon=True)
        thread.start()
        self.conversion_threads.append(thread)
    
    def conversion_complete(self):
        """Handle conversion completion"""
        self.log_progress("\n🎉 All conversions completed!")
        self.convert_btn.configure(state="normal", text="🚀 Start Conversion")
        messagebox.showinfo("Complete", "All video conversions completed successfully!")
    
    def conversion_error(self, error_msg):
        """Handle conversion error"""
        self.log_progress(f"\n❌ Conversion error: {error_msg}")
        self.convert_btn.configure(state="normal", text="🚀 Start Conversion")
        messagebox.showerror("Error", f"Conversion failed: {error_msg}")
    
    def on_closing(self):
        """Handle application closing"""
        # Wait for any ongoing conversions to complete
        for thread in self.conversion_threads:
            if thread.is_alive():
                response = messagebox.askyesno(
                    "Conversion in Progress", 
                    "Video conversion is in progress. Are you sure you want to exit?"
                )
                if not response:
                    return
                break
        
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = VideoConverterApp()
    app.run()