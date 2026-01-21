from hardware import Hardware, System, __version__, fileSystem, sysModules, uasyncio


async def main_menu():
    hw = Hardware()
    sys = System(display = hw.display, font = hw.font_default)

    sys.show_system_info()
    await hw.asyncio.sleep(1)

    hw.display.load_pbm("logo.pbm")
    hw.font_default.write(__version__, 0, 42)
    hw.display.show()
    hw.sound.play_sound(hw.sound.POWER_UP_SND)
    await hw.asyncio.sleep(2)

    hw.asyncio.create_task(hw.buttons.scan_task())

    hw.gcCollect()
    games = []
    for game in fileSystem.listdir('/'):
        if game[:2] == "G_":
            module = __import__(game.split('.')[0])
            games.append((getattr(module, '__long_name__'), game.split('.')[0]))

            del module
            if games[-1][1] in sysModules:
                del sysModules[games[-1][1]]
            hw.gcCollect()


    selected: list = [0, 0]
    page_size = 3
    while True: 
        hw.display.fill(0) 
        hw.font_default.write("WYBIERZ GRE:", 0, 0)
        for i, game in zip(range(page_size), games[selected[0]:selected[0]+3]): 
            hw.font_default.write(game[0], 2, 15 + (i * 10), i != (selected[1] % page_size), i == (selected[1] % page_size))
        hw.display.show()
        
        if hw.buttons.was_pressed(hw.BTN_C):
           hw.buttons.reset_state()
           await sys.run_game(games[selected[0] + selected[1]][1], hardware=hw)
           hw.buttons.reset_state()
           hw.buttons.clear_callbacks()

        if hw.buttons.was_pressed(hw.BTN_DOWN):
            if selected[1] < (page_size - 1):
                selected[1] += 1
            else:
                if selected[0] < len(games) - page_size:
                    selected[0] += 1
                else:
                    selected[0] = 0
                    selected[1] = 0

            hw.sound.play_sound(hw.sound.UP_SND)

        if hw.buttons.was_pressed(hw.BTN_UP):
            if selected[1] != 0:
                selected[1] -= 1
            else:
                if selected[0] != 0:
                    selected[0] -= 1
                else:
                    selected[0] = len(games) - page_size
                    selected[1] = page_size - 1
            
            hw.sound.play_sound(hw.sound.DOWN_SND)

        if hw.buttons.was_pressed(hw.BTN_B):
            sys.show_system_info()
            await hw.asyncio.sleep(2)
            
        await hw.asyncio.sleep_ms(100) # type: ignore

try:
    uasyncio.run(main_menu())
except KeyboardInterrupt:
    pass