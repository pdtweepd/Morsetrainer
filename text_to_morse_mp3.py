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
            
            raw_input = input("Enter Text (or type 'random' for practice groups): ")
            
            if raw_input.lower().strip() == 'random':
                count = int(input("How many groups of 5? [default 10]: ") or 10)
                m_type = input("Mode (letters/numbers/mixed/koch) [default mixed]: ").lower() or "mixed"
                level = 2
                if m_type == "koch":
                    level = int(input("Koch Level (1-40) [default 2]: ") or 2)
                text = morse_logic.generate_random_text(count, m_type, level)
            else:
                text = raw_input
            
            if not text:
                print("Text cannot be empty.")
                continue

            print(f"\nConfiguration:")
            print(f"- Text/Practice: '{text}'")
            print(f"- Character Speed: {char_speed} WPM")
            print(f"- Effective Speed: {eff_speed} WPM")
            
            confirm = input("\nExecute script? (yes/no): ").lower().strip()
            
            if confirm in ['yes', 'y']:
                tu, intra, char_g, word_g = morse_logic.calculate_timings(char_speed, eff_speed)
                output_filename = "morse.mp3"
                
                print(f"Generating Morse code...")
                temp_wav = morse_logic.generate_morse_wav(text, tu, char_g, word_g)
                
                success, message = morse_logic.convert_wav_to_mp3(temp_wav, output_filename)
                if success:
                    print(f"Successfully saved to {output_filename}")
                    if raw_input.lower().strip() == 'random':
                        print(f"ANSWER KEY: {text}")
                else:
                    print(f"Error: {message}")
                
                if temp_wav and os.path.exists(temp_wav):
                    os.remove(temp_wav)
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
