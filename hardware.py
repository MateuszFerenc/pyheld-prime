import pcd8544_fb
import uasyncio as asyncio
from machine import Pin, SPI, I2C, PWM, ADC, freq
from ezFBfont import ezFBfont as font
import ezFBfont_4x6_ascii_06 
from gc import collect as gcCollect, mem_free as gcMem_free, mem_alloc as gcMem_alloc # type: ignore
from os import statvfs # type: ignore
from sys import modules as sysModules

SND_START = [(880, 100), (0, 50), (880, 100), (1174, 200)]


async def _play_async(melody):
    try:
        async with speaker_lock:
            for freq, duration in melody:
                if freq == 0:
                    speaker.duty(0)
                else:
                    speaker.freq(freq)
                    speaker.duty(512)
                await asyncio.sleep_ms(duration) # type: ignore
            speaker.duty(0)
    except asyncio.CancelledError:
        speaker.duty(0)
        raise

def play_sound(melody, interrupt=False):
    global current_sound_task
    
    if interrupt and current_sound_task is not None:
        current_sound_task.cancel()
    
    current_sound_task = asyncio.create_task(_play_async(melody))
    return current_sound_task

def get_system_info():
    gcCollect()
    ram_free = gcMem_free()
    ram_alloc = gcMem_alloc()
    ram_total = ram_free + ram_alloc
    
    fs_stat = statvfs('/')
    flash_total = fs_stat[0] * fs_stat[2]
    flash_free = fs_stat[0] * fs_stat[3]
    
    adc = ADC(0)
    raw_v = adc.read()
    voltage = raw_v / ((100.0 / ( 100.0 + 220.0 + 142.0 )) * 1023.0)

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

async def run_game(game_name):
    gcCollect()

    try:
        module = __import__(game_name)
        await module.start()

        if game_name in sysModules:
            del sysModules[game_name]

    except Exception as e:
        display.fill(0)
        font_default.write("Game error:", 0, 0)
        font_default.write(str(e)[:15], 0, 10)
        font_default.write(str(e)[16:30], 0, 18)
        display.show()
        await asyncio.sleep(2)
    
    finally:
        gcCollect()


class ButtonEvents:
    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address
        self.last_state = 0xFF
        self.pressed_mask = 0x00
        self.callbacks = {}

    def on_press(self, btn_bit, callback):
        self.callbacks[btn_bit] = callback

    def clear_callbacks(self):
        self.callbacks = {}

    async def scan_task(self):
        while True:
            try:
                current = self.i2c.readfrom(self.address, 1)[0]
                new_presses = (self.last_state & ~current)
                
                if new_presses:
                    self.pressed_mask |= new_presses
                    
                    for bit, callback in self.callbacks.items():
                        if new_presses & bit:
                            callback()
                                
                self.last_state = current
            except Exception as e:
                print(f"hardware/ButtonEvents.scan_task error: {e}")
            
            await asyncio.sleep_ms(20) # type: ignore

    def was_pressed(self, btn_bit):
        if self.pressed_mask & btn_bit:
            self.pressed_mask &= ~btn_bit
            return True
        return False
    
BTN_UP = 1 << 7
BTN_DOWN = 1 << 6
BTN_LEFT = 1 << 5
BTN_RIGHT = 1 << 4
BTN_A = 1 << 1
BTN_B = 1 << 2
BTN_C = 1 << 3

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

buttons = ButtonEvents(i2c, pcf_addr)