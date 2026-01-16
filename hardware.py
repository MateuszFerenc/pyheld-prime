import pcd8544_fb
import uasyncio as asyncio
from machine import Pin, SPI, I2C, PWM, ADC, freq
from ezFBfont import ezFBfont as font
import ezFBfont_4x6_ascii_06 
# import ezFBfont_6x12_ascii_10
from gc import collect as gcCollect, mem_free as gcMem_free, mem_alloc as gcMem_alloc # type: ignore
from os import statvfs, listdir # type: ignore
from sys import modules as sysModules
import framebuf

SND_START = [(880, 100), (0, 50), (880, 100), (1174, 200)]
SND_DIE  = [(400, 100), (200, 200)]

async def _play_async(melody):
    try:
        async with speaker_lock:    # mutex na dostęp do głośnika
            for freq, duration in melody:   # pobieranie tonu i jego czasu
                if freq == 0:
                    speaker.duty(0)     # cisza
                else:
                    speaker.freq(freq)  # częstotliwość
                    speaker.duty(512)   # wypełnienie
                await asyncio.sleep_ms(duration) # type: ignore
            speaker.duty(0)     # wyciszenie po zakończeniu gry
    except asyncio.CancelledError:
        speaker.duty(0)
        raise

def play_sound(melody, interrupt=False):
    global current_sound_task
    
    if interrupt and current_sound_task is not None:
        current_sound_task.cancel()
    
    current_sound_task = asyncio.create_task(_play_async(melody))
    return current_sound_task

def readBatteryVoltage():
    adc = ADC(0)
    raw_v = adc.read()
    voltage = raw_v / ((100.0 / ( 100.0 + 220.0 + 142.0 )) * 1023.0)
    return voltage

def get_system_info():
    gcCollect()
    ram_free = gcMem_free()
    ram_alloc = gcMem_alloc()
    ram_total = ram_free + ram_alloc
    
    fs_stat = statvfs('/')
    flash_total = fs_stat[0] * fs_stat[2]
    flash_free = fs_stat[0] * fs_stat[3]
    
    voltage = readBatteryVoltage()

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
    font_default.text_centered("-- SYS INFO --", 0)
    font_default.write(f"CPU: {info['cpu']}MHz", 0, 10)
    font_default.write(f"RAM: {info['ram']}\\{info['all_ram']}kB", 0, 18)
    font_default.write(f"MEM: {info['flash']}\\{info['all_flash']}kB", 0, 26)
    font_default.write(f"BAT: {info['volt']}V", 0, 34)
    display.show()

async def run_game(game_name):
    gcCollect() # wstępne uruchomienie garbage collector

    try:
        module = __import__(game_name)  # import właściwego modułu
        await module.start()    # wywołanie metody start

        del module

        if game_name in sysModules:     # czyszczenie pamięci modułów
            del sysModules[game_name]

    except Exception as e:  # obsługa błędu gry
        display.fill(0)
        print(f"Game error:\n{e}")
        font_default.write("Game error:", 0, 0)
        font_default.multiline_text(str(e), 0, 10)
        display.show()
        await asyncio.sleep(2)
    
    finally:    # finalne czyszczenie po grze, aby odzyskać jak najwięcej pamięci
        gcCollect()

def show_pbm(filename: str, x: int = 0, y: int = 0):
    gcCollect()
    try:
        with open(filename, 'rb') as f:
            type = f.readline()
            if type != b'P4\n':
                line = f.readline()
                while line.startswith(b'#'):
                    line = f.readline()
                dims = line.split()
            else:
                dims = f.readline().split()
            
            width = int(dims[0])
            height = int(dims[1])
            
            data = f.read()
            
            fb = framebuf.FrameBuffer(bytearray(data), width, height, framebuf.MONO_HLSB)
            display.blit(fb, x, y)
            display.show()
            del fb
            gcCollect()
    except Exception as e:
        print("Błąd wczytywania PBM:", e)


class FontOverride(font):
    def text_centered(self, text: str, y: int, color: int = 1):
        size_x, _ = self.size(text)
        x = (self._device.width // 2) - (size_x // 2)
        x = max(0, x)
        self.write(text, x, y, color)

    def multiline_text(self, text: str, x: int, y: int, color: int = 1):
        words = text.split(' ')
        current_line = ""
        current_y = y
        
        for word in words:
            test_line = current_line + word + " "
            w, h = self.size(test_line)
            
            if x + w > self._device.width:
                self.write(current_line, x, current_y, color)
                current_line = word + " "
                current_y += self._font.height() + 2
                
                if current_y > self._device.height - self._font.height():
                    current_line = ""
                    break
            else:
                current_line = test_line
        
        if current_line:
            self.write(current_line, x, current_y, color)


class ButtonEvents:
    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address
        self.last_state = 0xFF
        self.pressed_mask = 0x00
        self.callbacks = {}
        self.callbacks_combo = {}

    def on_press(self, btn_bit: int, callback):
        self.callbacks[btn_bit] = callback

    def on_combo(self, bits: int, callback):
        self.callbacks_combo[bits] = callback

    def clear_callbacks(self):
        self.callbacks = {}
        self.callbacks_combo = {}

    async def scan_task(self):
        active_combos = set()
        while True:
            try:
                current = self.i2c.readfrom(self.address, 1)[0] # odczyt z ekspandera
                new_presses = (self.last_state & ~current)  # wyznaczenie tylko zmienionych bitów
                
                if self.callbacks_combo:
                    for bits, callback in self.callbacks_combo.items():
                        is_pressed = (current & bits) == 0
                    
                        if is_pressed and bits not in active_combos:
                            callback()
                            active_combos.add(bits)
                        elif not is_pressed and bits in active_combos:
                            active_combos.remove(bits)

                if new_presses: # jeżeli nowe wciśnięcia
                    self.pressed_mask |= new_presses
                    # wywołanie funkcji zarejestrowanej dla danego przycisku
                    for bit, callback in self.callbacks.items():
                        if new_presses & bit and not active_combos:
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
    
    def reset_state(self):
        self.pressed_mask = 0x00
        try:
            self.last_state = self.i2c.readfrom(self.address, 1)[0]
        except:
            pass
    
BTN_UP = 1 << 7
BTN_DOWN = 1 << 6
BTN_LEFT = 1 << 5
BTN_RIGHT = 1 << 4
BTN_A = 1 << 1
BTN_B = 1 << 2
BTN_C = 1 << 3

network = __import__("network")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(False)

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

del sta_if
del ap_if
del network
gcCollect()

i2c = I2C(scl=Pin(5), sda=Pin(4))
spi = SPI(1, baudrate=8000000, polarity=0, phase=0)

cs = Pin(0)
dc = Pin(2)

display = pcd8544_fb.PCD8544_FB(spi, cs, dc)  
display.contrast(60)

font_default = FontOverride(display, ezFBfont_4x6_ascii_06)

pcf_addr = 0x20

pwm_pin = Pin(15)
speaker = PWM(pwm_pin)
speaker.duty(0)

speaker_lock = asyncio.Lock()
current_sound_task = None

buttons = ButtonEvents(i2c, pcf_addr)