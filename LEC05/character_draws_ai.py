from pico2d import *
from pico2d import draw_filled_circle
from pico2d import set_color
import math

character = load_image('character.png')

def draw_character(x, y):
    set_color(255, 220, 180)
    draw_filled_circle(x, y + 30, 18)
    set_color(70, 120, 220)
    draw_rectangle(x - 15, y - 20, x + 15, y + 20)
    set_color(0, 0, 0)
    draw_filled_circle(x - 6, y + 34, 2)
    draw_filled_circle(x + 6, y + 34, 2)
    draw_line(x - 6, y + 24, x + 6, y + 24)


def handle_events():
    global running
    for event in get_events():
        if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
            running = False


def draw():
    global frame
    clear_canvas()

    # Circle
    angle = frame * 0.04
    draw_character(160 + 70 * math.cos(angle), 360 + 70 * math.sin(angle))

    # Rectangle, traversed continuously around its four sides
    rectangle = [(430, 290), (570, 290), (570, 430), (430, 430)]
    side = (frame // 60) % len(rectangle)
    t = (frame % 60) / 60.0
    a, b = rectangle[side], rectangle[(side + 1) % len(rectangle)]
    draw_character(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    # Triangle, traversed continuously around its three sides
    triangle = [(770, 290), (910, 430), (770, 430)]
    side = (frame // 60) % len(triangle)
    t = (frame % 60) / 60.0
    a, b = triangle[side], triangle[(side + 1) % len(triangle)]
    draw_character(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    update_canvas()
    frame += 1

open_canvas(1000, 720)
running = True
frame = 0
while running:
    handle_events()
    draw()
    delay(0.02)
close_canvas()