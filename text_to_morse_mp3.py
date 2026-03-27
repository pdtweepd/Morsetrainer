import sys
import os
import morse_logic

VERSION = morse_logic.VERSION

def check_dependencies():
    lame_path = morse_logic.get_lame_path()
    if not lame_path:
        print("\nMissing dependency: 'lame' (MP3 encoder) not found.")
        print("Installation instructions:")
        if os.name == 'nt':
            print("- Windows: Download lame.exe and add it to your PATH.")
        else:
            print("- Linux: Run 'sudo apt install lame'")
            print("- macOS: Run 'brew install lame'")
        return False
    return True

if __name__ == "__main__":
    if not check_dependencies():
        print("\nPlease install the required dependencies to continue.")
        sys.exit(1)

    while True:
        try:
            print(f"\n--- Morse Code MP3 Generator (Training Edition) v{VERSION} ---")
            char_speed = float(input("Enter Character Speed (WPM) [default 12]: ") or 12)
            eff_speed = float(input("Enter Effective Word Speed (WPM) [default 5]: ") or 5)
            frequency = float(input("Enter Frequency (Hz) [default 650]: ") or 650)
            frequency = max(200.0, min(4000.0, frequency))

            raw_input = input("Enter Text (or type 'random' for practice groups): ")

            if raw_input.lower().strip() == 'random':
                count = max(1, int(input("How many groups of 5? [default 10]: ") or 10))
                m_type = input("Mode (letters/numbers/punctuation/mixed/koch) [default mixed]: ").lower() or "mixed"
                level = 2
                if m_type == "koch":
                    level = max(2, min(40, int(input("Koch Level (2-40) [default 2]: ") or 2)))
                text = morse_logic.generate_random_text(count, m_type, level)
            else:
                text = raw_input

            if not text:
                print("Text cannot be empty.")
                continue

            output_filename = input("Output filename [default morse.mp3]: ").strip() or "morse.mp3"
            if not output_filename.endswith(".mp3"):
                output_filename += ".mp3"

            voice = input("Include voice answer key? (yes/no) [default no]: ").lower().strip()
            include_voice = voice in ['yes', 'y']

            print(f"\nConfiguration:")
            print(f"- Text/Practice: '{text}'")
            print(f"- Character Speed: {char_speed} WPM")
            print(f"- Effective Speed: {eff_speed} WPM")
            print(f"- Frequency: {frequency} Hz")
            print(f"- Output: {output_filename}")
            print(f"- Voice: {'yes' if include_voice else 'no'}")

            confirm = input("\nExecute script? (yes/no): ").lower().strip()

            if confirm in ['yes', 'y']:
                tu, _, char_g, word_g = morse_logic.calculate_timings(char_speed, eff_speed)
                morse_wav = None
                voice_wav = None
                combined_wav = None
                try:
                    print("Generating Morse code...")
                    morse_wav = morse_logic.generate_morse_wav(text, tu, char_g, word_g, frequency)

                    final_wav = morse_wav
                    if include_voice:
                        print("Generating voice...")
                        voice_wav = morse_logic.generate_voice_wav(text)
                        if voice_wav:
                            combined_wav = morse_logic.combine_wavs([morse_wav, voice_wav])
                            if combined_wav:
                                final_wav = combined_wav
                        else:
                            print("Warning: TTS not available, skipping voice.")

                    success, message = morse_logic.convert_wav_to_mp3(final_wav, output_filename)
                    if success:
                        print(f"Successfully saved to {output_filename}")
                        if raw_input.lower().strip() == 'random':
                            print(f"ANSWER KEY: {text}")
                    else:
                        print(f"Error: {message}")
                finally:
                    for f in filter(None, [morse_wav, voice_wav, combined_wav]):
                        try:
                            if os.path.exists(f):
                                os.remove(f)
                        except OSError:
                            pass
                break
            else:
                print("Restarting configuration...\n")

        except ValueError as e:
            print(f"Invalid input: {e}")
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
