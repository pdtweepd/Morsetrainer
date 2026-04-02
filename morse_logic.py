import wave
import math
import os
import re
import random
import subprocess
import tempfile
import shutil

VERSION = "1.0.8"

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--',
    '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...', ':': '---...',
    ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-',
    '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    '<AA>': '.-.-', '<AR>': '.-.-.', '<AS>': '.-...', '<BT>': '-...-',
    '<CL>': '-.-..-..', '<CT>': '-.-.-', '<KN>': '-.--.', '<SK>': '...-.-',
    '<SOS>': '...---...', '<BK>': '-...-.-'
}

# Standard Koch character order
KOCH_SEQUENCE = "KMRSUAPTLOWI.NJEF0Y,VG5/Q9ZH38B?427C16"

def calculate_timings(wpm_char, wpm_eff):
    tu = 1.2 / wpm_char
    if wpm_eff >= wpm_char:
        return tu, tu, tu * 3, tu * 7
    ts = (60.0 / wpm_eff - 31.0 * tu) / 19.0
    char_gap = 3.0 * ts
    word_gap = 7.0 * ts
    return tu, tu, char_gap, word_gap

def sanitize_text(text):
    text = text.upper()
    sanitized = []
    ignored = set()
    tokens = re.findall(r'<[^>]+>|.', text)
    for token in tokens:
        if token in MORSE_CODE:
            sanitized.append(token)
        elif token.startswith('<') and token.endswith('>'):
            inner = token[1:-1]
            valid_inner = True
            for char in inner:
                if char not in MORSE_CODE:
                    valid_inner = False
                    ignored.add(char)
            if valid_inner and inner:
                sanitized.append(token)
            else:
                ignored.add(token)
        elif token.isspace():
            sanitized.append(' ')
        else:
            ignored.add(token)
    return "".join(sanitized), ignored

def get_visual_morse(text):
    text, _ = sanitize_text(text)
    visual = []
    tokens = re.findall(r'<[^>]+>|.', text)
    for token in tokens:
        if token == ' ':
            visual.append("   ")
        else:
            code = MORSE_CODE.get(token, "")
            visual.append(code + " ")
    return "".join(visual)

def generate_random_text(count=10, mode="mixed", koch_level=2):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    punctuation = ".,?!/()&:;=+-_\"$@"

    if mode == "letters":
        pool = letters
    elif mode == "numbers":
        pool = numbers
    elif mode == "punctuation":
        pool = punctuation
    elif mode == "koch":
        pool = KOCH_SEQUENCE[:max(2, min(koch_level, len(KOCH_SEQUENCE)))]
    else: # mixed
        pool = letters + numbers + punctuation

    groups = []
    for _ in range(count):
        group = "".join(random.choice(pool) for _ in range(5))
        groups.append(group)
    return " ".join(groups)

def generate_morse_wav(text, tu, char_gap, word_gap, frequency=650.0):
    import array as _array
    frequency = max(200.0, min(4000.0, float(frequency)))
    SAMPLE_RATE = 22050
    RAMP_TIME = 0.005 # 5ms
    TWO_PI_F_OVER_SR = 2.0 * math.pi * frequency / SAMPLE_RATE

    def make_tone(duration, volume=0.5):
        num_samples = int(duration * SAMPLE_RATE)
        ramp_samples = int(RAMP_TIME * SAMPLE_RATE)
        samples = _array.array('h', [0]) * num_samples
        for i in range(num_samples):
            current_vol = volume
            if i < ramp_samples:
                current_vol = volume * (i / ramp_samples)
            elif i > num_samples - ramp_samples:
                current_vol = volume * ((num_samples - i) / ramp_samples)
            samples[i] = int(current_vol * 32767.0 * math.sin(TWO_PI_F_OVER_SR * i))
        return samples

    def make_silence(duration):
        num_samples = int(duration * SAMPLE_RATE)
        return _array.array('h', [0]) * num_samples

    # Pre-compute common tones and silences for reuse
    dot_tone = make_tone(tu)
    dash_tone = make_tone(tu * 3)
    intra_silence = make_silence(tu)
    char_silence = make_silence(char_gap)
    word_extra = make_silence(max(0, word_gap - char_gap))

    chunks = []
    tokens = re.findall(r'<[^>]+>|.', text.upper())

    for token in tokens:
        if token == ' ':
            chunks.append(word_extra)
            continue

        code = MORSE_CODE.get(token)
        if not code and token.startswith('<') and token.endswith('>'):
            alt_token = token[1:-1]
            code = "".join(MORSE_CODE.get(c, "") for c in alt_token)

        if code:
            if code == '/':
                chunks.append(word_extra)
            else:
                for i, bit in enumerate(code):
                    if bit == '.':
                        chunks.append(dot_tone)
                    elif bit == '-':
                        chunks.append(dash_tone)
                    if i < len(code) - 1:
                        chunks.append(intra_silence)
                chunks.append(char_silence)

    # Combine all chunks into one array
    all_samples = _array.array('h')
    for chunk in chunks:
        all_samples.extend(chunk)

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="morse_")
    try:
        with os.fdopen(fd, 'wb') as tmp:
            with wave.open(tmp, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(all_samples.tobytes())
        return path
    except Exception as e:
        if os.path.exists(path): os.remove(path)
        raise

def generate_voice_wav(text, language="en"):
    """Generates a WAV file using espeak or other TTS."""
    clean_text = re.sub(r'[<>]', ' ', text)
    clean_text = " ".join(clean_text)
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="voice_")
    os.close(fd)

    try:
        # 1. Check Environment Variable (Lead Dev preference)
        env_path = os.getenv("MTSPEAK")
        if env_path:
            cmd_path = shutil.which(env_path) if os.path.sep not in env_path else env_path
            if cmd_path and os.path.exists(cmd_path):
                subprocess.run([cmd_path, "-v", language, "-s", "80", "-w", path, clean_text], check=True, capture_output=True)
                return path

        # 2. Cross-platform check for espeak/espeak-ng as fallback
        espeak_path = shutil.which("espeak") or shutil.which("espeak-ng")
        if espeak_path:
            subprocess.run([espeak_path, "-v", language, "-s", "80", "-w", path, clean_text], check=True, capture_output=True)
            return path

        # 3. On Windows, try PowerShell for TTS (no external dependency)
        if os.name == 'nt':
            # Write text to a temp file to avoid shell injection
            text_fd, text_path = tempfile.mkstemp(suffix=".txt", prefix="tts_")
            try:
                with os.fdopen(text_fd, 'w', encoding='utf-8') as tf:
                    tf.write(clean_text)
                ps_command = (
                    "Add-Type -AssemblyName System.speech; "
                    "$text = Get-Content -Raw -LiteralPath "
                    f"'{text_path.replace(chr(39), chr(39)+chr(39))}'; "
                    "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$speak.SetOutputToWaveFile('{path.replace(chr(39), chr(39)+chr(39))}'); "
                    "$speak.Speak($text); "
                    "$speak.Dispose();"
                )
                subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
            finally:
                if os.path.exists(text_path): os.remove(text_path)
            return path

    except Exception:
        if os.path.exists(path): os.remove(path)
        return None
    # No TTS method available — clean up and return None
    if os.path.exists(path): os.remove(path)
    return None

