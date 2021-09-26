
# https://stackoverflow.com/questions/5414639/python-imaging-library-text-rendering

import matplotlib.pyplot as plt
from wand.color import Color
from wand.image import Image
from wand.drawing import Drawing
from wand.compat import nested

def hello_wand():
    with Drawing() as draw:
        with Image(width=750, height=100, background=Color("lightblue")) as img:
            # Properties are set within draw, like the ones below
            
            draw.font_family = 'consolas'
            #draw.font_size = 40.0
            draw.font_size = 50
            draw.text_antialias = False
            
            # https://docs.wand-py.org/en/0.6.7/wand/drawing.html#wand.drawing.TEXT_ALIGN_TYPES
            # Text align types are:
            # ['undefined', 'left', 'center', 'right']
            draw.text_alignment = 'left'
            
            draw.push()
            draw.fill_color = Color('darkred')

            # https://docs.wand-py.org/en/0.6.7/wand/drawing.html#wand.drawing.Drawing.text
            # Text has three parameters: x, y, and body.
            # Body is the actual text, as a string.
            # X and Y are the coordinates of the text.
            # Coordinates are measured from the upper left corner of the image,
            #     to the lower left corner of the text.
            # Left handed coords aaaaaaaargh whyyyyyyyyyyyyyyyy

            text = 'Hello, wand!\nA0 B0 A1 B1 C4 D8'
            est_num_lines = text.count('\n') + 1
            draw.text(50, int(img.height - draw.font_size*(est_num_lines - 1)),
                      text)
            draw.pop()
            draw(img)
            
            plt.gcf().figimage(img)
            plt.show()

if __name__ == "__main__":
    hello_wand()
