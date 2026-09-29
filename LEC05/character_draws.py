from pico2d import *
import math

open_canvas(800, 600)

character = load_image('character.png')


def draw_circle():
    print('Circle')
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = 400 + 200 * math.cos(rad)
        y = 300 + 200 * math.sin(rad)
        clear_canvas()
        character.draw(x, y)
        update_canvas()
        delay(0.1)
    pass

def draw_top():
    print ('Top')
    
    pass

def draw_right():
    print('Right')
    pass

def draw_bottom():
    print('Bottom')
    pass

def draw_left():
    print('Left')
    pass

def draw_rectangle():
    print('Rectangle')
    draw_top()
    draw_right()
    draw_bottom()
    draw_left()
    pass

def draw_triangle():
    print('Triangle')
    pass


while True:
    # draw_circle()
    draw_rectangle()
    draw_triangle()
    break
    pass

close_canvas()