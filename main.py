import uasyncio as asyncio
import hardware as hw

power_up_snd = [(440, 100), (880, 100), (1760, 150)]
up_snd = [(500, 100), (760, 100)]
down_snd = [(760, 100), (500, 100)]

async def main_menu():
    hw.show_system_info()

    hw.play_sound(power_up_snd)

    await asyncio.sleep(3)

    games = ["Flappy Bird", "Pacman", "Snake"] 
    selected = 0 
    while True: 
        hw.display.fill(0) 
        hw.font_default.write("WYBIERZ GRE:", 0, 0)
        for i, name in enumerate(games): 
            prefix = ">" if i == selected else " " 
            hw.font_default.write(prefix + name, 5, 15 + (i*10))
        hw.display.show()
        
        btns = hw.get_buttons()
        # print(f"Got buttons: {btns}")
        #if not (btns & (1 << 2)): # Przycisk START
        #    module = __import__(games[selected])
        #    await module.start() 

        if not (btns & (1 << 7)): # Przycisk Up
            selected = (selected - 1) % len(games) 
            hw.play_sound(up_snd)
            await asyncio.sleep_ms(10) 

        if not (btns & (1 << 6)): # Przycisk Down 
            selected = (selected + 1) % len(games) 
            hw.play_sound(down_snd)
            await asyncio.sleep_ms(10) 
            
        await asyncio.sleep_ms(100)

try:
    asyncio.run(main_menu())
except KeyboardInterrupt:
    pass