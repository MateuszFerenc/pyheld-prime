import uasyncio as asyncio
import hardware as hw

from hardware import play_async

power_up_snd = [(440, 100), (880, 100), (1760, 150)]

asyncio.create_task(play_async(power_up_snd))

async def main_menu():
    selected = 0
    games = ["flappy", "pacman"]

    while True:
        hw.display.fill(0)
        hw.display.text("MENU:", 0, 0, 1)
        hw.display.show()

        btns = hw.get_buttons()
        if not (btns & (1 << 2)): # Przycisk START
            module = __import__(games[selected])
            await module.start() 
            
        await asyncio.sleep_ms(100)

try:
    asyncio.run(main_menu())
except KeyboardInterrupt:
    pass