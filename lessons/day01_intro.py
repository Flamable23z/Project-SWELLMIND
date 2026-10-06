import sys
import time 
import random 
import requests
import threading
from datetime import datetime 
from memory import load_memory, save_memory
from speech import speak

# Load saved user settings (like name and favourite colour) from memory.json
memory = load_memory()
colours = ["blue", "red", "green", "yellow", "orange", "pink", "purple"]
running = True 
hour = datetime.now().hour

# Helper function to fetch and evaluate marine forecast data for a single beach
def check_single_beach(lat, lon, min_wind, max_wind, is_or_range, beach_name, max_wind_speed=22):
    # Open-Meteo API endpoint for marine weather
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["wave_height", "wave_period", "wind_speed_10m", "wind_direction_10m", "sea_surface_temperature"],
        "timezone": "Africa/Johannesburg"
    }
    
    try:
        # Fetch weather data from API and convert response to JSON dictionary
        response = requests.get(url, params=params)
        data = response.json()
        
        # Index 6 corresponds to 06:00 AM forecast in the hourly data array
        height = data["hourly"]["wave_height"][6]
        period = data["hourly"]["wave_period"][6]
        wind = data["hourly"]["wind_speed_10m"][6]
        wind_dir = data["hourly"]["wind_direction_10m"][6]
        temp = data["hourly"]["sea_surface_temperature"][6]
        
        # Defensive programming: set default fallbacks if API returns None values
        if wind is None: wind = 0
        if wind_dir is None: wind_dir = 0
        if temp is None: temp = 15
        
        # Offshore wind check:
        # Muizenberg (315° to 45°) wraps past 0° North, so it needs an 'OR' check.
        # Llandudno (112° to 157°) is a normal range, so it uses an 'AND' check.
        if is_or_range:
            is_offshore = (wind_dir >= min_wind or wind_dir <= max_wind)
        else:
            is_offshore = (min_wind <= wind_dir <= max_wind)
            
        # Overall boolean check: surf is good if waves are high enough, period is long, wind is light & offshore
        is_good = (height >= 0.8 and period >= 7.0 and wind < max_wind_speed and is_offshore)
        
        stats = f"{beach_name.capitalize()}: {height}m ({period}s) | Wind: {wind}km/h ({wind_dir}°) | Water: {temp}°C"
        return is_good, stats
        
    except Exception as e:
        # Error handling so a network failure doesn't crash the entire program
        print(f"Error checking {beach_name}: {e}")
        return False, f"{beach_name.capitalize()}: Data unavailable"

# Main function to check both beaches and send reports
def check_surf():
    print("Swellmind: Checking Muizenberg and Llandudno forecasts...")
    speak("Checking surf conditions for both Muizenberg and Llandudno.")
    
    # Muizenberg: NW to NE offshore wind (max 22 km/h)
    muiz_good, muiz_stats = check_single_beach(-34.1081, 18.4719, 315, 45, True, "muizenberg")
    
    # Llandudno: SE offshore wind (can handle up to 30 km/h)
    llan_good, llan_stats = check_single_beach(-34.0083, 18.3383, 112, 157, False, "llandudno", 30)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Decision tree: decide report message based on which spot is surfable
    if muiz_good and llan_good:
        status = "BOTH GOOD"
        msg = f"Surf's UP everywhere! Both spots are firing.\n{muiz_stats}\n{llan_stats}\nSet alarm for 5:30 AM!"
        speak("Great news! Both Muizenberg and Llandudno have good waves tomorrow morning.")
    elif muiz_good:
        status = "MUIZENBERG GOOD"
        msg = f"Surf's UP at Muizenberg! {muiz_stats}. Set alarm for 5:30 AM!"
        speak("Muizenberg is looking good! Wind is offshore on the False Bay side.")
    elif llan_good:
        status = "LLANDUDNO GOOD"
        msg = f"Surf's UP at Llandudno! {llan_stats}. Set alarm for 5:30 AM!"
        speak("Llandudno is looking good! South East wind is clean on the Atlantic side.")
    else:
        status = "SLEEP IN"
        msg = f"Neither beach is ideal.\n{muiz_stats}\n{llan_stats}"
        speak("Conditions aren't ideal at either beach tomorrow. Sleep in!")
        
    print(f"\nSwellmind Report:\n{msg}")
    
    # Trigger push notification to ntfy app if surf is good
    if muiz_good or llan_good:
        try:
            requests.post(
                "https://ntfy.sh/muizenberg_surf_benjy",
                data=msg.encode("utf-8")
            )
        except Exception as e:
            print(f"Could not send ntfy notification: {e}")

    # Log the report result to a text file for history tracking
    log_entry = f"[{timestamp}] Result: {status}\n  -> {muiz_stats}\n  -> {llan_stats}\n"
    with open("surf_history.txt", "a", encoding="utf-8", errors="replace") as file:
        file.write(log_entry)

