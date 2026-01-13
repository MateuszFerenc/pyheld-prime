import framebuf

class RotatedProxy:
    def __init__(self, real_fb, width, height):
        self.fb = real_fb  # Oryginalny PCD8544_FB
        self.w = width
        self.h = height

    def pixel(self, x, y, c=None):
        # Transformacja współrzędnych 180 stopni
        tx = self.w - 1 - x
        ty = self.h - 1 - y
        if c is None:
            return self.fb.pixel(tx, ty)
        self.fb.pixel(tx, ty, c)

    def fill_rect(self, x, y, w, h, c):
        self.fb.fill_rect(self.w - x - w, self.h - y - h, w, h, c)

    def hline(self, x, y, w, c):
        self.fb.hline(self.w - x - w, self.h - 1 - y, w, c)

    def vline(self, x, y, h, c):
        self.fb.vline(self.w - 1 - x, self.h - y - h, h, c)

    def fill(self, c):
        self.fb.fill(c)

    def blit(self, src, x, y, key=-1, palette=None):
        # Standardowy blit nie wie o wymiarach src w MicroPythonie.
        # Ta metoda musi tu być, aby nie wyrzucało błędu, ale 
        # dla czcionek użyjemy draw_glyph.
        pass

    def draw_glyph(self, glyph_fb, x, y, w, h, key, palette):
        """Metoda dedykowana dla ezFBfont - rysuje glif piksel po pikselu z rotacją"""
        for sy in range(h):
            for sx in range(w):
                px = glyph_fb.pixel(sx, sy)
                if px != key:
                    # Rysujemy używając naszej obróconej metody pixel
                    self.pixel(x + sx, y + sy, px)