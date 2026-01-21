from pcd8544_fb import PCD8544_FB
import uasyncio
from machine import Pin, SPI, I2C, PWM, ADC, freq
from ezFBfont import ezFBfont as font
import ezFBfont_4x6_ascii_06 
from gc import collect as gcCollect, mem_free as gcMem_free, mem_alloc as gcMem_alloc # type: ignore
import os as fileSystem
from sys import modules as sysModules
import framebuf

__version__ = "v1.0.2"

class Hardware:
    BTN_UP = 1 << 7
    BTN_DOWN = 1 << 6
    BTN_LEFT = 1 << 5
    BTN_RIGHT = 1 << 4
    BTN_A = 1 << 1
    BTN_B = 1 << 2
    BTN_C = 1 << 3

    def __init__(self, speakerPin: int = 15, i2cSDA: int = 4, i2cSCL: int = 5, spiBaud: int = 8000000, displayCS: int = 0, displayDC: int = 2, i2cButtonsAddr: int = 0x20) -> None:
        self.__speaker = PWM(Pin(speakerPin))
        self.__speaker.duty(0)

        self.sound = Sound(self.__speaker)

        self.spi = SPI(1, baudrate = spiBaud)
        self.i2c = I2C(scl = Pin(i2cSCL), sda = Pin(i2cSDA))

        self.display = DisplayOverride(self.spi, Pin(displayCS), Pin(displayDC))
        self.display.contrast(60)

        self.font_default = FontOverride(self.display, ezFBfont_4x6_ascii_06)

        self.buttons = ButtonEvents(self.i2c, i2cButtonsAddr)

        self.gcCollect = gcCollect
        self.gcMemFree = gcMem_free

        self.asyncio = uasyncio

        network = __import__("network")
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(False)

        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)

        del sta_if
        del ap_if
        del network
        self.gcCollect()


class Sound:
    POWER_UP_SND = [(440, 100), (880, 100), (1760, 150)]
    UP_SND = [(500, 100), (760, 100)]
    DOWN_SND = [(760, 100), (500, 100)]

    SND_START = [(880, 100), (0, 50), (880, 100), (1174, 200)]
    SND_DIE = [(400, 100), (200, 200)]
    CHEAT_ON_SND = [(400, 200), (600, 200), (800, 200)]
    CHEAT_OFF_SND = [(800, 200), (600, 200), (400, 200)]

    def __init__(self, speaker) -> None:
        self.speaker = speaker
        self.current_sound_task = None
        self.speaker_lock = uasyncio.Lock()
    
    async def _play_async(self, melody):
        try:
            async with self.speaker_lock:    # mutex na dostęp do głośnika
                for freq, duration in melody:   # pobieranie tonu i jego czasu
                    if freq == 0:
                        self.speaker.duty(0)     # cisza
                    else:
                        self.speaker.freq(freq)  # częstotliwość
                        self.speaker.duty(512)   # wypełnienie
                    await uasyncio.sleep_ms(duration) # type: ignore
                self.speaker.duty(0)     # wyciszenie po zakończeniu gry
        except uasyncio.CancelledError:
            self.speaker.duty(0)
            raise

    def play_sound(self, melody, interrupt=False):
        if interrupt and self.current_sound_task is not None:
            self.current_sound_task.cancel()
        
        self.current_sound_task = uasyncio.create_task(self._play_async(melody))
        return self.current_sound_task

class System:
    def __init__(self, display: DisplayOverride, font: FontOverride) -> None:
        self.display = display
        self.font = font

    def readBatteryVoltage(self, channel: int = 0):
        adc = ADC(channel)
        raw_v = adc.read()
        voltage = raw_v / ((100.0 / ( 100.0 + 220.0 + 142.0 )) * 1023.0)
        return voltage
    
    def get_system_info(self):
        gcCollect()
        ram_free = gcMem_free()
        ram_alloc = gcMem_alloc()
        ram_total = ram_free + ram_alloc
        
        fs_stat = fileSystem.statvfs('/') # type: ignore
        flash_total = fs_stat[0] * fs_stat[2]
        flash_free = fs_stat[0] * fs_stat[3]
        
        voltage = self.readBatteryVoltage()

        cpu_freq = freq() // 1000000 # MHz
        
        return {
            "ram": ram_free // 1024,
            "all_ram": ram_total // 1024,
            "flash": flash_free // 1024,
            "all_flash": flash_total // 1024,
            "volt": round(voltage, 2),
            "cpu": cpu_freq
        }
    
    def show_system_info(self):
        info = self.get_system_info()
        self.display.fill(0)
        self.font.text_centered("-- SYS INFO --", 0)
        self.font.write(f"CPU: {info['cpu']}MHz", 0, 10)
        self.font.write(f"RAM: {info['ram']}\\{info['all_ram']}kB", 0, 18)
        self.font.write(f"MEM: {info['flash']}\\{info['all_flash']}kB", 0, 26)
        self.font.write(f"BAT: {info['volt']}V", 0, 34)
        self.display.show()

    async def run_game(self, game_name, hardware: Hardware):
        gcCollect() # wstępne uruchomienie garbage collector

        try:
            module = __import__(game_name)  # import właściwego modułu
            game = module.Game(hardware=hardware)
            await game.start()    # wywołanie metody start

            del module, game

            if game_name in sysModules:     # czyszczenie pamięci modułów
                del sysModules[game_name]

        except Exception as e:  # obsługa błędu gry
            self.display.fill(0)
            print(f"Game error:\n{e}")
            self.font.write("Game error:", 0, 0)
            self.font.multiline_text(str(e), 0, 10)
            self.display.show()
            await uasyncio.sleep(2)
        
        finally:    # finalne czyszczenie po grze, aby odzyskać jak najwięcej pamięci
            gcCollect()


class DisplayOverride(PCD8544_FB):
    def load_pbm(self, filename: str, x: int = 0, y: int = 0):
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
                self.blit(fb, x, y)
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
            
            await uasyncio.sleep_ms(20) # type: ignore

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
    
if __name__ == "__main__":
    print(f"This file should not be run standalone!")