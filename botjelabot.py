#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEARTWOOD MINING BOT - v4.2 (LDPlayer 9 - Click-based Joystick & Action)
Cotton detected → Calculate distance → Click joystick → Drag in direction → Stop at distance 0 → Click gather icon
Using ADB tap + drag for joystick, and click coordinates for action buttons
"""

import os
import sys
import cv2
import glob
import time
import requests
import threading
import numpy as np
import tkinter as tk
import pyautogui
import pygetwindow as gw
import subprocess
from datetime import datetime
from tkinter import PhotoImage

# Try different keyboard libraries
try:
    import pydirectinput as pdi
    USE_PYDIRECTINPUT = True
    print("✅ Using PyDirectInput for keyboard")
except ImportError:
    USE_PYDIRECTINPUT = False
    print("⚠️  PyDirectInput not available, using pyautogui")

try:
    import keyboard
    USE_KEYBOARD_LIB = True
    print("✅ Using keyboard library")
except ImportError:
    USE_KEYBOARD_LIB = False

# GLOBAL
global Lilian, movement_active, stop_movement_flag, current_target, adb_device
full_counter = 0
lifted_cotton = 0
movement_active = False
stop_movement_flag = False
current_target = None
adb_device = None

# CONFIG
WINDOW_TITLE = 'LDPlayer'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ⭐ JOYSTICK POSITION (LDPLAYER GAME COORDINATES)
JOYSTICK_CENTER_X = 130      # X dalam game area
JOYSTICK_CENTER_Y = 550      # Y dalam game area
JOYSTICK_PUSH_RADIUS = 70    # Push radius untuk joystick

# ⭐ ACTION/GATHER BUTTON POSITION
# Tentukan koordinat icon gather di LDPlayer
GATHER_BUTTON_X = 380        # UBAH SESUAI POSISI ICON GATHER DI GAME ANDA
GATHER_BUTTON_Y = 540        # UBAH SESUAI POSISI ICON GATHER DI GAME ANDA

# ⭐ ADB DRAG PARAMETERS
DRAG_DURATION_MS = 500       # Duration of drag in milliseconds
TRACKING_UPDATE_INTERVAL = 0.02
DISTANCE_THRESHOLD = 20      # Stop when distance <= 20px (lebih toleran)
DIRECTION_RECALC_INTERVAL = 0.15  # Recalculate direction every 150ms
HARVEST_COMPLETE_MIN_TIME = 3

harvest_block_until = None

def asset_path(*parts):
    return os.path.join(BASE_DIR, *parts)

# Templates
MINING_TEMPLATE = asset_path('MISC', 'mining', 'Capture.JPG')
CHOP_TEMPLATE = asset_path('MISC', 'mining', 'chop.jpg')
MINE_TEMPLATE = asset_path('MISC', 'mining', 'mine.jpg')
PICKUP_TEMPLATE = asset_path('MISC', 'mining', 'pickup.jpg')
DIED_TEMPLATE = asset_path('MISC', 'game', 'died.JPG')
TOWN_TEMPLATE = asset_path('MISC', 'game', 'town.JPG')
COTTON_ONGROUND_TEMPLATE = asset_path('MISC', 'mining', 'storage', 'cotton_onground.jpg')
COTTON_FOLDER = asset_path('MISC', 'mining', 'cotton')

# Thresholds
THRESHOLD_MINING_ACTION = 0.73
THRESHOLD_COTTON_DETECTION = 0.78
THRESHOLD_MISC = 0.5
MAX_DISTANCE_TO_COTTON = 450
DIRECTION_AXIS_DEADZONE = 1

# ============ ADB FUNCTIONS ============

def init_adb():
    """Initialize ADB connection to LDPlayer"""
    global adb_device
    try:
        # Try to connect to LDPlayer default port
        result = subprocess.run(['adb', 'connect', 'localhost:5555'], 
                              capture_output=True, text=True, timeout=5)
        print(f"✅ ADB connect result: {result.stdout.strip()}")
        
        # Verify connection
        result = subprocess.run(['adb', 'devices'], 
                              capture_output=True, text=True, timeout=5)
        
        if 'localhost:5555' in result.stdout or '127.0.0.1:5555' in result.stdout:
            adb_device = 'localhost:5555'
            print(f"✅ Connected to ADB device: {adb_device}")
            return True
        else:
            print("⚠️  No ADB devices found. Make sure LDPlayer has ADB enabled.")
            return False
            
    except FileNotFoundError:
        print("❌ ADB not found in PATH. Install Android SDK Platform Tools.")
        return False
    except Exception as e:
        print(f"❌ ADB init failed: {e}")
        return False

def adb_shell(command):
    """Execute ADB shell command"""
    global adb_device
    if not adb_device:
        return None
    try:
        result = subprocess.run(['adb', '-s', adb_device, 'shell', command],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️  ADB command failed: {e}")
        return None

def adb_drag_joystick(direction_x, direction_y, duration_ms=500):
    """
    Drag joystick using ADB tap and drag
    Joystick di LDPlayer memerlukan: tap di center, lalu drag ke arah target
    
    Args:
        direction_x, direction_y: Direction vector (will be normalized)
        duration_ms: Duration of drag in milliseconds
    """
    global adb_device
    if not adb_device:
        return False
    
    try:
        # Normalize direction
        mag = np.sqrt(direction_x**2 + direction_y**2)
        if mag < DIRECTION_AXIS_DEADZONE:
            return False
        
        norm_x = direction_x / mag
        norm_y = direction_y / mag
        
        # Calculate push distance
        push_dist = min(mag * 0.4, JOYSTICK_PUSH_RADIUS)
        
        # Calculate target position
        target_x = int(JOYSTICK_CENTER_X + (norm_x * push_dist))
        target_y = int(JOYSTICK_CENTER_Y + (norm_y * push_dist))
        
        direction_str = ""
        if abs(norm_x) > abs(norm_y):
            direction_str = "←" if norm_x < 0 else "→"
        else:
            direction_str = "↑" if norm_y < 0 else "↓"
        
        print(f'🎮 {direction_str} ADB Drag: ({JOYSTICK_CENTER_X},{JOYSTICK_CENTER_Y}) → ({target_x},{target_y}) dur={duration_ms}ms')
        
        # Execute drag: input touchscreen swipe = drag
        cmd = f"input touchscreen swipe {JOYSTICK_CENTER_X} {JOYSTICK_CENTER_Y} {target_x} {target_y} {duration_ms}"
        
        subprocess.run(['adb', '-s', adb_device, 'shell', cmd],
                      capture_output=True, text=True, timeout=10)
        
        # Wait for drag to complete
        time.sleep(duration_ms / 1000.0 + 0.1)
        
        return True
        
    except Exception as e:
        print(f"❌ Joystick drag failed: {e}")
        return False

def adb_tap(x, y):
    """
    Tap at coordinates using ADB
    """
    global adb_device
    if not adb_device:
        return False
    
    try:
        cmd = f"input touchscreen tap {x} {y}"
        subprocess.run(['adb', '-s', adb_device, 'shell', cmd],
                      capture_output=True, text=True, timeout=5)
        return True
    except Exception as e:
        print(f"❌ Tap failed: {e}")
        return False

# ============ TEMPLATE MATCHING FUNCTIONS ============

def find_harvest_prompt(screenshot):
    """Find prompt and return (name, confidence)"""
    prompts = [
        ('gather', MINING_TEMPLATE, THRESHOLD_MINING_ACTION),
        ('chop', CHOP_TEMPLATE, THRESHOLD_MINING_ACTION),
        ('mine', MINE_TEMPLATE, THRESHOLD_MINING_ACTION),
        ('pickup', PICKUP_TEMPLATE, THRESHOLD_MINING_ACTION),
    ]
    best = None
    for name, path, threshold in prompts:
        if not os.path.exists(path):
            continue
        try:
            template = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if template is None:
                continue
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if template.ndim == 3 else template
            img_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) if screenshot.ndim == 3 else screenshot
            res = cv2.matchTemplate(img_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
            _, conf, _, _ = cv2.minMaxLoc(res)
            if conf >= threshold and (best is None or conf > best[1]):
                best = (name, float(conf))
        except:
            pass
    return best

def find_template_candidates(screenshot, template, threshold):
    """Find all matches >= threshold"""
    try:
        search_img = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) if screenshot.ndim == 3 else screenshot
        tpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if template.ndim == 3 else template
        result = cv2.matchTemplate(search_img, tpl, cv2.TM_CCOEFF_NORMED)
        peak_map = cv2.dilate(result, np.ones((21, 21), dtype=np.uint8))
        peak_y, peak_x = np.where((result >= threshold) & (result == peak_map))
        h, w = tpl.shape[:2]
        candidates = []
        for x, y in zip(peak_x, peak_y):
            center = (int(x + w // 2), int(y + h // 2))
            candidates.append((float(result[y, x]), (int(x), int(y)), center))
        return candidates
    except:
        return []

def find_locked_target(screenshot, target_lock):
    """Find locked target in current screenshot"""
    try:
        template = cv2.imread(target_lock['template_path'], cv2.IMREAD_UNCHANGED)
        if template is None:
            return None
        candidates = find_template_candidates(screenshot, template, THRESHOLD_COTTON_DETECTION)
        if not candidates:
            return None
        px, py = target_lock['last_center']
        conf, tl, center = min(candidates, key=lambda m: ((m[2][0]-px)**2 + (m[2][1]-py)**2))
        return template, conf, tl, center
    except:
        return None

def calculate_distance(p1, p2):
    """Calculate distance between two points"""
    return np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

# ============ BOT MAIN LOOP ============

def create_bot(window_title):
    """Main bot loop with ADB drag joystick and tap gather"""
    global Lilian, lifted_cotton, harvest_block_until, movement_active, current_target
    
    try:
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            print(f"❌ Window not found")
            stop_function()
            return
        
        target_window = windows[0]
        game_w = target_window.width
        game_h = target_window.height
        char_x = game_w // 2
        char_y = game_h // 2

        print(f"✅ Window: {target_window.title}")
        print(f"📏 Game resolution: {game_w}x{game_h}")
        print(f"👤 Character center: ({char_x}, {char_y})")
        print(f"🎮 Joystick center: ({JOYSTICK_CENTER_X}, {JOYSTICK_CENTER_Y})")
        print(f"📍 Distance Threshold: {DISTANCE_THRESHOLD}px")
        print(f"⏱️  Drag Duration: {DRAG_DURATION_MS}ms")
        print(f"🖱️  Gather button: ({GATHER_BUTTON_X}, {GATHER_BUTTON_Y})")

        while not target_window.isActive:
            print("⏳ Waiting for window to be active...")
            time.sleep(0.5)

        print("✅ Bot started!")

        iteration = 0
        locked_target = None
        harvesting = False
        harvest_start = 0.0
        last_direction_update = time.time()

        while True:
            iteration += 1
            if not Lilian:
                print("🛑 Stopped")
                break

            while not target_window.isActive:
                time.sleep(0.1)

            try:
                ss = pyautogui.screenshot()
                ss = np.array(ss)
                ss = cv2.cvtColor(ss, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"❌ Screenshot: {e}")
                continue

            try:
                now = time.monotonic()
                
                # Check for gather prompt
                prompt = find_harvest_prompt(ss)
                
                if prompt and prompt[0] == 'gather' and not harvesting and not movement_active:
                    print(f"🌾 Gather found! Clicking gather button at ({GATHER_BUTTON_X}, {GATHER_BUTTON_Y})")
                    harvesting = True
                    harvest_start = now
                    harvest_block_until = now + HARVEST_COMPLETE_MIN_TIME
                    
                    # Click gather button
                    tapped = adb_tap(GATHER_BUTTON_X, GATHER_BUTTON_Y)
                    if tapped:
                        lifted_cotton += 1
                        if 'label_lifted_cotton' in globals():
                            label_lifted_cotton.config(text=f'🌾 Cotton: {lifted_cotton}')
                        print(f"✅ Gathering... wait {HARVEST_COMPLETE_MIN_TIME}s")
                        time.sleep(HARVEST_COMPLETE_MIN_TIME)
                        harvesting = False
                        locked_target = None
                        current_target = None
                        continue
                    else:
                        print("⚠️ Gather click failed")
                        harvesting = False

                # If harvesting, wait until complete
                if harvesting:
                    if now - harvest_start >= HARVEST_COMPLETE_MIN_TIME:
                        print("✅ Harvest complete")
                        harvesting = False
                        locked_target = None
                        current_target = None

                # Scan for cotton if not harvesting and no target
                if not harvesting and locked_target is None and not movement_active:
                    if os.path.isdir(COTTON_FOLDER):
                        try:
                            entries = os.listdir(COTTON_FOLDER)
                            paths = [os.path.join(COTTON_FOLDER, f) for f in entries 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                        except:
                            paths = []
                    else:
                        paths = []

                    if len(paths) > 0:
                        print(f"🔎 Scanning {len(paths)} templates")

                        nearest = None
                        for path in paths:
                            try:
                                tpl = cv2.imread(path)
                                if tpl is None:
                                    continue
                                h, w = tpl.shape[:2]
                                if h < 6 or w < 6:
                                    continue
                                for conf, tl, center in find_template_candidates(ss, tpl, THRESHOLD_COTTON_DETECTION):
                                    dist = calculate_distance((char_x, char_y), center)
                                    if dist <= MAX_DISTANCE_TO_COTTON and (nearest is None or dist < nearest[4]):
                                        nearest = (path, conf, tpl, tl, dist, center)
                            except:
                                pass

                        if nearest:
                            path, conf, tpl, tl, dist, center = nearest
                            locked_target = {
                                'template_path': path,
                                'last_center': center,
                                'last_distance': dist,
                            }
                            current_target = center
                            print(f"🔒 Target locked! Dist={dist:.0f}px, Conf={conf:.2f}")

                # === ADB DRAG JOYSTICK PURSUIT ===
                if not harvesting and locked_target and not movement_active:
                    match = find_locked_target(ss, locked_target)
                    if match is None:
                        print("⌛ Target lost, scanning again...")
                        locked_target = None
                        current_target = None
                    else:
                        tpl, conf, tl, target_center = match
                        locked_target['last_center'] = target_center
                        current_target = target_center
                        dist = calculate_distance((char_x, char_y), target_center)

                        if dist <= DISTANCE_THRESHOLD:
                            print(f"✅ REACHED TARGET! Dist={dist:.0f}px - Waiting for gather prompt...")
                            locked_target = None
                            current_target = None
                        elif now - last_direction_update >= DIRECTION_RECALC_INTERVAL:
                            # Calculate direction to target
                            last_direction_update = now
                            dx = target_center[0] - char_x
                            dy = target_center[1] - char_y
                            
                            # Execute drag
                            movement_active = True
                            adb_drag_joystick(dx, dy, DRAG_DURATION_MS)
                            movement_active = False
                            
                            print(f"  📍 Distance: {dist:.0f}px | Dir: ({dx:.0f}, {dy:.0f})")

                try:
                    display_image(ss)
                except:
                    pass

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

            time.sleep(0.05)  # Main loop: 50ms

    except Exception as e:
        print(f"❌ Fatal: {e}")
        import traceback
        traceback.print_exc()
        stop_function()

# ============ UI FUNCTIONS ============

class RedirectText:
    def __init__(self, tw):
        self.tw = tw
    
    def write(self, s):
        ts = datetime.now().strftime("[%H:%M:%S]")
        for line in s.split('\n'):
            if line:
                self.tw.insert(tk.END, f"{ts} {line}\n")
        self.tw.see(tk.END)
    
    def flush(self):
        pass

def display_image(ss):
    """Display screenshot in GUI"""
    try:
        if ss is None:
            return
        h, w, _ = ss.shape
        new_w = min(300, w)
        new_h = min(200, int(new_w * h / w))
        resized = cv2.resize(ss, (new_w, new_h))
        ret, buf = cv2.imencode('.ppm', resized)
        photo = PhotoImage(data=buf.tobytes())
        image_label.config(image=photo)
        image_label.image = photo
    except:
        pass

def test_input():
    """Test ADB drag and tap"""
    print("\n" + "="*60)
    print("🧪 TEST ADB DRAG & TAP")
    print("="*60)
    
    if not adb_device:
        print("❌ ADB not connected!")
        return
    
    print(f"✅ ADB Device: {adb_device}")
    print(f"✅ Joystick: ({JOYSTICK_CENTER_X}, {JOYSTICK_CENTER_Y})")
    print(f"✅ Gather button: ({GATHER_BUTTON_X}, {GATHER_BUTTON_Y})")
    print(f"✅ Drag Duration: {DRAG_DURATION_MS}ms")
    print(f"⏳ Wait 3 seconds before testing...\n")
    time.sleep(3)
    
    print("➡️  Testing 8 directions via ADB drag...")
    directions = [
        (0, -200, "UP"),
        (200, -200, "UP-RIGHT"),
        (200, 0, "RIGHT"),
        (200, 200, "DOWN-RIGHT"),
        (0, 200, "DOWN"),
        (-200, 200, "DOWN-LEFT"),
        (-200, 0, "LEFT"),
        (-200, -200, "UP-LEFT"),
    ]
    
    for dx, dy, name in directions:
        print(f"   {name}")
        adb_drag_joystick(dx, dy, DRAG_DURATION_MS)
        time.sleep(0.2)
    
    print("\n➡️  Testing GATHER TAP...")
    time.sleep(1)
    adb_tap(GATHER_BUTTON_X, GATHER_BUTTON_Y)
    
    print("\n✅ Test complete!")
    print("="*60 + "\n")

def start_function():
    """Start bot"""
    global Lilian
    if not adb_device:
        print("❌ ADB not connected! Cannot start bot.")
        print("   Make sure LDPlayer is running and ADB port 5555 is open.")
        return
    
    print("▶️  STARTING BOT v4.2 (ADB DRAG & TAP)")
    print("🎮 Using ADB drag for joystick movement")
    print("🖱️  Using ADB tap for gather action")
    print("💡 Make sure LDPlayer window is active")
    Lilian = True
    threading.Thread(target=create_bot, args=(WINDOW_TITLE,), daemon=True).start()
    start_button["state"] = "disabled"
    stop_button["state"] = "normal"

def stop_function():
    """Stop bot"""
    global Lilian
    print("⏹️  STOPPING BOT")
    Lilian = False
    start_button["state"] = "normal"
    stop_button["state"] = "disabled"

# ============ MAIN ============

if __name__ == "__main__":
    Lilian = False
    
    # Initialize ADB
    print("\n" + "="*60)
    print("🎮 HEARTWOOD BOT v4.2 - ADB DRAG & TAP")
    print("="*60)
    print("\n🔌 Initializing ADB connection...\n")
    
    if not init_adb():
        print("\n⚠️  ADB initialization failed!")
        print("\nSetup instructions:")
        print("1. Download Android SDK Platform Tools:")
        print("   https://developer.android.com/studio/command-line/adb")
        print("")
        print("2. Add to PATH or run from same directory")
        print("")
        print("3. Open LDPlayer and enable ADB:")
        print("   Settings → Advanced → Enable ADB")
        print("")
        print("4. Make sure LDPlayer is running before starting bot")
        print("\n" + "="*60 + "\n")
    
    root = tk.Tk()
    root.title("🎮 Heartwood Bot v4.2 (ADB Drag & Tap)")
    root.geometry("305x700+0+0")
    root.attributes("-topmost", True)
    root.wm_attributes('-toolwindow', 1)
    root.configure(bg='#2b2b2b')

    # Console output
    console = tk.Text(root, wrap=tk.WORD, height=14, width=35,
                      bg='#1e1e1e', fg='#00ff00', font=('Courier', 8))
    console.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
    sys.stdout = RedirectText(console)

    # Start button
    start_button = tk.Button(root, text="▶️  START", command=start_function,
                             fg="white", bg="#00aa00", font=('Arial', 10, 'bold'))
    start_button.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

    # Stop button
    stop_button = tk.Button(root, text="⏹️  STOP", command=stop_function,
                            fg="white", bg="#aa0000", font=('Arial', 10, 'bold'))
    stop_button.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    # Test button
    test_button = tk.Button(root, text="🧪 TEST INPUT", command=test_input,
                            fg="white", bg="#0099cc", font=('Arial', 8))
    test_button.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky='ew')

    # Image display
    image_label = tk.Label(root, bg='#1e1e1e', height=8)
    image_label.grid(row=3, column=0, columnspan=2, padx=0, pady=5, sticky='ew')

    # Cotton counter
    label_lifted_cotton = tk.Label(root, text="🌾 Cotton: 0", fg="#00ff00", bg='#2b2b2b',
                                   font=('Arial', 12, 'bold'))
    label_lifted_cotton.grid(row=0, column=0, columnspan=2, padx=0, pady=5)

    # Info
    print('╔════════════════════════════════════╗')
    print('║  🎮 HEARTWOOD BOT v4.2            ║')
    print('║  ADB Drag & Tap Mode               ║')
    print('║  Click-based Joystick & Action     ║')
    print('╚════════════════════════════════════╝')
    print('')
    print('🎮 ADB Drag & Tap Features:')
    print('  • ADB tap + drag for joystick')
    print('  • ADB tap for gather action')
    print('  • No keyboard input needed')
    print('  • Direct touch event injection')
    print('  • Works with LDPlayer joystick')
    print('')
    print('⚠️  IMPORTANT CONFIGURATION:')
    print('  You MUST set the correct coordinates:')
    print(f'  • GATHER_BUTTON_X = {GATHER_BUTTON_X}')
    print(f'  • GATHER_BUTTON_Y = {GATHER_BUTTON_Y}')
    print('')
    print('  To find coordinates:')
    print('  1. Take a screenshot of your game')
    print('  2. Find the icon/button to gather')
    print('  3. Note the X, Y coordinates')
    print('  4. Update the values in script')
    print('')
    print('Configuration:')
    print(f'  • Joystick Center: ({JOYSTICK_CENTER_X}, {JOYSTICK_CENTER_Y})')
    print(f'  • Drag Duration: {DRAG_DURATION_MS}ms')
    print(f'  • Distance Threshold: {DISTANCE_THRESHOLD}px')
    print(f'  • Direction Update: {DIRECTION_RECALC_INTERVAL*1000:.0f}ms')
    print(f'  • Push Radius: {JOYSTICK_PUSH_RADIUS}px')
    print('')
    print('ADB Commands Used:')
    print('  • Drag: input touchscreen swipe X1 Y1 X2 Y2 DURATION')
    print('  • Tap: input touchscreen tap X Y')
    print('')
    print('Instructions:')
    print('  1. Find the gather button coordinates in your game')
    print('  2. Update GATHER_BUTTON_X and GATHER_BUTTON_Y')
    print('  3. Make sure LDPlayer is running')
    print('  4. Click "🧪 TEST INPUT" to verify ADB')
    print('  5. Click "▶️  START" to begin farming')
    print('')

    stop_button["state"] = "disabled"
    root.mainloop()
