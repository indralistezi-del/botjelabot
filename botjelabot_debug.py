#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG SCRIPT - Test ADB drag dengan berbagai parameter
"""

import subprocess
import time

adb_device = 'localhost:5555'

def adb_shell(command):
    """Execute ADB shell command"""
    try:
        result = subprocess.run(['adb', '-s', adb_device, 'shell', command],
                              capture_output=True, text=True, timeout=5)
        print(f"✅ Command executed: {command}")
        print(f"   Output: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_tap():
    """Test simple tap"""
    print("\n" + "="*60)
    print("TEST 1: Simple TAP at center joystick")
    print("="*60)
    adb_shell("input touchscreen tap 130 550")
    time.sleep(0.5)

def test_drag_short():
    """Test drag pendek"""
    print("\n" + "="*60)
    print("TEST 2: Short DRAG (300ms)")
    print("="*60)
    adb_shell("input touchscreen swipe 130 550 200 550 300")
    time.sleep(1)

def test_drag_medium():
    """Test drag medium"""
    print("\n" + "="*60)
    print("TEST 3: Medium DRAG (500ms)")
    print("="*60)
    adb_shell("input touchscreen swipe 130 550 200 550 500")
    time.sleep(1)

def test_drag_long():
    """Test drag panjang"""
    print("\n" + "="*60)
    print("TEST 4: Long DRAG (1000ms)")
    print("="*60)
    adb_shell("input touchscreen swipe 130 550 200 550 1000")
    time.sleep(1.5)

def test_drag_extreme():
    """Test drag ekstrim"""
    print("\n" + "="*60)
    print("TEST 5: Extreme DRAG (2000ms)")
    print("="*60)
    adb_shell("input touchscreen swipe 130 550 200 550 2000")
    time.sleep(2.5)

def test_multiple_drags():
    """Test multiple drags in sequence"""
    print("\n" + "="*60)
    print("TEST 6: Multiple DRAGS (direction changes)")
    print("="*60)
    directions = [
        (130, 550, 130, 450, "UP"),
        (130, 550, 200, 550, "RIGHT"),
        (130, 550, 130, 650, "DOWN"),
        (130, 550, 60, 550, "LEFT"),
    ]
    
    for x1, y1, x2, y2, name in directions:
        print(f"\n   Drag {name}: ({x1},{y1}) → ({x2},{y2})")
        adb_shell(f"input touchscreen swipe {x1} {y1} {x2} {y2} 800")
        time.sleep(1)

def test_coordinate_discovery():
    """Test berbagai coordinate untuk menemukan yang benar"""
    print("\n" + "="*60)
    print("TEST 7: Coordinate DISCOVERY (tap berbagai posisi)")
    print("="*60)
    
    test_coords = [
        (130, 550, "Default (130, 550)"),
        (100, 500, "Top-Left (100, 500)"),
        (150, 500, "Top-Right (150, 500)"),
        (100, 600, "Bottom-Left (100, 600)"),
        (150, 600, "Bottom-Right (150, 600)"),
        (400, 400, "Center High (400, 400)"),
        (400, 800, "Center Low (400, 800)"),
    ]
    
    for x, y, desc in test_coords:
        print(f"\n   Tap at {desc}")
        adb_shell(f"input touchscreen tap {x} {y}")\n        time.sleep(0.5)

def test_emulator_info():
    """Get emulator screen size"""
    print("\n" + "="*60)
    print("TEST 8: Get EMULATOR INFO")
    print("="*60)
    
    print("\n📱 Screen size:")
    adb_shell("wm size")
    
    print("\n🔌 ADB devices:")
    subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    
    print("\n📊 Display dump (first 50 lines):")
    result = subprocess.run(['adb', '-s', adb_device, 'shell', 'dumpsys display | head -50'],
                          capture_output=True, text=True)
    print(result.stdout)

if __name__ == "__main__":
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "🎮 ADB DRAG DEBUG - Heartwood Bot" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    # Test ADB connection first
    print("\n🔌 Testing ADB connection...")
    try:
        result = subprocess.run(['adb', 'devices'], 
                              capture_output=True, text=True, timeout=5)
        if 'localhost:5555' in result.stdout:
            print("✅ ADB connected to localhost:5555")
        else:
            print("⚠️  ADB devices:")
            print(result.stdout)
    except Exception as e:
        print(f"❌ ADB error: {e}")
        exit(1)
    
    print("\n" + "="*60)
    print("⏳ PERSIAPAN: Pastikan LDPlayer game sudah buka dan karakter")
    print("   ready. Anda punya 5 detik untuk siap-siap...")
    print("="*60)
    time.sleep(5)
    
    # Run tests
    test_tap()
    time.sleep(1)
    
    test_drag_short()
    time.sleep(1)
    
    test_drag_medium()
    time.sleep(1)
    
    test_drag_long()
    time.sleep(1)
    
    test_drag_extreme()
    time.sleep(1)
    
    test_multiple_drags()
    time.sleep(1)
    
    test_coordinate_discovery()
    time.sleep(1)
    
    test_emulator_info()
    
    print("\n" + "="*60)
    print("✅ DEBUG TESTS SELESAI!")
    print("="*60)
    print("\n📝 INSTRUCTIONS:")
    print("1. Lihat mana test yang berhasil membuat karakter bergerak")
    print("2. Catat parameter yang berhasil (duration, coordinates)")
    print("3. Update botjelabot.py dengan parameter tersebut")
    print("4. Khususnya update:")
    print("   - JOYSTICK_CENTER_X")
    print("   - JOYSTICK_CENTER_Y")
    print("   - DRAG_DURATION_MS")
    print("\n")
