try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, scrolledtext
except ImportError:
    print("Error: The 'tkinter' module is missing.")
    print("Please install it by running: sudo apt-get install python3-tk")
    import sys
    sys.exit(1)

import os
import shutil
import morse_logic

class MorseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Morse Code Trainer v{morse_logic.VERSION}")
        
        # High DPI scaling
        try:
            self.root.tk.call('tk', 'scaling', 1.5)
        except Exception:
            pass
            
        self.root.geometry("700x750")
        
        # Variables
        self.char_wpm = tk.IntVar(value=12)
        self.eff_wpm = tk.IntVar(value=5)
        self.freq = tk.DoubleVar(value=650)
        self.output_file = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "morse.mp3"))
        self.random_count = tk.IntVar(value=10)
        self.random_mode = tk.StringVar(value="mixed")
        self.koch_level = tk.IntVar(value=2)
        self.include_voice = tk.BooleanVar(value=False)
        self.voice_language = tk.StringVar(value="en")
        self._preview_wavs = []
        self._playback_proc = None

        self.char_wpm.trace_add('write', self._clamp_eff_wpm)
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def create_widgets(self):
        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Speed Controls
        speed_frame = ttk.LabelFrame(main_frame, text="Speed Configuration", padding="10")
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="Character Speed (WPM):").grid(row=0, column=0, sticky=tk.W)
        self.char_scale = ttk.Scale(
            speed_frame, from_=5, to=50, 
            variable=self.char_wpm, 
            orient=tk.HORIZONTAL,
            command=lambda v: self.char_wpm.set(round(float(v)))
        )
        self.char_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(speed_frame, textvariable=self.char_wpm).grid(row=0, column=2)
        
        ttk.Label(speed_frame, text="Effective Speed (WPM):").grid(row=1, column=0, sticky=tk.W)
        self.eff_scale = ttk.Scale(
            speed_frame, from_=1, to=50, 
            variable=self.eff_wpm, 
            orient=tk.HORIZONTAL,
            command=lambda v: self.eff_wpm.set(round(float(v)))
        )
        self.eff_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(speed_frame, textvariable=self.eff_wpm).grid(row=1, column=2)
        
        speed_frame.columnconfigure(1, weight=1)
        
        # Audio Config
        audio_frame = ttk.LabelFrame(main_frame, text="Audio & Trainer Config", padding="10")
        audio_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(audio_frame, text="Frequency (Hz):").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(audio_frame, textvariable=self.freq, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(audio_frame, text="Include Voice Answer Key (requires espeak)", variable=self.include_voice).grid(row=0, column=2, sticky=tk.W, padx=20)

        ttk.Label(audio_frame, text="Voice Language:").grid(row=1, column=0, sticky=tk.W)
        voice_langs = ["en", "nl", "de", "fr", "es", "it", "pt", "pl", "ru", "zh", "ja", "ko"]
        ttk.OptionMenu(audio_frame, self.voice_language, "en", *voice_langs).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Text Input
        text_frame = ttk.LabelFrame(main_frame, text="Input Text", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_input = scrolledtext.ScrolledText(text_frame, height=6, font=('Courier New', 11))
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.bind('<KeyRelease>', self.update_visual)
        
        # Random Generator
        rand_frame = ttk.Frame(text_frame)
        rand_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rand_frame, text="Random:").pack(side=tk.LEFT)
        ttk.Entry(rand_frame, textvariable=self.random_count, width=4).pack(side=tk.LEFT, padx=5)
        
        self.mode_menu = ttk.OptionMenu(rand_frame, self.random_mode, "mixed", "letters", "numbers", "punctuation", "koch")
        self.mode_menu.pack(side=tk.LEFT, padx=5)
        
        self.koch_label = ttk.Label(rand_frame, text="Koch Lvl:")
        self.koch_label.pack(side=tk.LEFT, padx=(10, 0))
        self.koch_spin = ttk.Spinbox(rand_frame, from_=2, to=len(morse_logic.KOCH_SEQUENCE), textvariable=self.koch_level, width=3)
        self.koch_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(rand_frame, text="Generate Practice", command=self.generate_random).pack(side=tk.LEFT, padx=5)
        
        # Visual Morse Display
        vis_frame = ttk.LabelFrame(main_frame, text="Visual Morse Feed", padding="10")
        vis_frame.pack(fill=tk.X, pady=5)
        self.visual_feed = tk.Text(vis_frame, height=3, font=('Courier New', 12), state=tk.DISABLED, bg="#f0f0f0")
        self.visual_feed.pack(fill=tk.X)
        
        # Output File
        out_frame = ttk.Frame(main_frame)
        out_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(out_frame, text="Output:").pack(side=tk.LEFT)
        ttk.Entry(out_frame, textvariable=self.output_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(out_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)
        
        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Play Preview", command=self.play_preview).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(btn_frame, text="Stop", command=self.stop_preview).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(btn_frame, text="Generate MP3", command=self.execute).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(btn_frame, text="Check Dependencies", command=self.check_deps).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Status
        self.status = ttk.Label(main_frame, text="Ready", foreground="blue")
        self.status.pack(pady=5)

    def update_visual(self, event=None):
        text = self.text_input.get(1.0, tk.END).strip()
        visual = morse_logic.get_visual_morse(text)
        self.visual_feed.config(state=tk.NORMAL)
        self.visual_feed.delete(1.0, tk.END)
        self.visual_feed.insert(tk.END, visual)
        self.visual_feed.config(state=tk.DISABLED)

    def generate_random(self):
        text = morse_logic.generate_random_text(self.random_count.get(), self.random_mode.get(), self.koch_level.get())
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(tk.END, text)
        self.update_visual()
        self.status.config(text=f"Generated {self.random_count.get()} random groups.", foreground="green")

    def browse_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")])
        if filename:
            self.output_file.set(filename)

    def check_deps(self):
        lame = morse_logic.get_lame_path()
        espeak = shutil.which("espeak") or shutil.which("espeak-ng")
        
        msg = f"Lame encoder: {'Found' if lame else 'NOT Found'}\n"
        if not lame:
            msg += " (Install 'lame' via apt/brew or add to PATH)\n"
            
        msg += f"espeak (Voice): {'Installed' if espeak else 'NOT Installed'}"
        if not espeak:
            if os.name == 'nt':
                msg += " (Windows TTS will use PowerShell fallback)"
            else:
                msg += " (Install 'espeak' for voice support)"
                
        messagebox.showinfo("Dependencies", msg)

    def _clamp_eff_wpm(self, *_):
        if self.eff_wpm.get() > self.char_wpm.get():
            self.eff_wpm.set(self.char_wpm.get())

    def stop_preview(self):
        morse_logic.stop_playback(self._playback_proc)
        self._playback_proc = None
        self.status.config(text="Stopped.", foreground="blue")

    def play_preview(self):
        # Stop any current playback
        morse_logic.stop_playback(self._playback_proc)
        self._playback_proc = None

        # Clean up temp files from the previous preview
        for f in self._preview_wavs:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        self._preview_wavs = []

        text_raw = self.text_input.get(1.0, tk.END).strip()
        if not text_raw:
            messagebox.showwarning("Warning", "Please enter some text.")
            return

        text, ignored = morse_logic.sanitize_text(text_raw)
        status_text = "Generating preview..."
        if ignored:
            status_text += f" (removed {len(ignored)} unsupported chars)"
        self.status.config(text=status_text, foreground="blue")
        self.root.update_idletasks()

        try:
            try:
                freq = float(self.freq.get())
            except (ValueError, tk.TclError):
                messagebox.showwarning("Warning", "Invalid frequency value.")
                return

            tu, _, char_g, word_g = morse_logic.calculate_timings(self.char_wpm.get(), self.eff_wpm.get())
            morse_wav = morse_logic.generate_morse_wav(text, tu, char_g, word_g, freq)
            self._preview_wavs.append(morse_wav)

            wav_to_play = morse_wav
            if self.include_voice.get():
                voice_wav = morse_logic.generate_voice_wav(text, self.voice_language.get())
                if voice_wav:
                    self._preview_wavs.append(voice_wav)
                    combined = morse_logic.combine_wavs([morse_wav, voice_wav])
                    if combined:
                        self._preview_wavs.append(combined)
                        wav_to_play = combined

            success, msg, proc = morse_logic.play_wav(wav_to_play)
            if success:
                self._playback_proc = proc
                self.status.config(text="Playing Morse...", foreground="green")
            else:
                messagebox.showerror("Error", msg)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            for f in self._preview_wavs:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except OSError:
                    pass
            self._preview_wavs = []

    def execute(self):
        text_raw = self.text_input.get(1.0, tk.END).strip()
        if not text_raw:
            messagebox.showwarning("Warning", "Please enter some text.")
            return
            
        text, ignored = morse_logic.sanitize_text(text_raw)
        if ignored:
            message = f"Warning: These characters are not supported and will be skipped:\n{', '.join(sorted(ignored))}\n\nContinue?"
            if not messagebox.askyesno("Sanitation Warning", message):
                return
            
        self.status.config(text="Processing...", foreground="blue")
        self.root.update_idletasks()

        try:
            freq = float(self.freq.get())
        except (ValueError, tk.TclError):
            messagebox.showwarning("Warning", "Invalid frequency value.")
            return

        morse_wav = None
        voice_wav = None
        combined_wav = None
        try:
            tu, _, char_g, word_g = morse_logic.calculate_timings(self.char_wpm.get(), self.eff_wpm.get())
            morse_wav = morse_logic.generate_morse_wav(text, tu, char_g, word_g, freq)

            final_wav = morse_wav
            if self.include_voice.get():
                voice_wav = morse_logic.generate_voice_wav(text, self.voice_language.get())
                if voice_wav:
                    combined_wav = morse_logic.combine_wavs([morse_wav, voice_wav])
                    if combined_wav:
                        final_wav = combined_wav

            success, msg = morse_logic.convert_wav_to_mp3(final_wav, self.output_file.get())
            if success:
                self.status.config(text=f"Successfully saved to {os.path.basename(self.output_file.get())}", foreground="green")
                messagebox.showinfo("Success", f"MP3 generated successfully:\n{self.output_file.get()}")
            else:
                self.status.config(text="Conversion failed!", foreground="red")
                messagebox.showerror("Error", msg)

        except Exception as e:
            self.status.config(text="Error occurred!", foreground="red")
            messagebox.showerror("Error", str(e))
        finally:
            for f in filter(None, [morse_wav, voice_wav, combined_wav]):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except OSError:
                    pass

    def _on_close(self):
        morse_logic.stop_playback(self._playback_proc)
        for f in self._preview_wavs:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MorseApp(root)
    root.mainloop()
