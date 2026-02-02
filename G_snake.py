import hardware as hw
from hardware import asyncio
import random

__long_name__ = "Snake"

isGameRunning = False
isGameOver = False
direction = (1, 0)
cheatMode = False

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

def changeDir(new_dir):
    global direction
    if (new_dir[0] * -1 != direction[0]) or (new_dir[1] * -1 != direction[1]):
        direction = new_dir

def cheat():
    global cheatMode
    if not cheatMode:
        hw.play_sound(hw.SND_CHEAT_ON)
        cheatMode = True
    else:
        hw.play_sound(hw.SND_CHEAT_OFF)
        cheatMode = False
    hw.display.show()

async def start():
    global isGameRunning, isGameOver, direction

    difficultyLevel = 0
    showStart = 0
    masterLoop = True

    hw.display.fill(0)
    hw.font_default.text_centered("FerencSoft presents:", 0)
    hw.font_default.text_centered(__long_name__, 10)
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
        elif showStart == 8:
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
        direction = (1, 0)
        snake = [(5, 5), (4, 5), (3, 5)]
        food = (randomInt(6, 19), randomInt(3, 10))
        scoreWidth, scoreWeight = 32, 6 # height=6 fixed because of font height
        
        hw.buttons.on_press(hw.BTN_UP,    lambda: changeDir((0, -1)))
        hw.buttons.on_press(hw.BTN_DOWN,  lambda: changeDir((0, 1)))
        hw.buttons.on_press(hw.BTN_LEFT,  lambda: changeDir((-1, 0)))
        hw.buttons.on_press(hw.BTN_RIGHT, lambda: changeDir((1, 0)))
        hw.buttons.on_combo(hw.BTN_A | hw.BTN_B, cheat)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1]) # ustalenie nowej pozycji głowy
            # detekcja kolizji z granicami ekranu
            if new_head[0] < 0 or new_head[0] > 20 or new_head[1] < 0 or new_head[1] > 11:
                isGameRunning = False
            # detekcja kolizji z samym sobą
            if new_head in snake:
                isGameRunning = False

            if isGameRunning:
                snake.insert(0, new_head)
                
                if new_head == food:    # zjedzono jabłko
                    if difficultyLevel == 1 and not cheatMode:
                        score += 2
                    elif difficultyLevel == 2 and not cheatMode:
                        score += 3
                    else:
                        score += 1
                    hw.play_sound([(1500, 30)])
                    while True:     # losowanie nowego jabłka poza wężem 
                        food = (randomInt(0, 20), randomInt(0, 11)) # a także poza obszarem wyniku
                        if food not in snake and ((food[0]*4 > (scoreWidth + 2)) or (food[1]*4 > (scoreWeight + 2))): 
                            break
                else:
                    snake.pop()

            hw.display.fill(0)
            
            # hw.display.rect(food[0]*4, food[1]*4, 4, 4, 1)
            hw.display.ellipse(food[0] * 4 + 2, food[1] * 4 + 2, 2, 2, 1)
            
            for i, segment in enumerate(snake):
                hw.display.ellipse(segment[0] * 4 + 2, segment[1] * 4 + 2, 2, 2, 1, i != 0)
                # hw.display.fill_rect(segment[0]*4, segment[1]*4, 4, 4, 1)
            
            score_text = "Score: %s" % score
            hw.font_default.write(score_text, 0, 0)
            scoreWidth = len(score_text)*4
            hw.display.show()

            if not cheatMode:
                delay = max(30, 150 - (score * (4 if difficultyLevel == 0 else 5 if difficultyLevel == 1 else 6)))
            else:
                delay = 150
        
            if isGameRunning and isGameOver:
                isGameRunning = False
                break

            await asyncio.sleep_ms(delay) # type: ignore

        if not isGameRunning and masterLoop:
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