# Background loop for local desktop auto-checks (runs every hour)
def auto_check_loop():
    while True:
        time.sleep(3600) # Sleep for 3600 seconds = 1 hour
        print("\n[Swellmind Auto-Check]: Running background hourly forecast check...")
        check_surf()

# If GitHub Actions runs the script with '--cron', check surf and exit immediately (headless mode)
if "--cron" in sys.argv:
    print("Swellmind running in automated Cloud Mode...")
    check_surf()
    sys.exit()  

# If running locally on laptop, start background thread for hourly checks
surf_thread = threading.Thread(target=auto_check_loop, daemon=True)
surf_thread.start()

# Greet user based on time of day and remembered name
def greet_user():
    if "name" in memory:
        user_name = memory['name']
        if hour < 12:
            greeting = f"Good morning {user_name}."
        elif hour < 18:
            greeting = f"Good afternoon {user_name}."
        else:
            greeting = f"Good evening {user_name}."
            
        print(greeting)
        speak(f"{greeting} What can I help you with today?")
    else:
        name = input("What is your name? ")
        memory["name"] = name 
        save_memory(memory)
        
        if hour < 12:
            greeting = f"Good morning {name}. It is a pleasure to meet you."
        elif hour < 18:
            greeting = f"Good afternoon {name}. It is a pleasure to meet you."
        else:
            greeting = f"Good evening {name}. It is a pleasure to meet you."
            
        print(greeting)
        speak(greeting)

greet_user()

# Main interactive command loop for local laptop terminal
while running:
    askcommand = input("\nWhat can I help you with today? ").lower().strip()
    
    if askcommand in ["goodbye", "bye", "exit", "quit"]:
        speak("Goodbye!")
        print("Goodbye!")
        running = False
        
    elif "surf" in askcommand or "swell" in askcommand or "waves" in askcommand:
        check_surf()
        
    elif "history" in askcommand or "log" in askcommand:
        try:
            with open("surf_history.txt", "r", encoding="utf-8", errors="replace") as file:
                history = file.read()
                print("\n--- SURF HISTORY LOG ---")
                print(history)
        except FileNotFoundError:
            print("Swellmind: No surf history found yet. Check the surf first!")
            
    elif "name" in askcommand and "my" in askcommand:
        response = f"Your name is {memory.get('name', 'unknown')}."
        print(response)
        speak(response)
        
    elif "name" in askcommand and "your" in askcommand:
        print("My name is Swellmind.")
        speak("My name is Swellmind.")
        
    elif "favourite" in askcommand and "colour" in askcommand and "your" in askcommand:
        if "Swellmindfavouritecolour" not in memory:
            memory["Swellmindfavouritecolour"] = random.choice(colours)
            save_memory(memory)
        response = f"My favourite colour is {memory['Swellmindfavouritecolour']}."
        print(response)
        speak(response)
        
    elif "favourite" in askcommand and "colour" in askcommand and "my" in askcommand:
        if "favouritecolour" in memory:
            response = f"Your favourite colour is {memory['favouritecolour']}."
            print(response)
            speak(response)
        else:
            favouritecolour = input("I'm not sure. What is your favourite colour? ").lower()
            memory["favouritecolour"] = favouritecolour
            save_memory(memory)
            response = f"Now I know your favourite colour is {favouritecolour}."
            print(response)
            speak(response)
            
    elif "time" in askcommand:
        current_time = datetime.now().strftime("%I:%M %p")
        print(current_time)
        speak(f"The time is {current_time}")
        
    elif askcommand == "new user":
        memory.pop("name", None)
        name = input("What is your name? ")
        memory["name"] = name 
        save_memory(memory)
        print(f"Hello {name}, memory updated.")
        speak(f"Hello {name}, memory updated.")