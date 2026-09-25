import pyttsx3

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 190)
        
        voices = engine.getProperty("voices")
        if len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
            
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        # On a headless cloud server without audio drivers, just print the text silently!
        print(f"[Speech Silent Mode]: {text}")