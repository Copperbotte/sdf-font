
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

    #"""
    # leave wand's api for performance
    t = time.time()
    sdf = np.array(img)
    print("img clone took %.4f seconds"%(time.time() - t))

    # simplify sdf to a single bit
    t = time.time()
    sdf = np.min(sdf, axis=2)
    sdf = sdf // 255
    sdf = sdf.astype(np.int8)
    print("sdf simplify took %.4f seconds"%(time.time() - t))

    # find boundary locations
    t = time.time()
    delta = np.zeros(sdf.shape, dtype=np.int8)

    #     vertical differences
    vdelta = np.abs(sdf[:-1, :] - sdf[1:, :])
    delta[:-1, :] += vdelta
    delta[1:, :] += vdelta

    #     horizontal differences
    hdelta = np.abs(sdf[:, :-1] - sdf[:, 1:])
    delta[:, :-1] += hdelta
    delta[:, 1:] += hdelta

    #     convert to binary
    delta = np.where(0 < delta, True, False)

    #     generate coordinates
    ind = np.indices(sdf.shape).T

    #     cull coordinates and sdf to find deltas
    c_ind = ind[delta]
    c_sdf = sdf[delta]

    #     sort sdf into font and background
    font_sites = c_ind[c_sdf == 0]
    back_sites = c_ind[c_sdf != 0]
    print("boundary search took %.4f seconds"%(time.time() - t))

    
    # Wouldn't a voronoi diagram work better for this?
    # find the closest boundary of opposite color for each point
    # for each boundary point, generate an sdf toward it
    t = time.time()
    sdf_bg = np.full(sdf.shape, img.width*img.width)
    for pt in font_sites:
        sdf_pt = ind - pt
        sdf_pt = np.sum(sdf_pt*sdf_pt, axis=2)
        sdf_bg = np.where(sdf_pt < sdf_bg, sdf_pt, sdf_bg)
    print("background sdf generation took %.4f seconds"%(time.time() - t))
    
    t = time.time()
    sdf_fo = np.full(sdf.shape, img.width*img.width)
    for pt in back_sites:
        sdf_pt = ind - pt
        sdf_pt = np.sum(sdf_pt*sdf_pt, axis=2)
        sdf_fo = np.where(sdf_pt < sdf_fo, sdf_pt, sdf_fo)
    print("font sdf generation took %.4f seconds"%(time.time() - t))

    # Replace sdf on sdf_bg with sdf_fo, if the point is on the font
    t = time.time()
    sdf_bg = np.where(sdf == 0, sdf_bg, sdf_fo)
    print("sdf merge took %.4f seconds"%(time.time() - t))

    # Convert from square distance to distance
    t = time.time()
    sdf_bg = np.sqrt(sdf_bg)

    # Re-scale, Clip, and Correct internal sign
    sdf_bg = sdf_bg / img.width
    sdf_bg = np.where(sdf_bg < 1, sdf_bg, 1)
    sdf_bg = np.where(sdf == 0, -sdf_bg, sdf_bg)

    # Lerp into int8
    sdf_bg = 255 * (sdf_bg/2.0 + 0.5)
    sdf = sdf_bg.astype(np.int8)
    #sdf = sdf + 10
    #sdf = sdf / 255 + 0.1
    print("conversion to sdf took %.4f seconds"%(time.time() - t))

    sdf = Image.from_array(sdf)
    globals().update(locals())
    return sdf

    return img
    
    #"""

    sdf = img.clone()
    
    t = time.time()
    # find a list of all the font and background points
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
    res_power = 9
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
