import uasyncio as asyncio
import hardware as hw
import random

isGameRunning = False
isGameOver = False
score = 0
direction = (1, 0)

def random_int(min_val, max_val):
    span = max_val - min_val + 1
    return min_val + (random.getrandbits(10) % span)

def exit_to_menu():
    global isGameRunning, isGameOver
    isGameRunning = True
    isGameOver = True

def restart_game():
    global isGameOver
    isGameOver = False

def change_dir(new_dir):
    global direction
    if (new_dir[0] * -1 != direction[0]) or (new_dir[1] * -1 != direction[1]):
        direction = new_dir

async def start():
    global isGameRunning, isGameOver, score, direction
    
    hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.display.fill(0)
    hw.font_default.text_centered("MonkeSoft presents:", 0)
    hw.font_default.text_centered("Snake", 10)
    hw.display.show()

    await asyncio.sleep(2)

    master_loop = True
    while master_loop:
        isGameRunning = True
        isGameOver = False
        score = 0
        direction = (1, 0)
        snake = [(5, 5), (4, 5), (3, 5)]
        food = (random_int(0, 20), random_int(0, 11))
        
        hw.buttons.on_press(hw.BTN_UP,    lambda: change_dir((0, -1)))
        hw.buttons.on_press(hw.BTN_DOWN,  lambda: change_dir((0, 1)))
        hw.buttons.on_press(hw.BTN_LEFT,  lambda: change_dir((-1, 0)))
        hw.buttons.on_press(hw.BTN_RIGHT, lambda: change_dir((1, 0)))
        hw.buttons.on_press(hw.BTN_A,     exit_to_menu)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

            if new_head[0] < 0 or new_head[0] > 20 or new_head[1] < 0 or new_head[1] > 11:
                isGameRunning = False
            
            if new_head in snake:
                isGameRunning = False

            if isGameRunning:
                snake.insert(0, new_head)
                
                if new_head == food:
                    score += 1
                    hw.play_sound([(1500, 30)])
                    while True:
                        food = (random_int(0, 20), random_int(0, 11))
                        if food not in snake: break
                else:
                    snake.pop()

            hw.display.fill(0)
            
            hw.display.rect(food[0]*4, food[1]*4, 4, 4, 1)
            
            for segment in snake:
                hw.display.fill_rect(segment[0]*4, segment[1]*4, 4, 4, 1)
            
            hw.font_default.write("Score: {}".format(score), 0, 0)
            hw.display.show()

            delay = max(40, 150 - (score * 5))
        
            if isGameRunning and isGameOver:
                isGameRunning = False
                break

            await asyncio.sleep_ms(delay) # type: ignore

        if not isGameRunning and master_loop:
            isGameOver = True
            hw.play_sound(hw.SND_DIE, interrupt=True)
            
            hw.buttons.on_press(hw.BTN_C, restart_game)
            hw.buttons.on_press(hw.BTN_A, exit_to_menu)

            hw.display.fill(0)
            hw.font_default.write("Koniec gry", 5, 5)
            hw.font_default.write("Wynik: {}".format(score), 5, 18)
            hw.font_default.write("C-Graj A-Wyjdz", 0, 35)
            hw.display.show()

            while isGameOver:
                await asyncio.sleep_ms(100) # type: ignore

                if isGameRunning and isGameOver:
                    master_loop = False
                    break

    hw.buttons.clear_callbacks()