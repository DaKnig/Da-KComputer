"""proto 3d engine"""
"""inspired by bisqwit"""
"""
note to self - common instructions:
    - abs jump
    - skip next inst - just invalidate its writeback...
    - gtz, ltz, ez, nez - flags, after sub, selected from a word
         known beforehand from the vector- (v[1]-v[2])[1]
    - scalars:
        - how many?
        - specialized load-increment. - v[1] = *count++ etc. or not?
        - choose result from vec operation - scalar = (v[1]-v[2])[3]
        - scalar ALU? or load from scalars to vec? sc1 += sc2

??  - writeback with mask - only save
"""

import numpy as np
import pygame
import pdb

def putxy(pixvec):
    pixvec = [int(n) for n in pixvec]
    d.set_at((pixvec[0],pixvec[1]),pygame.Color(*pixvec[3:6]))

def draw_line(y,counter = [0]): # singleton
    v = np.array( [[0.]*8] *8) # 8 vectors of xyz rgb nc nc

    v[1] = vram[counter]; counter[0]+=1
    v[2] = vram[counter]; counter[0]+=1
    v[3] = vram[counter]; counter[0]+=1

    # sort triangles like so
    #  v1
    # v2
    #   v3  # sorted by y
    #pdb.set_trace()
    if (v[1] - v[2])[1] > 0:
        v[1] , v[2] = v[2].copy(), v[1].copy()
    if (v[1] - v[3])[1] > 0:
        v[1] , v[3] = v[3].copy(), v[1].copy()
    if (v[2] - v[3])[1] > 0:
        v[2] , v[3] = v[3].copy(), v[2].copy()

    if y < v[1][1] or y > v[3][1]: # if outside the triangle...
        return
    if (v[3]-v[1])[1] < 1: # if there's 0 lines to draw...
        return

    # which bends, left or right?
    bend = (v[2] - v[1])[1] * (v[3] - v[1])[0] < \
           (v[2] - v[1])[0] * (v[3] - v[1])[1]
    # false=left side, true=right side; line 38 rasterize.hh. shortside.

    # swap later ... if bend. # assume bend = 1
    side_slopes = np.array([[0.]*8]*2) # "slopes" 0,1 for left, right # v6,v7?
    current_line_bounds = np.array([[0.]*8]*2)

    side_slopes[0] = v[3] - v[1]
    side_slopes[0] = side_slopes[0] / side_slopes[0][1] # left slope over y
    current_line_bounds[0] = v[3] + side_slopes[0] * (y-v[3][1])


    if y < v[2][1]:
        side_slopes[1] = v[2] - v[1]
        side_slopes[1] = side_slopes[1] / side_slopes[1][1] # right slope over y
        current_line_bounds[1] = v[2] + side_slopes[1] * (y-v[2][1])
    else:
        side_slopes[1] = v[3] - v[2]
        side_slopes[1] = side_slopes[1] / side_slopes[1][1] # right slope over y
        current_line_bounds[1] = v[3] + side_slopes[1] * (y-v[3][1])


    if (not bend) == True: # swap
        side_slopes[0], side_slopes[1] = \
            side_slopes[1].copy(), side_slopes[0].copy()
        current_line_bounds[0], current_line_bounds[1] = \
            current_line_bounds[1].copy(), current_line_bounds[0].copy()

    v[0] = current_line_bounds[1]-current_line_bounds[0]
    if v[0][0] == 0:
        return
    v[0] = v[0]/v[0][0] # going left to right with v[0] as slope over x

    walker = current_line_bounds[0]
    while (walker[0] < current_line_bounds[1][0]):
        # check z
        putxy(walker)
        walker += v[0]

def draw_triangle(k): # draw triangle saved at vram 3k, 3k+1, 3k+2
    for i in range(500):
        draw_line(i,[3*k])
    pygame.display.update()


def main():
    pygame.init()
    global d
    global vram
    global line_buffer

    d = pygame.display.set_mode((800,600))

    vram = np.array([#x y z param param param
        [0.01,0.01,0.01,4,5,100,7,8],
        [100,200,30,4,200,6,7,8],
        [200,100,30,200,50,60,70,80],
    ])

    line_buffer = np.array([
        [32000,0,0,0] # far, black
        *800]*2) # dual buffer; 800 pixels. each has z and color
    pdb.set_trace()
    draw_triangle(0)

pdb.set_trace()
main()
pygame.display.update()

import sys
import time
try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise Exception()
        time.sleep(1/5)
        pygame.display.update() 
except:
    pygame.quit()
