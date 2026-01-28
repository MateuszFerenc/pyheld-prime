import hardware as hw
from hardware import asyncio, framebuf

__long_name__ = "Stack attack"

def exit_to_menu():
    global isGameRunning, isGameOver
    isGameRunning = True
    isGameOver = True

def restart_game():
    global isGameOver
    isGameOver = False

async def start():
    
    hw.display.fill(0)
    # hw.font_default.text_centered("Siemens Mobile game", 0)
    # hw.font_default.text_centered("remade by MonkeSoft:", 6)
    hw.font_default.text_centered("Siemens Mobile game remade by MonkeSoft:", 0)
    # text_centered multiline buggy
    hw.font_default.text_centered(__long_name__, 20)
    hw.font_default.write("RAM Free: %skB" % round(hw.gcMem_free() / 1024, 2), 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    hw.display.load_pbm("sa_w.pbm")
    hw.display.rect(0, 42, 84, 6, 0, True)
    hw.font_default.text_centered("Press C to start", 42)
    hw.display.show()

    hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.buttons.reset_state()
    while True:
        if hw.buttons.was_pressed(hw.BTN_C):
            break
        await asyncio.sleep_ms(100) # type: ignore

    # master_loop = True
    # while master_loop:
    #     pass

    hw.buttons.clear_callbacks()

if __name__ == "__main__":
    print("This file should not be run standalone!")