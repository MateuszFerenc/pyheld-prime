import uasyncio as asyncio
import hardware as hw
import random

isGameRunning = False
score = 0

def exit_game():
    global isGameRunning
    isGameRunning = False

def jump():
    global bird_vel
    bird_vel = -3.5
    hw.play_sound([(600, 30), (800, 30)])

def randint(min, max):
    return random.getrandbits(10) % (max - min + 1) + min

async def start():
    global isGameRunning, score, bird_vel
    isGameRunning = True
    score = 0
    
    bird_y = 20.0
    bird_vel = 0.0
    gravity = 0.5
    
    pipes = []
    pipe_speed = 2
    pipe_width = 8
    gap_height = 16
    
    def spawn_pipe():
        pipes.append([84, randint(10, 30)])

    spawn_pipe()

    hw.buttons.on_press(hw.BTN_A, exit_game) # Wyjście
    hw.buttons.on_press(hw.BTN_UP, jump)     # Skok
    
    hw.play_sound(hw.SND_START, interrupt=True)
    
    while isGameRunning:
        bird_vel += gravity
        bird_y += bird_vel
        
        for p in pipes:
            p[0] -= pipe_speed
            
        if pipes[0][0] < -pipe_width:
            pipes.pop(0)
            score += 1
            hw.play_sound([(1200, 20)])
            
        if pipes[-1][0] < 50:
            spawn_pipe()

        if bird_y > 44 or bird_y < 0:
            isGameRunning = False
            
        bird_rect = (10, int(bird_y), 4, 4) # x, y, w, h
        for p in pipes:
            if 10 < p[0] + pipe_width and 10 + 4 > p[0]:
                if bird_y < p[1] - (gap_height // 2) or bird_y + 4 > p[1] + (gap_height // 2):
                    isGameRunning = False

        hw.display.fill(0)

        hw.display.rect(10, int(bird_y), 4, 4, 1)
        
        for p in pipes:
            upper_h = p[1] - (gap_height // 2)
            lower_y = p[1] + (gap_height // 2)
            hw.display.rect(p[0], 0, pipe_width, upper_h, 1)
            hw.display.rect(p[0], lower_y, pipe_width, 48 - lower_y, 1)
            
        hw.font_default.write(f"Score: {score}", 70, 0)
        
        hw.display.show()
        
        await asyncio.sleep_ms(30) # type: ignore
    
    # --- Koniec gry ---
    hw.play_sound(hw.SND_DIE, interrupt=True)
    hw.buttons.clear_callbacks()
    hw.display.fill(0)
    hw.display.text("KONIEC", 15, 10, 1)
    hw.display.text("WYNIK: " + str(score), 10, 25, 1)
    hw.display.show()
    await asyncio.sleep(2)