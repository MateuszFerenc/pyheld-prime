import hardware as hw
from hardware import asyncio

__long_name__ = "Pong"

isGameRunning = False
isGameOver = False

def exitToMenu():
    global isGameRunning, isGameOver
    isGameRunning = True
    isGameOver = True

def restartGame():
    global isGameOver
    isGameOver = False

async def start():
    global isGameRunning, isGameOver

    difficultyLevel = 0
    pvpMode = True
    showStart = 0
    masterLoop = True
    paddleLength = 10
    paddleHalfLength = paddleLength // 2
    paddleWidth = 5
    paddlePosDelta = 4

    hw.display.fill(0)
    hw.font_default.text_centered("FerencSoft presents:", 0)
    hw.font_default.text_centered(__long_name__, 10)
    hw.font_default.write("RAM Free: %skB" % round(hw.gcMem_free() / 1024, 2), 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    hw.font_default.text_centered("Mode: %s" % ("P vs P" if pvpMode else "P vs C"), 36)

    hw.buttons.on_press(hw.BTN_B, exitToMenu)
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
        if hw.buttons.was_pressed(hw.BTN_LEFT | hw.BTN_RIGHT):
            pvpMode ^= True
            hw.display.rect(0, 36, 84, 6, 0, True)
            hw.font_default.text_centered("Mode: %s" % ("P vs P" if pvpMode else "P vs C"), 36)
        if showStart == 0:
            hw.display.rect(0, 42, 84, 6, 0, True)
            hw.font_default.text_centered("Press C to start", 42)
        elif showStart == 8:
            hw.display.rect(0, 42, 84, 6, 0, True)
            hw.font_default.text_centered("Difficulty: %s" % ("EASY" if difficultyLevel == 0 else "MEDIUM" if difficultyLevel == 1 else "HARD"), 42)
        showStart += 1
        if showStart == 12:
            showStart = 0
        hw.display.show()
        await asyncio.sleep_ms(150) # type: ignore

    hw.buttons.reset_state()

    if isGameRunning and isGameOver:
        masterLoop = False
    
    while masterLoop:
        isGameRunning = True
        isGameOver = False

        paddleA_pos = hw.display.height // 2 - paddleHalfLength
        paddleB_pos = paddleA_pos
        ballPos = [hw.display.width / 2, hw.display.height / 2]
        ballVel = [0.0, 0.0]
        ballAccel = 0.5
        scoreA = 0
        scoreB = 0

        hw.buttons.on_press(hw.BTN_B, exitToMenu)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            hw.display.fill(0)

            hw.display.rect(0, paddleA_pos, paddleWidth, paddleLength, 1, 1)
            hw.display.rect(84 - paddleWidth, paddleB_pos, paddleWidth, paddleLength, 1, 1)

            hw.display.ellipse(int(ballPos[0]), int(ballPos[1]), 2, 2, 1)

            # test ball
            hw.display.rect(int(ballPos[0]) - 2, abs(paddleA_pos + paddleHalfLength - int(ballPos[1])) - 2, 5, 5, 1)

            hw.font_default.text_centered("A: %s   B: %s" % (scoreA, scoreB), 0)

            hw.display.show()

            if pvpMode:
                if hw.buttons.is_pressed(hw.BTN_UP):
                    print(f"ballPosDelta: {paddleLength + paddleA_pos - int( ballPos[1])}, paddleA_pos: {paddleA_pos}")
                    paddleA_pos -= paddlePosDelta
                    if paddleA_pos < 0:
                        paddleA_pos = 0
                    # if (paddleA_pos - paddlePosDelta) >= 0:
                    #     paddleA_pos -= paddlePosDelta
                if hw.buttons.is_pressed(hw.BTN_DOWN):
                    print(f"ballPosDelta: {paddleLength + paddleA_pos - int(ballPos[1])}, paddleA_pos: {paddleA_pos}")
                    paddleA_pos += paddlePosDelta
                    if paddleA_pos > (48 - paddleLength):
                        paddleA_pos = 48 - paddleLength
                    # if (paddleA_pos - paddlePosDelta) <= (hw.display.height - paddleLength):
                    #     paddleA_pos += min(48 - paddleA_pos, paddlePosDelta)
            else:   # computer move
                ballPosDelta = paddleLength + paddleA_pos - ballPos[1]
                paddleA_pos += int(ballPosDelta)
            if hw.buttons.is_pressed(hw.BTN_A):
                # if (paddleB_pos - paddlePosDelta) >= 0:
                paddleB_pos -= paddlePosDelta
                if paddleB_pos < 0:
                    paddleB_pos = 0
            if hw.buttons.is_pressed(hw.BTN_C):
                paddleB_pos += paddlePosDelta
                if paddleB_pos > (48 - paddleLength):
                    paddleB_pos = 48 - paddleLength
                # if (paddleB_pos - paddlePosDelta) < (hw.display.height - paddleLength):
                #     paddleB_pos += min(48 - paddleB_pos, paddlePosDelta)
                #     ballPos[1] += paddlePosDelta

            if abs(scoreA - scoreB) == 0 and scoreA != scoreB:
                isGameRunning = False
                break

            if isGameRunning and isGameOver:
                isGameRunning = False
                break
            
            await asyncio.sleep_ms(30) # type: ignore

        if not isGameRunning:
            isGameOver = True
            hw.play_sound(hw.SND_DIE, interrupt=True)
            
            hw.buttons.on_press(hw.BTN_C, restartGame)

            hw.display.fill(0)
            hw.font_default.write("%s %s" % (("EASY" if difficultyLevel == 0 else "MEDIUM" if difficultyLevel == 1 else "HARD"), ("P vs P" if pvpMode else "P vs C")), 5, 18)
            hw.font_default.text_centered("Score - A: %s B: %s" % (scoreA, scoreB), 24)
            hw.font_default.text_centered("C-Play again B-Exit", 35)
            hw.display.show()
            inverted = 0

            while isGameOver: 
                if inverted == 0:
                    hw.font_default.text_centered("GAME OVER", 5, 1, 0)
                elif inverted == 4:
                    hw.font_default.text_centered("GAME OVER", 5, 0, 1)
                inverted += 1
                if inverted == 8:
                    inverted = 0
                hw.display.show()

                if isGameRunning and isGameOver:
                    masterLoop = False
                    break

                await asyncio.sleep_ms(150) # type: ignore

    hw.buttons.clear_callbacks()

if __name__ == "__main__":
    print(f"This file should not be run standalone!")