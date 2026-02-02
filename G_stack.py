import hardware as hw
from hardware import asyncio, framebuf

__long_name__ = "Stack attack"

# def exit_to_menu():
#     global isGameRunning, isGameOver
#     isGameRunning = True
#     isGameOver = True

# def restart_game():
#     global isGameOver
#     isGameOver = False

async def start():
    difficultyLevel = 0
    showStart = 0
    
    hw.display.fill(0)
    hw.font_default.text_centered("Siemens Mobile game remade by FerencSoft:", 0)
    hw.font_default.text_centered(__long_name__, 20)
    hw.font_default.write("RAM Free: %skB" % round(hw.gcMem_free() / 1024, 2), 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    hw.display.load_pbm("sa_w.pbm")
    hw.display.show()

    # hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.buttons.reset_state()
    while True:
        if hw.buttons.was_pressed(hw.BTN_C):
            break
        if hw.buttons.was_pressed(hw.BTN_UP):
            if difficultyLevel < 3:
                difficultyLevel += 1
        if hw.buttons.was_pressed(hw.BTN_DOWN):
            if difficultyLevel > 0:
                difficultyLevel -= 1
        if showStart == 0:
            hw.display.rect(0, 42, 84, 6, 0, True)
            hw.font_default.text_centered("Press C to start", 42)
        if showStart == 8:
            hw.display.rect(0, 42, 84, 6, 0, True)
            hw.font_default.text_centered("Difficulty: %s" % ("EASY" if difficultyLevel == 0 else "MEDIUM" if difficultyLevel == 1 else "HARD"), 42)
        showStart += 1
        if showStart == 12:
            showStart = 0
        hw.display.show()
        await asyncio.sleep_ms(150) # type: ignore

    # master_loop = True
    # while master_loop:
    #     pass

    hw.buttons.clear_callbacks()

if __name__ == "__main__":
    print("This file should not be run standalone!")