import uasyncio as asyncio
import hardware as hw
import random
from framebuf import FrameBuffer, MONO_HLSB

__long_name__ = "Flappy Bird"

isGameRunning = False
isGameOver = False
score = 0
bird_vel = 0.0
bird_size = 6

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
        hw.play_sound([(400, 30), (600, 30)])

def cheat():
    global bird_size
    if bird_size == 6:
        hw.play_sound([(400, 200), (600, 200), (800, 200)])
        hw.font_default.write("x", 80, 42)
        bird_size = 1
    else:
        hw.play_sound([(800, 200), (600, 200), (400, 200)])
        hw.font_default.write(" ", 80, 42)
        bird_size = 6
    hw.display.show()

async def start():
    global isGameRunning, isGameOver, score, bird_vel, bird_size
    
    hw.buttons.on_press(hw.BTN_A, exit_to_menu)

    hw.display.fill(0)
    hw.font_default.text_centered("MonkeSoft presents:", 0)
    hw.font_default.text_centered("Flappy bird", 10)
    hw.font_default.write(f"RAM Free: {hw.gcMem_free() // 1024} kB", 0, 42)
    hw.display.show()

    await asyncio.sleep(2)

    hw.display.rect(0, 42, 84, 6, 0, True)
    hw.font_default.text_centered("Press C to start", 42)
    hw.display.show()

    hw.buttons.reset_state()
    while True:
        if hw.buttons.was_pressed(hw.BTN_C):
            break
        await asyncio.sleep_ms(100) # type: ignore
    
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
        
        hw.buttons.on_press(hw.BTN_UP, jump)
        hw.buttons.on_combo(hw.BTN_A | hw.BTN_B, cheat)

        hw.play_sound(hw.SND_START, interrupt=True)

        while isGameRunning:
            bird_vel += gravity     # prędkość spadania
            bird_y += bird_vel      # pozycja OY

            hw.display.fill(0)
            
            for p in pipes:     # przesunięcie pozycji rur w OX
                p[0] -= pipe_speed
            
            if pipes[0][0] < -4:    # wykrywanie przejścia miedzy rurami
                pipes.pop(0)
                score += 1
                hw.play_sound([(1500, 30)])
            
            if pipes[-1][0] < 50:   # tworzenie nowej rury
                pipes.append([84, random_int(12, 36)])

            if bird_y > 44 or bird_y < 0:   # wykrycie wypadnięcia ptaka z ekranu
                isGameRunning = False
            
            for p in pipes:     # wykrycie kolizji z rurami
                if 10 < p[0] + 8 and 10 + bird_size > p[0]:
                    if bird_y < p[1] - 8 or bird_y + bird_size > p[1] + 8:
                        isGameRunning = False

            hw.display.blit(bird_fbuf, 10, int(bird_y), 0) # rysowanie ptaka

            for p in pipes: # rysowanie rur
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

if __name__ == "__main__":
    print(f"This file should not be run standalone!")