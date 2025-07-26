import customtkinter as ctk
import tkinter
import subprocess
import os
import sys
import re
import threading
from tkinter import filedialog
import sys
import queue

def resource_path(relative_path):
    """ Zwraca poprawną ścieżkę do zasobów, działa dla .py i dla .exe """
    try:
        # PyInstaller tworzy tymczasowy folder i przechowuje jego ścieżkę w _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
    
# --- Dracula Theme Colors & Fonts ---

BG_COLOR = "#282a36"
FRAME_COLOR = "#44475a"
ACCENT_COLOR = "#bd93f9"  # Purple
HIGHLIGHT_COLOR = "#ff79c4"  # Pink
TEXT_COLOR = "#f8f8f2"
COMMENT_COLOR = "#6272a4"

# --- Configuration ---

YT_DLP_PATH = resource_path("yt-dlp.exe")

PREDEFINED_PATHS = {
    "YouTube (Main)": r"D:\Youtube",
    "Brawl Stars Music": r"D:\BrawlStars\assets\music",
    "Brawl Stars SFX": r"D:\BrawlStars\assets\sfx",
}

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        # --- Basic Window Setup ---
        self.title("Ultimate YouTube Downloader")
        self.geometry("850x600")
        self.configure(fg_color=BG_COLOR)
        ctk.set_appearance_mode("dark")

        # --- Grid Configuration ---
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Fonts ---
        self.font_label = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.font_main = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_small = ctk.CTkFont(family="Segoe UI", size=10)

        # --- Download Queue ---
        self.download_queue = queue.Queue()
        self.is_running = False
        self.last_successful_path = ""

        # =================================================================
        # === LEFT COLUMN: CONTROLS =======================================
        # =================================================================

        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)

        # --- URL Input ---
        self.label_url = ctk.CTkLabel(self.left_frame, text="🔗 URL", font=self.font_label, text_color=TEXT_COLOR)
        self.label_url.grid(row=0, column=0, sticky="w")
        self.entry_url = ctk.CTkEntry(self.left_frame, placeholder_text="Paste a video or playlist URL here...", font=self.font_main, fg_color=FRAME_COLOR, border_width=0, text_color=TEXT_COLOR)
        self.entry_url.grid(row=1, column=0, pady=(5, 10), sticky="ew")

        # --- Save Path ---
        self.label_path = ctk.CTkLabel(self.left_frame, text="📁 Save Location", font=self.font_label, text_color=TEXT_COLOR)
        self.label_path.grid(row=2, column=0, pady=(10, 5), sticky="w")
        self.path_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.path_frame.grid(row=3, column=0, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        self.path_option_var = tkinter.StringVar(value="Select a predefined path...")
        self.path_menu = ctk.CTkOptionMenu(self.path_frame, values=list(PREDEFINED_PATHS.keys()) + ["Custom Path..."], command=self.path_option_selected, variable=self.path_option_var, font=self.font_main, fg_color=FRAME_COLOR, button_color=ACCENT_COLOR, button_hover_color=HIGHLIGHT_COLOR)
        self.path_menu.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.entry_path = ctk.CTkEntry(self.path_frame, placeholder_text="Selected path will appear here...", font=self.font_main, fg_color=FRAME_COLOR, border_width=0, text_color=TEXT_COLOR)
        self.entry_path.grid(row=1, column=0, padx=0, pady=5, sticky="ew")

        # --- Options Frame ---
        self.options_frame = ctk.CTkFrame(self.left_frame, fg_color=FRAME_COLOR, corner_radius=10)
        self.options_frame.grid(row=4, column=0, pady=15, sticky="ew")
        self.options_frame.grid_columnconfigure(1, weight=1)

        # --- Format Options ---
        self.label_format = ctk.CTkLabel(self.options_frame, text="⚙️ Format & Quality", font=self.font_label, text_color=TEXT_COLOR)
        self.label_format.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
        self.radio_var = tkinter.StringVar(value="Video")
        self.radio_video = ctk.CTkRadioButton(self.options_frame, text="Video + Audio", variable=self.radio_var, value="Video", font=self.font_main, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR, command=self._update_options_state)
        self.radio_video.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.radio_audio = ctk.CTkRadioButton(self.options_frame, text="Audio Only (.mp3)", variable=self.radio_var, value="Audio", font=self.font_main, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR, command=self._update_options_state)
        self.radio_audio.grid(row=2, column=0, padx=20, pady=(5, 15), sticky="w")

        # --- Quality Selection Menu ---
        self.quality_var = tkinter.StringVar(value="Best")
        self.quality_menu = ctk.CTkOptionMenu(self.options_frame, variable=self.quality_var, values=["Best", "1080p", "720p", "480p"], font=self.font_main, fg_color=BG_COLOR, button_color=ACCENT_COLOR, button_hover_color=HIGHLIGHT_COLOR)
        self.quality_menu.grid(row=1, column=1, padx=15, pady=5, sticky="e")

        # --- Checkbox Options ---
        self.checkbox_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.checkbox_frame.grid(row=3, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        self.subs_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text="Subtitles", font=self.font_small, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR)
        self.subs_checkbox.grid(row=0, column=0, padx=5, sticky="w")
        self.embed_thumb_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text="Embed Thumbnail", font=self.font_small, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR, state="disabled")
        self.embed_thumb_checkbox.grid(row=1, column=0, padx=5, sticky="w")
        self.clear_url_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text="Clear after adding", font=self.font_small, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR)
        self.clear_url_checkbox.grid(row=0, column=1, padx=5, sticky="w")
        
        # --- Add to Queue Button ---
        self.button_add_queue = ctk.CTkButton(self.left_frame, text="➕ Add to Queue", height=40, command=self.add_to_queue, font=self.font_label, fg_color=FRAME_COLOR, hover_color="#5a5d71")
        self.button_add_queue.grid(row=5, column=0, pady=15, sticky="ew")
        
        # =================================================================
        # === RIGHT COLUMN: QUEUE & LOGS ==================================
        # =================================================================
        
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(4, weight=1)
        self.label_queue = ctk.CTkLabel(self.right_frame, text="🔢 Download Queue", font=self.font_label, text_color=TEXT_COLOR)
        self.label_queue.grid(row=0, column=0, sticky="w")
        self.queue_frame = ctk.CTkScrollableFrame(self.right_frame, fg_color=FRAME_COLOR, corner_radius=10)
        self.queue_frame.grid(row=1, column=0, pady=5, sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)
        self.queue_widgets = []
        self.progress_bar = ctk.CTkProgressBar(self.right_frame, orientation="horizontal", progress_color=ACCENT_COLOR, fg_color=FRAME_COLOR)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, pady=10, sticky="ew")
        self.label_logs = ctk.CTkLabel(self.right_frame, text="📜 Logs", font=self.font_label, text_color=TEXT_COLOR)
        self.label_logs.grid(row=3, column=0, pady=(10, 0), sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.right_frame, state="disabled", wrap="word", font=self.font_main, fg_color=FRAME_COLOR, border_width=0, text_color=TEXT_COLOR)
        self.log_textbox.grid(row=4, column=0, pady=5, sticky="nsew")
        self.action_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        self.button_start_queue = ctk.CTkButton(self.action_frame, text="🚀 Start Queue", height=45, command=self.start_queue, font=self.font_label, fg_color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR)
        self.button_start_queue.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.button_open_folder = ctk.CTkButton(self.action_frame, text="📂 Open Folder", height=45, command=self.open_last_folder, font=self.font_label, fg_color=FRAME_COLOR, hover_color="#5a5d71", state="disabled")
        self.button_open_folder.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    def _update_options_state(self):
        """Intelligently enables/disables options based on format."""
        if self.radio_var.get() == "Audio":
            self.quality_menu.configure(state="disabled")
            self.embed_thumb_checkbox.configure(state="normal")
            self.subs_checkbox.configure(state="disabled")
            self.subs_checkbox.deselect()
        else:  # Video
            self.quality_menu.configure(state="normal")
            self.embed_thumb_checkbox.configure(state="disabled")
            self.embed_thumb_checkbox.deselect()
            self.subs_checkbox.configure(state="normal")

    def add_to_queue(self):
        url = self.entry_url.get()
        save_path = self.entry_path.get()
        if not url:
            self.log("❌ Please enter a URL to add to the queue.")
            return
        if not save_path:
            self.log("❌ Please select a save location before adding to the queue.")
            return
        
        job = {
            "url": url, "save_path": save_path,
            "format": self.radio_var.get(),
            "quality": self.quality_var.get(),
            "subs": self.subs_checkbox.get(),
            "embed_thumb": self.embed_thumb_checkbox.get()
        }
        self.download_queue.put(job)
        self.log(f"✅ Added to queue: {url[:50]}...")
        self.update_queue_display()
        if self.clear_url_checkbox.get():
            self.entry_url.delete(0, 'end')

    def process_queue(self):
        while not self.download_queue.empty():
            self.update_progress(0)
            job = self.download_queue.get()
            self.after(0, self.update_queue_display)
            self.log(f"\n--- Starting job: {job['url'][:60]}... ---")

            save_path = job['save_path']
            self.last_successful_path = save_path
            self.button_open_folder.configure(state="normal")

            args = [YT_DLP_PATH, "-i", "--no-warnings"]
            is_playlist = any(s in job['url'] for s in ['playlist?', '/playlist/'])

            # --- Format, Quality, and Subtitles Logic ---
            if job['format'] == "Audio":
                args.extend(['-f', 'bestaudio', '-x', '--audio-format', 'mp3'])
                if job['embed_thumb']:
                    args.append('--embed-thumbnail')
            else:  # Video
                quality = job['quality']
                if quality == "Best":
                    format_string = "bestvideo+bestaudio/best"
                else:
                    resolution = quality.replace('p', '')
                    format_string = f"bestvideo[height<={resolution}]+bestaudio/best"
                args.extend(['-f', format_string, '--merge-output-format', 'mp4'])
                
                # Subtitle arguments added ONLY for video format
                if job['subs']:
                    args.extend(['--write-subs', '--write-auto-sub', '--sub-langs', 'en', '--no-embed-subs'])

            # --- Simplified and corrected output path logic ---
            if is_playlist:
                output_template = os.path.join(save_path, '%(playlist_title)s', '%(playlist_index)s - %(title)s.%(ext)s')
            elif job['subs'] and job['format'] == 'Video':
                output_template = os.path.join(save_path, '%(title)s', '%(title)s.%(ext)s')
            else:
                output_template = os.path.join(save_path, '%(title)s.%(ext)s')

            args.extend(['-o', output_template])
            args.append(job['url'])

            try:
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW)
                vtt_files_to_convert = []
                for line in iter(process.stdout.readline, ''):
                    self.log(line.strip())
                    progress_match = re.search(r'\[download\]\s+([0-9.]+)%', line)
                    if progress_match:
                        self.update_progress(float(progress_match.group(1)) / 100)
                    if "Writing video subtitles to:" in line:
                        vtt_path = line.split("Writing video subtitles to:")[1].strip()
                        vtt_files_to_convert.append(vtt_path)
                
                process.wait()

                if vtt_files_to_convert:
                    self.log("\n--- Cleaning transcripts to .txt ---")
                    for vtt_path in vtt_files_to_convert:
                        if os.path.exists(vtt_path):
                            base_path, _ = os.path.splitext(vtt_path)
                            if base_path.endswith('.en'):
                                base_path = base_path[:-3]
                            txt_path = base_path + ".txt"
                            if self._clean_vtt_to_txt(vtt_path, txt_path):
                                self.log(f"✅ Created clean transcript: {os.path.basename(txt_path)}")
                        else:
                            self.log(f"⚠️ Could not find VTT file to convert: {vtt_path}")

            except Exception as e:
                self.log(f"❌ ERROR during download: {e}")

        self.log("\n✅✅✅ Queue Finished! ✅✅✅")
        self.is_running = False
        self.button_start_queue.configure(state="normal", text="🚀 Start Queue")

    # --- Helper Functions ---
    def log(self, message):
        self.after(0, self._log_thread_safe, message)

    def _log_thread_safe(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", str(message) + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def update_progress(self, value):
        self.after(0, self.progress_bar.set, value)

    def path_option_selected(self, choice):
        if choice == "Custom Path...":
            self.entry_path.delete(0, 'end')
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.entry_path.insert(0, folder_path)
                self.path_option_var.set("Custom Path...")
        else:
            self.entry_path.delete(0, 'end')
            self.entry_path.insert(0, PREDEFINED_PATHS[choice])

    def update_queue_display(self):
        for widget in self.queue_widgets:
            widget.destroy()
        self.queue_widgets.clear()
        
        for i, job in enumerate(list(self.download_queue.queue)):
            job_frame = ctk.CTkFrame(self.queue_frame, fg_color=BG_COLOR)
            job_frame.grid(row=i, column=0, pady=2, sticky="ew")
            job_frame.grid_columnconfigure(0, weight=1)
            dest_folder = os.path.basename(job['save_path'])
            display_text = f"{i+1}. {job['url'][:40]}...  ->  {dest_folder}"
            label = ctk.CTkLabel(job_frame, text=display_text, text_color=TEXT_COLOR, font=self.font_small, anchor="w")
            label.grid(row=0, column=0, padx=5, sticky="ew")
            button = ctk.CTkButton(job_frame, text="❌", width=20, fg_color="transparent", hover_color=FRAME_COLOR, command=lambda j=job: self.remove_from_queue(j))
            button.grid(row=0, column=1, padx=5)
            self.queue_widgets.append(job_frame)

    def remove_from_queue(self, job_to_remove):
        new_queue = queue.Queue()
        [new_queue.put(job) for job in list(self.download_queue.queue) if job != job_to_remove]
        self.download_queue = new_queue
        self.update_queue_display()

    def start_queue(self):
        if self.is_running:
            self.log("⚠️ Queue is already running.")
        elif self.download_queue.empty():
            self.log("⚠️ Queue is empty. Add URLs first.")
        else:
            self.is_running = True
            self.button_start_queue.configure(state="disabled", text="Running...")
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")
            threading.Thread(target=self.process_queue, daemon=True).start()

    def open_last_folder(self):
        if self.last_successful_path and os.path.exists(self.last_successful_path):
            os.startfile(self.last_successful_path)
        else:
            self.log("❌ Last download path not found or not set.")

    def _get_title(self, url):
        try:
            process = subprocess.run([YT_DLP_PATH, '--get-filename', '-o', '%(title)s', url], capture_output=True, text=True, encoding='utf-8', check=True)
            return process.stdout.strip()
        except Exception as e:
            self.log(f"❌ Could not get video title: {e}")
            return None

    def _clean_vtt_to_txt(self, vtt_path, txt_path):
        try:
            with open(vtt_path, 'r', encoding='utf-8') as infile, open(txt_path, 'w', encoding='utf-8') as outfile:
                lines = []
                [lines.append(re.sub(r'<[^>]+>', '', line).strip()) for line in infile if "-->" not in line and "WEBVTT" not in line and line.strip() != "" and (not lines or re.sub(r'<[^>]+>', '', line).strip() != lines[-1])]
                outfile.write("\n".join(lines))
            return True
        except:
            return False

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"Failed to start the application: {e}")
        input("Press Enter to exit.")