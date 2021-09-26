
# https://stackoverflow.com/questions/5414639/python-imaging-library-text-rendering

import matplotlib.pyplot as plt
import numpy as np
from wand.color import Color
from wand.image import Image
from wand.drawing import Drawing
from wand.compat import nested

import time

def create_coordinate_image(x, y, res_power=8):
    width = 2**res_power
    with Drawing() as draw:
        #with Image(width=width, height=width, background=Color("lightblue")) as img:
        img = Image(width=width, height=width, background=Color("white"))
        
        draw.font_family = 'consolas'
        draw.font_size = width * 0.75
        draw.text_antialias = False
        draw.text_alignment = 'center'
        
        draw.push()
        draw.fill_color = Color('black')

        text = chr(ord('A') + x) + str(int(y))
        draw.text(width//2, int(width * (3/4)), text)
        draw.pop()
        draw(img)

        #img.destroy()
        return img

def create_sdf(img):
    sdf = img.clone()

    t = time.time()
    #find a list of all the font and background points
    black = Color('black')
    pts_font = []
    pts_bg = []
    for x in range(img.width):
        for y in range(img.height):
            if img[x][y] == black:
                pts_font.append((x, y))
            else:
                pts_bg.append((x, y))
    print("pixel sort took %.4f seconds"%(time.time() - t))

    t = time.time()
    #find points on boundary
    #    (reduces dimension by one)
    pts_font_boundary = []
    for pt in pts_font:
        c = img[pt[0]][pt[1]]
        
        bound = False
        for x,y in [(1,0),(-1,0),(0,1),(0,-1)]:
            if img[pt[0] + x][pt[1] + y] != c:
                bound = True
        if bound:
            pts_font_boundary.append(pt)
    print("boundary sort took %.4f seconds"%(time.time() - t))
    
    t = time.time()
    with Drawing() as draw:        
        draw.fill_color = Color('red')
        for pt in pts_font_boundary:
            draw.point(pt[1], pt[0])
        draw(sdf)
    print("boundary color took %.4f seconds"%(time.time() - t))

    def Norm(pt1, pt2):
        pt1 = np.array(pt1)
        pt2 = np.array(pt2)
        dp = pt2-pt1
        return np.dot(dp, dp)

    t = time.time()
    #for each white point, find the closest black point
    for bg_pt in pts_bg:
        #find the closest black point
        closest = pts_font_boundary[0]
        norm = Norm(closest, bg_pt)
        for fo_pt in pts_font_boundary[1:]:
            n = Norm(fo_pt, bg_pt)
            if n < norm:
                norm = n
                closest = fo_pt

        #find its clamped distance
        dist = int(np.sqrt(norm) * 10)
        if 255 < dist:
            dist = 255
            
        #set the pixel color on the sdf image
        with Drawing() as draw:
            draw.fill_color = Color('#'+("%02x"%(dist))*3)
            draw.point(bg_pt[1], bg_pt[0])
            draw(sdf)
    print("sdf took %.4f seconds"%(time.time() - t))
    
    globals().update(locals())
    return sdf

def hello_sdf():
    res_power = 6
    width = 2**res_power

    fig = plt.gcf()
    for x in range(1):
        for y in range(1):
            t = time.time()
            with create_coordinate_image(x,y, res_power=res_power) as img:
                print("image took %.4f seconds"%(time.time() - t))
                with create_sdf(img) as sdf:
                    #plt.gcf().figimage(sdf, xo=width*x, yo=width*y)
                    plt.imshow(sdf)
                
                #plt.gcf().figimage(img, xo=width*x, yo=width*y)
    
    plt.show()

    
    

if __name__ == "__main__":
    hello_sdf()
