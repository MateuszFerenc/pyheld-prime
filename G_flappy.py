import hardware as hw
from hardware import asyncio, framebuf
import random

__long_name__ = "Flappy Bird"

isGameRunning = False
isGameOver = False
birdVel = 0.0
bird_size = 6

bird_data = bytearray([
    0x0C, 0x12, 0xC5, 0x22, 0x54, 0x44, 0x38, 0x28
])
bird_fbuf = framebuf.FrameBuffer(bird_data, 8, 8, framebuf.MONO_HLSB)

def randomInt(min_val, max_val):
    span = max_val - min_val + 1
    return min_val + (random.getrandbits(10) % span)

def exitToMenu():
    global isGameRunning, isGameOver
    isGameRunning = True
    isGameOver = True

def restartGame():
    global isGameOver
    isGameOver = False

def jump():
    global birdVel
    if isGameRunning:
        birdVel = -2.8#-3.2
        hw.play_sound([(400, 30), (600, 30)])

def cheat():
    global bird_size
    if bird_size == 6:
        hw.play_sound([(400, 200), (600, 200), (800, 200)])
        bird_size = 1
    else:
        hw.play_sound([(800, 200), (600, 200), (400, 200)])
        bird_size = 6

async def start():
    global isGameRunning, isGameOver, birdVel, bird_size
    
    difficultyLevel = 0
    showStart = 0
    masterLoop = True

    hw.display.fill(0)
    hw.font_default.text_centered("FerencSoft presents:", 0)
    hw.font_default.text_centered(__long_name__, 10)
    # .format ??????? 
    # and b'text' as bytes?
    hw.font_default.write("RAM Free: %skB" % round(hw.gcMem_free() / 1024, 2), 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    hw.buttons.on_press(hw.BTN_A, exitToMenu)
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
    
    if isGameRunning and isGameOver:
        masterLoop = False

    while masterLoop:
        isGameRunning = True
        isGameOver = False
        score = 0
        birdY = 20.0
        birdVel = 0.0
        gravity = 0.35 if difficultyLevel == 0 else 0.45 if difficultyLevel == 1 else 0.7
        pipes = [[84, 24]] 
        pipeSpeed = 2
        
        hw.buttons.on_press(hw.BTN_UP, jump)
        hw.buttons.on_combo(hw.BTN_A | hw.BTN_B, cheat)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            birdVel += gravity     # prędkość spadania
            birdY += birdVel      # pozycja OY

            hw.display.fill(0)
            
            for p in pipes:     # przesunięcie pozycji rur w OX
                p[0] -= pipeSpeed
            
            if pipes[0][0] < -4:    # wykrywanie przejścia miedzy rurami
                pipes.pop(0)
                score += 1
                hw.play_sound([(1500, 30)])
            
            if pipes[-1][0] < 50:   # tworzenie nowej rury
                pipes.append([84, randomInt(12, 36)])

            if birdY > 44 or birdY < 0:   # wykrycie wypadnięcia ptaka z ekranu
                isGameRunning = False
            
            for p in pipes:     # wykrycie kolizji z rurami
                if 10 < p[0] + 8 and 10 + bird_size > p[0]:
                    if birdY < p[1] - 8 or birdY + bird_size > p[1] + 8:
                        isGameRunning = False

            hw.display.blit(bird_fbuf, 10, int(birdY), 0) # rysowanie ptaka

            for p in pipes: # rysowanie rur
                hw.display.rect(p[0], 0, 8, p[1]-8, 1)
                hw.display.rect(p[0], p[1]+8, 8, 48-(p[1]+8), 1)

            hw.font_default.write("Score: %s" % score, 0, 0)
            hw.display.show()

            if isGameRunning and isGameOver:
                isGameRunning = False
                break
            
            await asyncio.sleep_ms(30) # type: ignore

        if not isGameRunning:
            isGameOver = True
            hw.play_sound(hw.SND_DIE, interrupt=True)
            
            hw.buttons.on_press(hw.BTN_C, restartGame)

            hw.display.fill(0)
            hw.font_default.write("%s score: %s" % (("EASY" if difficultyLevel == 0 else "MEDIUM" if difficultyLevel == 1 else "HARD"), score), 5, 18)
            hw.font_default.text_centered("C-Play again A-Exit", 35)
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
    print("This file should not be run standalone!")