import pcd8544_fb
import uasyncio as asyncio
from machine import Pin, SPI, I2C, PWM, ADC, freq
from ezFBfont import ezFBfont as font
import ezFBfont_4x6_ascii_06 
import gc
import os

i2c = I2C(scl=Pin(5), sda=Pin(4))
spi = SPI(1, baudrate=8000000, polarity=0, phase=0)

cs = Pin(0)
dc = Pin(2)

display = pcd8544_fb.PCD8544_FB(spi, cs, dc)  
display.contrast(55)

font_default = font(display, ezFBfont_4x6_ascii_06)

pcf_addr = 0x20

pwm_pin = Pin(15)
speaker = PWM(pwm_pin)
speaker.duty(0)

speaker_lock = asyncio.Lock()
current_sound_task = None

freq(160)

async def _play_async(melody):
    try:
        async with speaker_lock:
            for freq, duration in melody:
                if freq == 0:
                    speaker.duty(0)
                else:
                    speaker.freq(freq)
                    speaker.duty(512)
                await asyncio.sleep_ms(duration)
            speaker.duty(0)
    except asyncio.CancelledError:
        speaker.duty(0)
        raise

def play_sound(melody, interrupt=False):
    global current_sound_task
    
    if interrupt and current_sound_task is not None:
        current_sound_task.cancel()
    
    # Tworzymy nowe zadanie
    current_sound_task = asyncio.create_task(_play_async(melody))
    return current_sound_task

def get_buttons():
    return i2c.readfrom(pcf_addr, 1)[0]

def get_system_info():
    # 1. RAM (w bajtach)
    gc.collect() # czyścimy przed pomiarem
    ram_free = gc.mem_free()
    ram_alloc = gc.mem_alloc()
    ram_total = ram_free + ram_alloc
    
    fs_stat = os.statvfs('/')
    flash_total = fs_stat[0] * fs_stat[2]
    flash_free = fs_stat[0] * fs_stat[3]
    
    adc = ADC(0)
    raw_v = adc.read()
    voltage = raw_v / ((100.0 / ( 100.0 + 220.0 + 142.0 )) * 1023.0)

    # 4. Inne dane
    cpu_freq = freq() // 1000000 # MHz
    
    return {
        "ram": ram_free // 1024,
        "all_ram": ram_total // 1024,
        "flash": flash_free // 1024,
        "all_flash": flash_total // 1024,
        "volt": round(voltage, 2),
        "cpu": cpu_freq
    }

def show_system_info():
    info = get_system_info()
    display.fill(0)
    font_default.write("SYS INFO", 10, 0)
    font_default.write(f"CPU: {info['cpu']}MHz", 0, 10)
    font_default.write(f"RAM: {info['ram']}\\{info['all_ram']}kB", 0, 18)
    font_default.write(f"MEM: {info['flash']}\\{info['all_flash']}kB", 0, 26)
    font_default.write(f"BAT: {info['volt']}V", 0, 34)
    display.show()