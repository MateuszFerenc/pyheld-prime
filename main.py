import uasyncio as asyncio
import hardware as hw

power_up_snd = [(440, 100), (880, 100), (1760, 150)]
up_snd = [(500, 100), (760, 100)]
down_snd = [(760, 100), (500, 100)]

async def main_menu():
    hw.show_system_info()
    await asyncio.sleep(2)

    hw.show_pbm("logo.pbm")
    hw.play_sound(power_up_snd)
    await asyncio.sleep(2)

    asyncio.create_task(hw.buttons.scan_task())

    # games = (("Flappy Bird", "flappy"), ("Pacman", "pacman"), ("Snake", "snake"))
    hw.gcCollect()
    games = []
    for game in hw.listdir('/'):
        if game[:2] == "G_":
            module = __import__(game.split('.')[0])
            games.append((getattr(module, '__long_name__'), game.split('.')[0]))

            del module
            if games[-1][1] in hw.sysModules:
                del hw.sysModules[games[-1][1]]
            hw.gcCollect()


    selected = 0 
    while True: 
        hw.display.fill(0) 
        hw.font_default.write("WYBIERZ GRE:", 0, 0)
        for i, name in enumerate(games): 
            prefix = ">" if i == selected else " " 
            hw.font_default.write(prefix + name[0], 5, 15 + (i*10))
        hw.display.show()
        
        if hw.buttons.was_pressed(hw.BTN_C): # Przycisk START
           hw.buttons.reset_state()
           await hw.run_game(games[selected][1])
           hw.buttons.reset_state()
           hw.buttons.clear_callbacks()

        if hw.buttons.was_pressed(hw.BTN_UP): # Przycisk Up
            selected = (selected - 1) % len(games) 
            hw.play_sound(up_snd)

        if hw.buttons.was_pressed(hw.BTN_DOWN): # Przycisk Down 
            selected = (selected + 1) % len(games) 
            hw.play_sound(down_snd)

        if hw.buttons.was_pressed(hw.BTN_B): # Przycisk B
            hw.show_system_info()
            await asyncio.sleep(2)
            
        await asyncio.sleep_ms(100) # type: ignore

try:
    asyncio.run(main_menu())
except KeyboardInterrupt:
    pass