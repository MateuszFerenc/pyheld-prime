import random

__long_name__ = "Snake"

class Game:
    def __init__(self, hardware) -> None:
        self.hardware = hardware

        self.isGameRunning = False
        self.isGameOver = False
        self.score = 0
        self.direction = (1, 0)
        self.cheatMode = False

    @staticmethod
    def random_int(min_val, max_val):
        span = max_val - min_val + 1
        return min_val + (random.getrandbits(10) % span)

    def exit_to_menu(self):
        self.isGameRunning = True
        self.isGameOver = True

    def restart_game(self):
        self.isGameOver = False

    def change_dir(self, new_dir):
        if (new_dir[0] * -1 != self.direction[0]) or (new_dir[1] * -1 != self.direction[1]):
            self.direction = new_dir

    def cheat(self):
        if not self.cheatMode:
            self.hardware.sound.play_sound(self.hardware.sound.CHEAT_ON_SND)
            self.cheatMode = True
        else:
            self.hardware.sound.play_sound(self.hardware.sound.CHEAT_OFF_SND)
            self.cheatMode = False
        self.hardware.display.show()

    async def start(self):        
        self.hardware.buttons.on_press(self.hardware.BTN_A, self.exit_to_menu)

        self.hardware.display.fill(0)
        self.hardware.font_default.text_centered("MonkeSoft presents:", 0)
        self.hardware.font_default.text_centered(__long_name__, 10)
        self.hardware.font_default.write(f"RAM Free: {self.hardware.gcMemFree() // 1024} kB", 0, 42)
        self.hardware.display.show()

        await self.hardware.asyncio.sleep(2)

        self.hardware.display.rect(0, 42, 84, 6, 0, True)
        self.hardware.font_default.text_centered("Press C to start", 42)
        self.hardware.display.show()

        self.hardware.buttons.reset_state()
        while True:
            if self.hardware.buttons.was_pressed(self.hardware.BTN_C):
                break
            await self.hardware.asyncio.sleep_ms(100) # type: ignore

        master_loop = True
        while master_loop:
            isGameRunning = True
            isGameOver = False
            score = 0
            direction = (1, 0)
            snake = [(5, 5), (4, 5), (3, 5)]
            food = (self.random_int(6, 19), self.random_int(3, 10))
            score_width, score_height = 32, 6 # height=6 fixed because of font height
            
            self.hardware.buttons.on_press(self.hardware.BTN_UP,    lambda: self.change_dir((0, -1)))
            self.hardware.buttons.on_press(self.hardware.BTN_DOWN,  lambda: self.change_dir((0, 1)))
            self.hardware.buttons.on_press(self.hardware.BTN_LEFT,  lambda: self.change_dir((-1, 0)))
            self.hardware.buttons.on_press(self.hardware.BTN_RIGHT, lambda: self.change_dir((1, 0)))
            self.hardware.buttons.on_press(self.hardware.BTN_A,     self.exit_to_menu)
            self.hardware.buttons.on_combo(self.hardware.BTN_A | self.hardware.BTN_B, self.cheat)

            self.hardware.sound.play_sound(self.hardware.sound.SND_START, interrupt=True)

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
                        self.hardware.sound.play_sound([(1500, 30)])
                        while True:     # losowanie nowego jabłka poza wężem 
                            food = (self.random_int(0, 20), self.random_int(0, 11)) # a także poza obszarem wyniku
                            if food not in snake and ((food[0]*4 > (score_width + 2)) or (food[1]*4 > (score_height + 2))): 
                                break
                    else:
                        snake.pop()

                self.hardware.display.fill(0)
                
                self.hardware.display.ellipse(food[0] * 4 + 2, food[1] * 4 + 2, 2, 2, 1)
                
                for i, segment in enumerate(snake):
                    self.hardware.display.ellipse(segment[0] * 4 + 2, segment[1] * 4 + 2, 2, 2, 1, i != 0)
                
                score_text = f"Score: {score}"
                self.hardware.font_default.write(score_text, 0, 0)
                score_width = len(score_text)*4
                self.hardware.display.show()

                if not self.cheatMode:
                    delay = max(40, 150 - (score * 5))
                else:
                    delay = 150
            
                if isGameRunning and isGameOver:
                    isGameRunning = False
                    break

                await self.hardware.asyncio.sleep_ms(delay) # type: ignore

            if not isGameRunning and master_loop:
                isGameOver = True
                self.hardware.sound.play_sound(self.hardware.sound.SND_DIE, interrupt=True)
                
                self.hardware.buttons.on_press(self.hardware.BTN_C, self.restart_game)
                self.hardware.buttons.on_press(self.hardware.BTN_A, self.exit_to_menu)

                self.hardware.display.fill(0)
                self.hardware.font_default.write("Koniec gry", 5, 5)
                self.hardware.font_default.write(f"Wynik: {score}", 5, 18)
                self.hardware.font_default.write("C-Graj A-Wyjdz", 0, 35)
                self.hardware.display.show()

                while isGameOver:
                    await self.hardware.asyncio.sleep_ms(100) # type: ignore

                    if isGameRunning and isGameOver:
                        master_loop = False
                        break

        self.hardware.buttons.clear_callbacks()

if __name__ == "__main__":
    print(f"This file should not be run standalone!")