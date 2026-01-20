import uasyncio as asyncio
import hardware as hw

power_up_snd = [(440, 100), (880, 100), (1760, 150)]
up_snd = [(500, 100), (760, 100)]
down_snd = [(760, 100), (500, 100)]

async def main_menu():
    hw.show_system_info()
    await asyncio.sleep(1)

    hw.display.load_pbm("logo.pbm")
    hw.font_default.write(hw.__version__, 0, 42)
    hw.display.show()
    hw.play_sound(power_up_snd)
    await asyncio.sleep(2)

    asyncio.create_task(hw.buttons.scan_task())

    hw.gcCollect()
    games = []
    for game in hw.os.listdir('/'):
        if game[:2] == "G_":
            module = __import__(game.split('.')[0])
            games.append((getattr(module, '__long_name__'), game.split('.')[0]))

            del module
            if games[-1][1] in hw.sysModules:
                del hw.sysModules[games[-1][1]]
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
           await hw.run_game(games[selected[0] + selected[1]][1])
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
            print(f"selected: {selected}")
            print(f"range: ({selected[0]}, {selected[0]+3}), games: {games[selected[0]:selected[0]+3]}" )
            hw.play_sound(up_snd)

        if hw.buttons.was_pressed(hw.BTN_UP):
            if selected[1] != 0:
                selected[1] -= 1
            else:
                if selected[0] != 0:
                    selected[0] -= 1
                else:
                    selected[0] = len(games) - page_size
                    selected[1] = page_size - 1
            print(f"selected: {selected}")
            print(f"range: ({selected[0]}, {selected[0]+3}), games: {games[selected[0]:selected[0]+3]}" )
            hw.play_sound(down_snd)

        if hw.buttons.was_pressed(hw.BTN_B):
            hw.show_system_info()
            await asyncio.sleep(2)
            
        await asyncio.sleep_ms(100) # type: ignore

try:
    asyncio.run(main_menu())
except KeyboardInterrupt:
    pass