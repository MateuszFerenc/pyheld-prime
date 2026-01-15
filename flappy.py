import uasyncio as asyncio
import hardware as hw
import random
from framebuf import FrameBuffer, MONO_HLSB

isGameRunning = False
isGameOver = False
score = 0
bird_vel = 0.0

bird_data = bytearray([
    0x0C, 0x12, 0xC5, 0x22, 0x54, 0x44, 0x38, 0x28
])
bird_fbuf = FrameBuffer(bird_data, 8, 8, MONO_HLSB)

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

def jump():
    global bird_vel
    if isGameRunning:
        bird_vel = -3.2
        hw.play_sound([(600, 30), (800, 30)])

async def start():
    global isGameRunning, isGameOver, score, bird_vel
    
    hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.display.fill(0)
    hw.font_default.text_centered("MonkeSoft presents:", 0)
    hw.font_default.text_centered("Flappy bird", 10)
    hw.display.show()

    await asyncio.sleep(2)

    hw.display.fill(0)
    
    master_loop = True
    while master_loop:
        isGameRunning = True
        isGameOver = False
        score = 0
        bird_y = 20.0
        bird_vel = 0.0
        gravity = 0.45
        pipes = [[84, 24]] 
        pipe_speed = 2
        bird_size = 6 # łatwiej niż 8px
        
        hw.buttons.on_press(hw.BTN_UP, jump)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            bird_vel += gravity
            bird_y += bird_vel
            
            for p in pipes:
                p[0] -= pipe_speed
            
            if pipes[0][0] < -8:
                pipes.pop(0)
                score += 1
                hw.play_sound([(1500, 30)])
            
            if pipes[-1][0] < 50:
                pipes.append([84, random_int(12, 36)])

            if bird_y > 44 or bird_y < 0:
                isGameRunning = False
            
            for p in pipes:
                if 10 < p[0] + 8 and 10 + bird_size > p[0]:
                    if bird_y < p[1] - 8 or bird_y + bird_size > p[1] + 8:
                        isGameRunning = False

            hw.display.fill(0)
            hw.display.blit(bird_fbuf, 10, int(bird_y), 0)

            for p in pipes:
                hw.display.rect(p[0], 0, 8, p[1]-8, 1)
                hw.display.rect(p[0], p[1]+8, 8, 48-(p[1]+8), 1)

            hw.font_default.write(f"Score: {score}", 0, 0)
            hw.display.show()

            if isGameRunning and isGameOver:
                isGameRunning = False
                break
            
            await asyncio.sleep_ms(30) # type: ignore

        if not isGameRunning:
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