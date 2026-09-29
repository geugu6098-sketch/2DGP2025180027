from pico2d import *
import math

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

# 궤적을 따라 움직일 캐릭터
character = load_image('character.png')


def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.02)


draw_character(400, 300)

close_canvas()
