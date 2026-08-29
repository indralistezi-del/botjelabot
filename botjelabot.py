#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEARTWOOD MINING BOT - v4.6 (AUTO DEVICE DETECTION)
CRITICAL FIX: Auto detect correct ADB device (emulator-5554, localhost:5555, etc)
"""

import os
import sys
import cv2
import time
import threading
import numpy as np
import tkinter as tk
import pyautogui
import pygetwindow as gw
import subprocess
import shutil
from datetime import datetime
from tkinter import PhotoImage

# GLOBAL
global Lilian, movement_active, current_target, adb_device, adb_path, latest_screenshot
full_counter = 0
lifted_cotton = 0
movement_active = False
current_target = None
adb_device = None
adb_path = None
latest_screenshot = None
screenshot_lock = threading.Lock()

# CONFIG
WINDOW_TITLE = 'LDPlayer'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ⭐ JOYSTICK POSITION
JOYSTICK_CENTER_X = 130
JOYSTICK_CENTER_Y = 550
JOYSTICK_PUSH_RADIUS = 70

# ⭐ GATHER BUTTON POSITION
GATHER_BUTTON_X = 380
GATHER_BUTTON_Y = 540

# ⭐ DRAG PARAMETERS
DRAG_DURATION_MS = 2000
DISTANCE_THRESHOLD = 40
DIRECTION_RECALC_INTERVAL = 0.5
HARVEST_COMPLETE_MIN_TIME = 3
DRAG_PUSH_MULTIPLIER = 0.5

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

# ============ ADB PATH DETECTION ============

def find_adb_path():
    """Auto detect ADB path"""
    global adb_path
    
    print("🔍 Searching for ADB path...")
    
    # Try common Windows paths
    windows_paths = [
        r"C:\Program Files\Android\platform-tools\adb.exe",
        r"C:\Program Files (x86)\Android\sdk\platform-tools\adb.exe",
        r"C:\Users\%username%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
    ]
    
    # Expand %username%
    windows_paths_expanded = []
    for path in windows_paths:
        if '%username%' in path:
            username = os.getenv('USERNAME')
            path = path.replace('%username%', username)
        windows_paths_expanded.append(path)
    
    # Try Windows paths
    for path in windows_paths_expanded:
        if os.path.exists(path):
            adb_path = path
            print(f"✅ Found ADB at: {adb_path}")
            return True
    
    # Try system PATH
    try:
        result = subprocess.run(['adb', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            adb_path = 'adb'
            print(f"✅ Found ADB in system PATH")
            return True
    except:
        pass
    
    # Try shutil.which
    adb_which = shutil.which('adb')
    if adb_which:
        adb_path = adb_which
        print(f"✅ Found ADB via shutil: {adb_path}")
        return True
    
    print("❌ ADB not found!")
    return False

# ============ AUTO DEVICE DETECTION ============

def auto_detect_device():
    """Auto detect available ADB device"""
    global adb_device, adb_path
    
    if not adb_path:
        return False
    
    print("🔍 Auto-detecting ADB device...")
    
    try:
        result = subprocess.run([adb_path, 'devices'], 
                              capture_output=True, text=True, timeout=5)
        
        devices = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'device' in line and 'List' not in line and 'attached' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    device_status = parts[1]
                    if device_status == 'device':
                        devices.append(device_id)
                        print(f"  Found: {device_id} ({device_status})")
        
        if not devices:
            print("❌ No devices found")
            return False
        
        # Priority: emulator-5554 > localhost:5555 > first available
        if 'emulator-5554' in devices:
            adb_device = 'emulator-5554'
            print(f"✅ Selected: emulator-5554 (LDPlayer)")
            return True
        elif 'localhost:5555' in devices:
            adb_device = 'localhost:5555'
            print(f"✅ Selected: localhost:5555")
            return True
        else:
            adb_device = devices[0]
            print(f"✅ Selected: {adb_device}")
            return True
            
    except Exception as e:
        print(f"❌ Device detection failed: {e}")
        return False

# ============ ADB FUNCTIONS ============

def init_adb():
    """Initialize ADB"""
    global adb_device, adb_path
    
    if not find_adb_path():
        return False
    
    # Try to connect to localhost:5555 (LDPlayer default)
    try:
        print("📱 Attempting to connect to localhost:5555 (LDPlayer)...")
        result = subprocess.run([adb_path, 'connect', 'localhost:5555'], 
                              capture_output=True, text=True, timeout=5)
        print(f"   Result: {result.stdout.strip()}")
        time.sleep(1)
    except Exception as e:
        print(f"   Connect attempt: {e}")
    
    # Auto detect device
    if not auto_detect_device():
        return False
    
    print(f"✅ ADB initialized successfully")
    print(f"   Device: {adb_device}")
    return True

def execute_adb_command(cmd):
    """Execute ADB command"""
    global adb_device, adb_path
    if not adb_device or not adb_path:
        return False
    
    try:
        print(f"   🔧 ADB: {cmd}")
        result = subprocess.run([adb_path, '-s', adb_device, 'shell', cmd],
                              capture_output=True, text=True, timeout=15)
        print(f"   ✅ Executed")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def adb_long_hold_drag(direction_x, direction_y, duration_ms=None):
    """Long hold drag"""
    global adb_device, adb_path
    if not adb_device or not adb_path:
        return False
    
    if duration_ms is None:
        duration_ms = DRAG_DURATION_MS
    
    try:
        mag = np.sqrt(direction_x**2 + direction_y**2)
        if mag < DIRECTION_AXIS_DEADZONE:
            return False
        
        norm_x = direction_x / mag
        norm_y = direction_y / mag
        push_dist = min(mag * DRAG_PUSH_MULTIPLIER, JOYSTICK_PUSH_RADIUS)
        
        target_x = int(JOYSTICK_CENTER_X + (norm_x * push_dist))
        target_y = int(JOYSTICK_CENTER_Y + (norm_y * push_dist))
        
        direction_str = ""
        if abs(norm_x) > abs(norm_y):
            direction_str = "←" if norm_x < 0 else "→"
        else:
            direction_str = "↑" if norm_y < 0 else "↓"
        
        print(f'🎮 {direction_str} DRAG: ({JOYSTICK_CENTER_X},{JOYSTICK_CENTER_Y}) → ({target_x},{target_y})')
        print(f'   {duration_ms}ms hold | Magnitude: {mag:.0f}')
        
        cmd = f"input touchscreen swipe {JOYSTICK_CENTER_X} {JOYSTICK_CENTER_Y} {target_x} {target_y} {duration_ms}"
        
        success = execute_adb_command(cmd)
        
        if success:
            time.sleep(duration_ms / 1000.0 + 0.1)
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Drag failed: {e}")
        return False

def adb_tap(x, y):
    """Tap"""
    global adb_device, adb_path
    if not adb_device or not adb_path:
        return False
    
    try:
        cmd = f"input touchscreen tap {x} {y}"
        print(f"   🖱️  Tap ({x}, {y})")
        return execute_adb_command(cmd)
    except Exception as e:
        print(f"❌ Tap failed: {e}")
        return False

# ============ TEMPLATE MATCHING ============

def find_harvest_prompt(screenshot):
    """Find harvest prompt"""
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
    """Find matches"""
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
    """Find locked target"""
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
    """Calculate distance"""
    return np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

# ============ SCREENSHOT THREAD ============

def screenshot_thread_worker(target_window):
    """Screenshot thread"""
    global latest_screenshot
    
    while Lilian:
        try:
            if not target_window.isActive:
                time.sleep(0.1)
                continue
            
            ss = pyautogui.screenshot()
            ss = np.array(ss)
            ss = cv2.cvtColor(ss, cv2.COLOR_RGB2BGR)
            
            with screenshot_lock:
                latest_screenshot = ss
            
            time.sleep(0.1)
        except Exception as e:
            time.sleep(0.1)

# ============ BOT MAIN LOOP ============

def create_bot(window_title):
    """Main bot loop"""
    global Lilian, lifted_cotton, movement_active, current_target, latest_screenshot
    
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
        print(f"📏 Resolution: {game_w}x{game_h}")
        print(f"🎮 Joystick: ({JOYSTICK_CENTER_X}, {JOYSTICK_CENTER_Y})")
        print(f"⏱️  Drag: {DRAG_DURATION_MS}ms")
        print("")
        
        # Start screenshot thread
        ss_thread = threading.Thread(target=screenshot_thread_worker, args=(target_window,), daemon=True)
        ss_thread.start()
        time.sleep(1)

        while not target_window.isActive:
            print("⏳ Waiting for window...")
            time.sleep(0.5)

        print("✅ Bot started!")

        locked_target = None
        harvesting = False
        harvest_start = 0.0
        last_direction_update = time.time()
        reached_target = False

        while True:
            if not Lilian:
                print("🛑 Stopped")
                break

            while not target_window.isActive:
                time.sleep(0.1)

            with screenshot_lock:
                ss = latest_screenshot
            
            if ss is None:
                time.sleep(0.05)
                continue

            try:
                now = time.monotonic()
                
                # STATE 1: Harvesting
                if harvesting:
                    if now - harvest_start >= HARVEST_COMPLETE_MIN_TIME:
                        print("✅ Harvest complete")
                        harvesting = False
                        locked_target = None
                        reached_target = False
                    continue
                
                # STATE 2: Reached target, check harvest prompt
                if reached_target and not movement_active:
                    prompt = find_harvest_prompt(ss)
                    if prompt:
                        print(f"🌾 Gather found! ({prompt[1]:.2f})")
                        harvesting = True
                        harvest_start = now
                        
                        tapped = adb_tap(GATHER_BUTTON_X, GATHER_BUTTON_Y)
                        if tapped:
                            lifted_cotton += 1
                            if 'label_lifted_cotton' in globals():
                                label_lifted_cotton.config(text=f'🌾 Cotton: {lifted_cotton}')
                            print(f"✅ Gathering...")
                            time.sleep(HARVEST_COMPLETE_MIN_TIME)
                            harvesting = False
                            reached_target = False
                            locked_target = None
                        continue
                
                # STATE 3: Force drag to target
                if locked_target and not movement_active:
                    match = find_locked_target(ss, locked_target)
                    if match is None:
                        print("⌛ Target LOST")
                        locked_target = None
                        reached_target = False
                    else:
                        tpl, conf, tl, target_center = match
                        locked_target['last_center'] = target_center
                        current_target = target_center
                        dist = calculate_distance((char_x, char_y), target_center)

                        if dist <= DISTANCE_THRESHOLD:
                            print(f"✅ REACHED! ({dist:.0f}px)")
                            reached_target = True
                        elif now - last_direction_update >= DIRECTION_RECALC_INTERVAL:
                            last_direction_update = now
                            dx = target_center[0] - char_x
                            dy = target_center[1] - char_y
                            
                            print(f"  📍 Distance: {dist:.0f}px")
                            
                            # FORCE DRAG
                            movement_active = True
                            try:
                                success = adb_long_hold_drag(dx, dy, DRAG_DURATION_MS)
                                if not success:
                                    print(f"  ⚠️ Drag failed")
                            finally:
                                movement_active = False
                        continue
                
                # STATE 4: Scan for cotton
                if not locked_target and not movement_active:
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
                            }
                            reached_target = False
                            print(f"🔒 Target LOCKED! ({dist:.0f}px, {conf:.2f})")

                try:
                    display_image(ss)
                except:
                    pass

            except Exception as e:
                print(f"❌ Error: {e}")
                movement_active = False

            time.sleep(0.05)

    except Exception as e:
        print(f"❌ Fatal: {e}")
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
    """Display screenshot"""
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
    """Test drag"""
    print("\n" + "="*60)
    print("🧪 TEST ADB DRAG")
    print("="*60)
    
    if not adb_device:
        print("❌ ADB not connected!")
        return
    
    print(f"✅ Device: {adb_device}")
    print(f"⏳ Starting in 3s...\n")
    time.sleep(3)
    
    print("Testing 4 directions...")
    for dx, dy, name in [(0, -200, "UP"), (200, 0, "RIGHT"), (0, 200, "DOWN"), (-200, 0, "LEFT")]:
        print(f"  {name}")
        adb_long_hold_drag(dx, dy, DRAG_DURATION_MS)
        time.sleep(0.5)
    
    print("\nTesting gather tap...")
    adb_tap(GATHER_BUTTON_X, GATHER_BUTTON_Y)
    print("\n✅ Test complete!")
    print("="*60 + "\n")

def start_function():
    """Start"""
    global Lilian
    if not adb_device:
        print("❌ ADB not connected!")
        return
    
    print("▶️  STARTING BOT v4.6")
    print(f"   Device: {adb_device}")
    Lilian = True
    threading.Thread(target=create_bot, args=(WINDOW_TITLE,), daemon=True).start()
    start_button["state"] = "disabled"
    stop_button["state"] = "normal"

def stop_function():
    """Stop"""
    global Lilian
    print("⏹️  STOPPING")
    Lilian = False
    start_button["state"] = "normal"
    stop_button["state"] = "disabled"

# ============ MAIN ============

if __name__ == "__main__":
    Lilian = False
    
    print("\n" + "="*60)
    print("🎮 HEARTWOOD BOT v4.6")
    print("="*60)
    print("\n🔌 Initializing...\n")
    
    if not init_adb():
        print("\n⚠️  ADB initialization failed!")
    
    root = tk.Tk()
    root.title("🎮 Heartwood Bot v4.6 (AUTO DEVICE DETECT)")
    root.geometry("305x700+0+0")
    root.attributes("-topmost", True)
    root.wm_attributes('-toolwindow', 1)
    root.configure(bg='#2b2b2b')

    console = tk.Text(root, wrap=tk.WORD, height=14, width=35,
                      bg='#1e1e1e', fg='#00ff00', font=('Courier', 8))
    console.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
    sys.stdout = RedirectText(console)

    start_button = tk.Button(root, text="▶️  START", command=start_function,
                             fg="white", bg="#00aa00", font=('Arial', 10, 'bold'))
    start_button.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

    stop_button = tk.Button(root, text="⏹️  STOP", command=stop_function,
                            fg="white", bg="#aa0000", font=('Arial', 10, 'bold'))
    stop_button.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    test_button = tk.Button(root, text="🧪 TEST INPUT", command=test_input,
                            fg="white", bg="#0099cc", font=('Arial', 8))
    test_button.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky='ew')

    image_label = tk.Label(root, bg='#1e1e1e', height=8)
    image_label.grid(row=3, column=0, columnspan=2, padx=0, pady=5, sticky='ew')

    label_lifted_cotton = tk.Label(root, text="🌾 Cotton: 0", fg="#00ff00", bg='#2b2b2b',
                                   font=('Arial', 12, 'bold'))
    label_lifted_cotton.grid(row=0, column=0, columnspan=2, padx=0, pady=5)

    print('╔════════════════════════════════════╗')
    print('║  🎮 HEARTWOOD BOT v4.6            ║')
    print('║  AUTO DEVICE DETECTION             ║')
    print('║  emulator-5554 PRIORITY            ║')
    print('╚════════════════════════════════════╝')
    print('')
    print('🆕 v4.6 CRITICAL FIXES:')
    print('  ✅ Auto detect correct ADB device')
    print('  ✅ emulator-5554 priority (LDPlayer)')
    print('  ✅ localhost:5555 fallback')
    print('  ✅ Any device support')
    print('')
    print('Auto-Detection Priority:')
    print('  1. emulator-5554 (LDPlayer)')
    print('  2. localhost:5555')
    print('  3. First available device')
    print('')

    stop_button["state"] = "disabled"
    root.mainloop()
