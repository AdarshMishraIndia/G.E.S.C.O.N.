import speech_recognition as sr
import pyautogui
import tkinter as tk

# Initialize the recognizer
recognizer = sr.Recognizer()

def create_status_window(message):
    """Create a small status window with the given message."""
    status_window = tk.Toplevel()
    status_window.title("Status")
    status_window.geometry("250x100")  # Size of the window
    status_window.attributes("-topmost", True)  # Keep it on top of other windows
    status_window.overrideredirect(True)  # Remove title bar

    label = tk.Label(status_window, text=message, font=("Arial", 14))
    label.pack(expand=True)

    # Position the window at the center of the screen
    screen_width = status_window.winfo_screenwidth()
    screen_height = status_window.winfo_screenheight()
    x = (screen_width // 2) - (250 // 2)
    y = (screen_height // 2) - (100 // 2)
    status_window.geometry(f"+{x}+{y}")

    return status_window

def listen_for_speech():
    """Listen for speech from the microphone and return the recognized text."""
    with sr.Microphone() as source:
        print("Listening for input...")
        
        # Create status window indicating waiting for input
        status_window = create_status_window("Waiting for voice input...")
        status_window.update()  # Refresh the window to show the message

        try:
            # Listen for speech with a timeout and phrase time limit
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)  # Wait max 5 sec for speech
        except sr.WaitTimeoutError:
            print("No speech detected within the time limit")
            status_window.destroy()
            return None

        status_window.destroy()  # Close the status window after capturing audio

        try:
            # Recognize the speech using Google Web Speech API
            text = recognizer.recognize_google(audio)
            print(f"Recognized Text: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError:
            print("Error with the recognition service")
            return None

def main():
    """Main function to listen for speech and write the recognized text."""
    root = tk.Tk()
    root.withdraw()  # Hide the root Tkinter window
    recognized_text = listen_for_speech()
    
    if recognized_text:
        print(f"Typing: {recognized_text}")
        pyautogui.write(recognized_text)  # Simulate typing the recognized text
    else:
        print("No valid text recognized to write.")

if __name__ == "__main__":
    main()
