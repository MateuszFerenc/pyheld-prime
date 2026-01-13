import pcd8544_fb
import uasyncio as asyncio
from machine import Pin, SPI, I2C, PWM
import rotatedProxy
from ezFBfont import ezFBfont as font
import ezFBfont_4x6_ascii_06 
import gc

i2c = I2C(scl=Pin(5), sda=Pin(4))
spi = SPI(1, baudrate=8000000, polarity=0, phase=0)

cs = Pin(0)
dc = Pin(2)

display = pcd8544_fb.PCD8544_FB(spi, cs, dc)
proxy = rotatedProxy.RotatedProxy(display, 84, 48)   

font_default = font(proxy, ezFBfont_4x6_ascii_06)

pcf_addr = 0x20

pwm_pin = Pin(15)
speaker = PWM(pwm_pin)
speaker.duty(0)

async def play_async(melody):
    for freq, duration in melody:
        if freq == 0:
            speaker.duty(0)
        else:
            speaker.freq(freq)
            speaker.duty(512)
        await asyncio.sleep_ms(duration)
    speaker.duty(0)

def get_buttons():
    return i2c.readfrom(pcf_addr, 1)[0]

def mem_free():
    r = gc.mem_free()
    print('free memory: %d' % r)