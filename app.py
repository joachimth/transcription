"""
This program is a simple transcriber, that transcribes 
audio files and returns an SRT-file. The transcribing is
done by OpenAI"s Whisper model: https://github.com/openai/whisper

This code bundles into an .exe-file that runs on Windows. It is developed on a Windows 11 machine, 
but has run succesfully on Windows 7 and 10 machines.

Author: Martin Dreyer
"""

# This file is part of T-tex.
#
# T-tex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 3, as published by
# the Free Software Foundation.
#
# T-tex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with T-tex. If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import StringVar
import tkinter.filedialog as filedialog
import sys
import os
import traceback
import subprocess
import threading
from redirector import Redirector
from styling import *
from settings import *
import whisper
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("T-TEX")
        self.model_size = MODEL_SIZE
        self.output_dir = OUTPUT_DIR
        self.output_format = OUTPUT_FORMAT
        self.configure_grid(0, 1)
        self.configure_background(BACKGROUND)
        self.frame = self.create_frame(height=HEIGHT, width=WIDTH, background=BACKGROUND)
        self.label = self.create_label(labeltext="Vælg en fil for at få den transskriberet", background=BACKGROUND, color=COLOR, font=FONT, fontsize=LABEL_FONTSIZE, colpos=0, rowpos=0)
        self.select_button = self.create_button( buttontext="Vælg fil", pady=4, padx=8, width=int((WIDTH*0.05)), font=FONT, fontsize=12, background=BUTTON_BG, color=BUTTON_COLOR, command=self.handle_upload, activebackground=BUTTON_BG_ACTIVE, activeforeground=BUTTON_FG_ACTIVE, colpos=0, rowpos=2)
        self.transcribe_button = self.create_button( buttontext="Transkribér", pady=4, padx=8, width=int((WIDTH*0.05)), font=FONT, fontsize=12, background=BUTTON_BG, color=BUTTON_COLOR, command=self.start_transcription_thread, activebackground=BUTTON_BG_ACTIVE, activeforeground=BUTTON_FG_ACTIVE, colpos=0, rowpos=3)
        self.dropdown = self.create_dropdown(command=self.set_model_size, background=BACKGROUND, color=COLOR, font=FONT, fontsize=12, colpos=0, rowpos=4)
        self.textbox = self.create_textbox(textbackground=TEXTBOX_BACKGROUND, textcolor=TEXTBOX_COLOR, font=FONT, fontsize=12, highlightbackground="#f2f2f2", colpos=0, rowpos=6)
        self.file_path = None
        self.current_file_label = self.create_label(labeltext=f"Valgt fil: {'Ingen' if self.file_path is None else self.file_path}", background=BACKGROUND, color=COLOR, font=FONT, fontsize=LABEL_FONTSIZE, colpos=0, rowpos=1)


    def is_ffmpeg_available(self):
        try:
            ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
            subprocess.run([ffmpeg_path, '-version'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def on_enter(self, event, button):
        button["bg"] = BUTTON_BG_HOVER

    def on_leave(self, event, button):
        button["bg"] = BUTTON_BG
    
    def configure_background(self, background):
        self.config(bg=background)

    def configure_grid(self, index, weight):
        self.rowconfigure(index=index, weight=weight)
        self.columnconfigure(index=index, weight=weight)

    def create_button(self, buttontext, pady, padx, width, background, color, font, fontsize, command, activebackground, activeforeground, colpos, rowpos):
        button = tk.Button(
            self, 
            text=buttontext,
            pady=pady,
            padx=padx,
            width=width,
            bg=background,
            fg=color,
            relief="flat",
            font=(font, fontsize),
            borderwidth=0,
            command=command,
            cursor="hand2",
            activebackground=activebackground,
            activeforeground=activeforeground
        )

        button.grid(column=colpos, row=rowpos, pady=(HEIGHT/10))
        button.bind("<Enter>", lambda event, button=button: self.on_enter(event, button))
        button.bind("<Leave>", lambda event, button=button: self.on_leave(event, button))

        return button
    
    def create_dropdown(self, command, background, color, font, fontsize, colpos, rowpos):
        options = [
            "Stor",
            "Mellem",
            "Lille",
            "Basal"
        ]
        clicked = StringVar()
        clicked.set("Mellem")
        dropdown = tk.OptionMenu(self,
                                      clicked,
                                      *options,
                                      command=command)
        
        self.create_label(labeltext="Vælg modelstørrelse (mindre modeller er hurtigere, men transskriberingen er mindre præcis)", background=BACKGROUND, color=COLOR, font=FONT, fontsize=DROPDOWN_LABEL_FONTSIZE, colpos=colpos, rowpos=rowpos)


        dropdown.grid(column=colpos, row=rowpos+1, pady=10, padx=10)
        dropdown.configure(
            padx=4,
            pady=8,
            font=(font, fontsize),
            relief="flat",
            cursor="hand2",
            bg=background,
            fg=color,
            borderwidth=0,
            width=int((WIDTH*0.01)),
        )

        return dropdown

    def create_frame(self, height, width, background):
        frame = tk.Frame(self, height=height, width=width, bg=background)
        frame.grid()
        return frame
    
    def create_label(self, labeltext, background, color, font, fontsize, colpos, rowpos):
        label = tk.Label(
        self, text=labeltext,
        bg=background,
        fg=color,
        font=(font, fontsize)
        )
        label.grid(column=colpos, row=rowpos)
        return label
    
    def create_textbox(self, textbackground, textcolor, font, fontsize, highlightbackground, colpos, rowpos):
        textbox = tk.Text(
            self,
            wrap=tk.WORD,
            bg=textbackground,
            fg=textcolor,
            borderwidth=0,
            padx=10,
            pady=10,
            font=(font, fontsize),
            highlightthickness=3,
        )
        textbox.config(highlightbackground=highlightbackground)
        textbox.grid(column=colpos, row=rowpos, pady=40, padx=40)
        sys.stdout = Redirector(textbox)

        return textbox
    
    def set_model_size(self, selected_option):
        if selected_option == "Stor":
            self.model_size = "large"
        elif selected_option == "Mellem":
            self.model_size = "medium"
        elif selected_option == "Lille":
            self.model_size = "small"
        elif selected_option == "Basal":
            self.model_size = "base"

    def handle_upload(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path == '':
            return
        elif "." in self.file_path and self.file_path.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:
            self.current_file_label.config(text=f"Valgt fil: {self.file_path.split('/')[-1]}")
        else:
            print(f"Forkert filtype. Følgende filtyper er godtaget: {ALLOWED_EXTENSIONS}")

    def set_ffmpeg_path(self):
        # Assuming the ffmpeg.exe is in the same directory as your main script
        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")

        # Get the current PATH environment variable
        current_path = os.environ.get("PATH", "")

        # Append the directory containing the ffmpeg executable to the PATH
        os.environ["PATH"] = f"{current_path}{os.pathsep}{os.path.dirname(ffmpeg_path)}"

        return ffmpeg_path
    
    def optimize_file(self, file_path):
        try:
            output_filename = file_path.split(".")[0] + ".ogg"
            ffmpeg_path = self.set_ffmpeg_path()
            command = [
                ffmpeg_path,
                "-i", file_path,
                "-vn",
                "-map_metadata", "-1",
                "-ac", "1",
                "-c:a", "libopus",
                "-b:a", "12k",
                "-application", "voip",
                output_filename
            ]

            result = subprocess.run(command, shell=False)

            # Check the return code
            if result.returncode == 0:
                print(f"Converted inputfile to .ogg: {output_filename}")
                return output_filename
            else:
                print(
                    f"Error during conversion. Return code: {result.returncode}")
                print(result.stderr)

        except Exception as e:
            traceback.print_exc()
            print(f"Fejl under transskribering: {e}")
            return None       

    def start_transcription_thread(self):
            try:
                transcription_thread = threading.Thread(
                    target=self.transcribe, args=(self.file_path,)
                )
                transcription_thread.start()
            except Exception as e:
                traceback.print_exc()
                print(f"Error starting transcription thread: {e}")
    
    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            traceback.print_exc()
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def float_to_time(self, float_value: float):
        milliseconds = int((float_value % 1) * 1000)
        seconds = int(float_value % 60)
        minutes = int((float_value // 60) % 60)
        hours = int(float_value // 3600)

        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        return time_str
    
    def save_tanscription(self, result, output_filename):
        index = 1
        try:
            with open(output_filename, "w", encoding="utf-8") as file:
                for value in result["segments"]:
                    start_time_str = self.float_to_time(value["start"])
                    end_time_str = self.float_to_time(value["end"])
                    text = value["text"].strip()
                    file.write(f"{index}\n")
                    file.write(f"{start_time_str} --> {end_time_str}\n")
                    file.write(f"{text}\n\n")
                    index += 1
            

        except Exception as e:
            traceback.print_exc()
            print(f"Fejl ved skrivning til tekstfil: {e}")
        
    def transcribe(self, file_path):
        try:
            if file_path is None:
                return
            
            if self.is_ffmpeg_available():
                print('ffmpeg is available!')
            else:
                print('ffmpeg is not available!')

            if file_path is not None:
                print("Initializing")
                directory, filename = os.path.split(file_path)
                self.transcribe_button.config(state=tk.DISABLED)

                ogg_file = self.optimize_file(self.file_path)
                
                print(f"Loading {self.model_size.upper()} model")
                model = whisper.load_model(self.model_size, device=DEVICE)

                if model:
                    print("Transcribing ...")
                result = model.transcribe(audio=self.get_resource_path(ogg_file), fp16=FP16, word_timestamps=TIMESTAMPS)
                if result:
                    if ogg_file:
                        os.remove(self.get_resource_path(ogg_file))
                    self.save_tanscription(result, (os.path.join(directory, filename.split('.')[0] + '.' + self.output_format)))

                    self.transcribe_button.config(state=tk.NORMAL)
                    print(f"{filename.split('.')[0] + '.' + self.output_format} saved to {directory + '/'} ")
                    print("Transcription finished.")
                    
        except Exception as e:
            traceback.print_exc()
            print(f"Error during transcription: {e}")


def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
