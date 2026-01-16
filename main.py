import uasyncio as asyncio
import hardware as hw

power_up_snd = [(440, 100), (880, 100), (1760, 150)]
up_snd = [(500, 100), (760, 100)]
down_snd = [(760, 100), (500, 100)]

barka_nuty = [
    # Takt 1-2: (Pauza) "Pan..."
    (370, 750),     # FIS (ćwierćnuta z kropką)
    
    # Takt 3: "...kie-dyś sta-nął..."
    (330, 250),     # MI (E4)
    (370, 250),     # FIS (F#4)
    (392, 250),     # SOL (G4)
    (370, 250),     # FIS (F#4)
    (330, 250),     # MI (E4)
    
    # Takt 4-5: "...nad brze-giem..."
    (293, 750),     # RE (D4)
    (293, 500),     # RE (D4) - ćwierćnuta
    (330, 250),     # MI (E4) - ósemka
    
    # Takt 6-7: "Szu-kał lu-dzi..."
    (370, 750),     # FIS (F#4)
    (392, 250),     # SOL (G4)
    (392, 250),     # SOL (G4)
    (392, 250),     # SOL (G4)
    (370, 250),     # FIS (F#4)
    
    # Takt 8-9: "...go-to-wych..."
    (330, 750),     # MI (E4)
    (330, 500),     # MI (E4)
    (330, 250),     # MI (E4)
    
    # Takt 10: "...pójść za Nim"
    (330, 250),     # MI (E4)
    (293, 250),     # RE (D4)
    (330, 250),     # MI (E4)
    (370, 750),     # FIS (F#4)
    
    # Takt 11-12: (Łącznik do kolejnej frazy)
    (370, 750)      # FIS (F#4)
]

async def main_menu():
    hw.show_system_info()
    await asyncio.sleep(2)

    hw.show_pbm("logo.pbm")
    hw.play_sound(power_up_snd)
    await asyncio.sleep(2)

    asyncio.create_task(hw.buttons.scan_task())
    hw.buttons.on_combo(hw.BTN_LEFT | hw.BTN_RIGHT, lambda: hw.play_sound(barka_nuty))

    games = (("Flappy Bird", "flappy"), ("Pacman", "pacman"), ("Snake", "snake"))
    selected = 0 
    while True: 
        hw.display.fill(0) 
        hw.font_default.write("WYBIERZ GRE:", 0, 0)
        for i, name in enumerate(games): 
            prefix = ">" if i == selected else " " 
            hw.font_default.write(prefix + name[0], 5, 15 + (i*10))
        hw.display.show()
        
        if hw.buttons.was_pressed(hw.BTN_C): # Przycisk START
           hw.buttons.reset_state()
           await hw.run_game(games[selected][1])
           hw.buttons.reset_state()
           hw.buttons.clear_callbacks()

        if hw.buttons.was_pressed(hw.BTN_UP): # Przycisk Up
            selected = (selected - 1) % len(games) 
            hw.play_sound(up_snd)
            await asyncio.sleep_ms(10)  # type: ignore

        if hw.buttons.was_pressed(hw.BTN_DOWN): # Przycisk Down 
            selected = (selected + 1) % len(games) 
            hw.play_sound(down_snd)
            await asyncio.sleep_ms(10)  # type: ignore
            
        await asyncio.sleep_ms(100) # type: ignore

try:
    asyncio.run(main_menu())
except KeyboardInterrupt:
    pass