def generate_silence_wav(duration=1.0, sample_rate=22050):
    """Generates a silent WAV file of the given duration."""
    import array as _array
    num_samples = int(duration * sample_rate)
    silence = _array.array('h', [0]) * num_samples
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="silence_")
    try:
        with os.fdopen(fd, 'wb') as tmp:
            with wave.open(tmp, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence.tobytes())
        return path
    except Exception:
        if os.path.exists(path): os.remove(path)
        raise

def _resample(frames, sampwidth, src_rate, dst_rate):
    """Resample audio frames from src_rate to dst_rate using linear interpolation."""
    import struct as _struct
    if src_rate == dst_rate:
        return frames
    fmt = {1: 'b', 2: '<h', 4: '<i'}[sampwidth]
    sample_count = len(frames) // sampwidth
    samples = _struct.unpack(f'{sample_count}{fmt}', frames)
    ratio = src_rate / dst_rate
    new_count = int(sample_count / ratio)
    resampled = []
    for i in range(new_count):
        src_pos = i * ratio
        idx = int(src_pos)
        frac = src_pos - idx
        if idx + 1 < sample_count:
            val = samples[idx] * (1 - frac) + samples[idx + 1] * frac
        else:
            val = samples[idx] if idx < sample_count else 0
        resampled.append(int(val))
    return _struct.pack(f'{new_count}{fmt}', *resampled)

def combine_wavs(wav_list):
    """Combines multiple WAV files into one, resampling if needed."""
    data = []
    params = None
    for wav_file in wav_list:
        if not wav_file or not os.path.exists(wav_file): continue
        with wave.open(wav_file, 'rb') as w:
            file_params = w.getparams()
            frames = w.readframes(w.getnframes())
            if params is None:
                params = file_params
                data.append(frames)
            elif (file_params.nchannels != params.nchannels or
                  file_params.sampwidth != params.sampwidth):
                continue
            elif file_params.framerate != params.framerate:
                resampled = _resample(frames, params.sampwidth,
                                      file_params.framerate, params.framerate)
                data.append(resampled)
            else:
                data.append(frames)

    if not data: return None

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="combined_")
    try:
        with os.fdopen(fd, 'wb') as tmp:
            with wave.open(tmp, 'wb') as output:
                output.setparams(params)
                for d in data:
                    output.writeframes(d)
        return path
    except Exception as e:
        if os.path.exists(path): os.remove(path)
        raise

def get_lame_path():
    # 1. Check Environment Variable (Lead Dev preference)
    env_path = os.getenv("MTLAME")
    if env_path:
        # If it's just a command name, find it in path, otherwise use as absolute path
        if os.path.sep not in env_path:
            cmd_path = shutil.which(env_path)
            if cmd_path: return cmd_path
        elif os.path.exists(env_path):
            return env_path

    # 2. Check PATH as fallback
    lame_path = shutil.which("lame")
    if lame_path:
        return lame_path

    return None

def convert_wav_to_mp3(wav_filename, mp3_filename):
    lame_path = get_lame_path()
    if not lame_path:
        return False, "Lame encoder not found. Please install 'lame' (apt install lame)."

    if not os.path.isabs(mp3_filename): mp3_filename = os.path.abspath(mp3_filename)
    try:
        result = subprocess.run(
            [lame_path, "-S", wav_filename, mp3_filename],
            check=False, capture_output=True, text=True
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            return False, f"MP3 conversion failed: {stderr or f'exit code {result.returncode}'}"
        return True, "Success"
    except Exception as e:
        return False, f"Error during MP3 conversion: {e}"

def play_wav(wav_filename):
    """Play a WAV file. Returns (success, message, process_or_None)."""
    try:
        if os.name == 'nt':
            # Windows play wav
            import winsound
            winsound.PlaySound(wav_filename, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True, "Playing...", None
        else:
            # Linux play wav
            aplay_path = shutil.which("aplay")
            if aplay_path:
                proc = subprocess.Popen([aplay_path, "-q", "--", wav_filename])
                return True, "Playing...", proc
            return False, "aplay not found.", None
    except Exception as e:
        return False, f"Playback error: {e}", None

def stop_playback(proc):
    """Stop a running playback process."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
