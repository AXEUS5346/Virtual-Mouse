import speech_recognition as sr
import pyautogui
import time
import threading

class SpeechController:
    def __init__(self):
        self.running = True
        self.recognizer = sr.Recognizer()
        
        # Dictionary for special keys and shortcuts
        self.special_keys = {
            "enter": "enter",
            "space": "space",
            "backspace": "backspace",
            "delete": "delete",
            "escape": "esc",
            "tab": "tab",
            "caps lock": "capslock",
            "shift": "shift",
            "control": "ctrl",
            "alt": "alt",
            "windows": "win",
            "command": "command",  # for Mac
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
        }

        # Add function keys
        for i in range(1, 13):
            self.special_keys[f"f{i}"] = f"f{i}"

    def start(self):
        self.thread = threading.Thread(target=self.speech_recognition)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def speech_recognition(self):
        with sr.Microphone() as source:
            print("Microphone connected. Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Speech recognition is active. Speak commands...")
            
            while self.running:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"Recognized: {text}")
                    self.process_speech_command(text)
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    print("Speech not recognized")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")

    def process_speech_command(self, command):
        if "type" in command:
            text_to_type = command.split("type ", 1)[1]
            pyautogui.write(text_to_type)
        elif "press" in command:
            key = command.split("press ", 1)[1]
            if key in self.special_keys:
                pyautogui.press(self.special_keys[key])
            else:
                pyautogui.press(key)
        elif "hold" in command:
            key = command.split("hold ", 1)[1]
            if key in self.special_keys:
                pyautogui.keyDown(self.special_keys[key])
        elif "release" in command:
            key = command.split("release ", 1)[1]
            if key in self.special_keys:
                pyautogui.keyUp(self.special_keys[key])
        elif "click" in command:
            pyautogui.click()
        elif "double click" in command:
            pyautogui.doubleClick()
        elif "right click" in command:
            pyautogui.rightClick()
        elif "scroll up" in command:
            pyautogui.scroll(300)
        elif "scroll down" in command:
            pyautogui.scroll(-300)
        elif "copy" in command:
            pyautogui.hotkey('ctrl', 'c')
        elif "paste" in command:
            pyautogui.hotkey('ctrl', 'v')
        elif "cut" in command:
            pyautogui.hotkey('ctrl', 'x')
        elif "undo" in command:
            pyautogui.hotkey('ctrl', 'z')
        elif "redo" in command:
            pyautogui.hotkey('ctrl', 'y')
        elif "select all" in command:
            pyautogui.hotkey('ctrl', 'a')
        elif "save" in command:
            pyautogui.hotkey('ctrl', 's')
        elif "find" in command:
            pyautogui.hotkey('ctrl', 'f')
        elif "new tab" in command:
            pyautogui.hotkey('ctrl', 't')
        elif "close tab" in command:
            pyautogui.hotkey('ctrl', 'w')
        elif "switch tab" in command:
            pyautogui.hotkey('ctrl', 'tab')
        elif "stop" in command or "exit" in command:
            self.running = False

def main():
    print("Voice-controlled keyboard started. Say 'stop' or 'exit' to quit.")
    controller = SpeechController()
    controller.start()
    
    try:
        while controller.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        print("Voice-controlled keyboard stopped.")

if __name__ == "__main__":
    main()