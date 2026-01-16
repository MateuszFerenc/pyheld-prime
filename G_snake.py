import uasyncio as asyncio
import hardware as hw
import random

__long_name__ = "Snake"

isGameRunning = False
isGameOver = False
score = 0
direction = (1, 0)
cheatMode = False

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

def cheat():
    global cheatMode
    if not cheatMode:
        hw.play_sound([(400, 200), (600, 200), (800, 200)])
        cheatMode = True
    else:
        hw.play_sound([(800, 200), (600, 200), (400, 200)])
        cheatMode = False
    hw.display.show()

async def start():
    global isGameRunning, isGameOver, score, direction
    
    hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.display.fill(0)
    hw.font_default.text_centered("MonkeSoft presents:", 0)
    hw.font_default.text_centered("Snake", 10)
    hw.font_default.write(f"RAM Free: {hw.gcMem_free() // 1024} kB", 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    master_loop = True
    while master_loop:
        isGameRunning = True
        isGameOver = False
        score = 0
        direction = (1, 0)
        snake = [(5, 5), (4, 5), (3, 5)]
        food = (random_int(6, 19), random_int(3, 10))
        score_width, score_height = 32, 6 # height=6 fixed because of font height
        
        hw.buttons.on_press(hw.BTN_UP,    lambda: change_dir((0, -1)))
        hw.buttons.on_press(hw.BTN_DOWN,  lambda: change_dir((0, 1)))
        hw.buttons.on_press(hw.BTN_LEFT,  lambda: change_dir((-1, 0)))
        hw.buttons.on_press(hw.BTN_RIGHT, lambda: change_dir((1, 0)))
        hw.buttons.on_press(hw.BTN_A,     exit_to_menu)
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
                    score += 1
                    hw.play_sound([(1500, 30)])
                    while True:     # losowanie nowego jabłka poza wężem 
                        food = (random_int(0, 20), random_int(0, 11)) # a także poza obszarem wyniku
                        if food not in snake and ((food[0]*4 > (score_width + 2)) or (food[1]*4 > (score_height + 2))): 
                            break
                else:
                    snake.pop()

            hw.display.fill(0)
            
            # hw.display.rect(food[0]*4, food[1]*4, 4, 4, 1)
            hw.display.ellipse(food[0] * 4 + 2, food[1] * 4 + 2, 2, 2, 1)
            
            for i, segment in enumerate(snake):
                hw.display.ellipse(segment[0] * 4 + 2, segment[1] * 4 + 2, 2, 2, 1, i != 0)
                # hw.display.fill_rect(segment[0]*4, segment[1]*4, 4, 4, 1)
            
            score_text = f"Score: {score}"
            hw.font_default.write(score_text, 0, 0)
            score_width = len(score_text)*4
            hw.display.show()

            if not cheatMode:
                delay = max(40, 150 - (score * 5))
            else:
                delay = 150
        
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
            hw.font_default.write(f"Wynik: {score}", 5, 18)
            hw.font_default.write("C-Graj A-Wyjdz", 0, 35)
            hw.display.show()

            while isGameOver:
                await asyncio.sleep_ms(100) # type: ignore

                if isGameRunning and isGameOver:
                    master_loop = False
                    break

    hw.buttons.clear_callbacks()

if __name__ == "__main__":
    print(f"This file should not be run standalone!")