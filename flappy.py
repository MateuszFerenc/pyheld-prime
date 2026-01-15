import uasyncio as asyncio
import hardware as hw

isGameRunning = False

def exit_game():
    global isGameRunning
    isGameRunning = False

async def start():
    global isGameRunning
    isGameRunning = True
    
    hw.buttons.on_press(hw.BTN_C, exit_game)
    
    hw.play_sound(hw.SND_START, interrupt=True)
    
    while isGameRunning:
        # Główna logika gry.
        # hw.play_sound(((440, 50), (400, 50)))
        # print(state["running"])
        await asyncio.sleep_ms(10) # type: ignore
    
    hw.buttons.clear_callbacks()
    hw.display.fill(0)
    hw.font_default.write("KONIEC", 25, 20, 1)
    hw.display.show()
    await asyncio.sleep(1)