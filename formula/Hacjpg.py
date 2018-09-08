import sys, traceback, os, random, math
import json
    
import cv2, base64, numpy
from PIL  import Image
from io   import BytesIO

class Hacjpg():
    """
    Use this abstract jpg class to simplify image (jpeg) processing by using cv2 module.
    OpenCV tutorial: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html
    
    Depend: cv2, base64
    """
    """
            width (x)
          /       \
        +---------+
        |         | \
        |.        |  height (y)
        |         | /
        +---------+
        
        The dot in the pic is: width, height = (1, 2)
    """
    def __init__(self):
        pass
    
    def open_base64tojpg(self, base64img):
        """
        Input: Convert a base64 input into a opencv img object, e.g.
        
        Output: A list of RGB array: [255 255 255] [255 255 255] ...
        """
        jpg = base64.b64decode(base64img)
        nparray = numpy.asarray(Image.open(BytesIO(jpg)))
        
        return nparray
    
    def close(self, jpg):
        if jpg:
            del jpg
    
    def show(self, img, name = "image", scale = 1.0, waitkey = 1):
        """
        Display the img in a standalone window.
        """
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        
        cv2.waitKey(waitkey)
            
    def rgb2uint(self, tup):
        """
        Simplify rgb tuple into a unsigned number
        """
        r, g, b = tup
        return (r * 256 * 256) + (g * 256) + b
    
    def uint2rgb(self, uint):
        r, g, b = uint / (256 * 256), uint / (256), uint % 256
        return r, g, b
    
    def get_pixel(self, img, x, y):
        """
            width (x)
          /       \
        +---------+
        |         | \
        |.        |  height (y)
        |         | /
        +---------+
        """
        b, g, r = (img.item(y, x, 0), img.item(y, x, 1), img.item(y, x, 2))
        return r, g, b
        
    def print_geometry(self, img):
        """
        Print the pixel data of input img. Print a lot of xxx (trash?)...
        But, this function helps me to know how to read the pixel of img.
        """
        width, height = self.get_resolution(img)
        
        for x in range(0, width):
            for y in range(0, height):
                r, g, b = self.get_pixel(img, x, y)
                uint = self.rgb2uint((r, g, b))
                uint2hex = hex(uint)
                sys.stdout.write(str(uint2hex) + ",") 
            
            sys.stdout.write("\n")
            
    def _createdir(self, folder):
        if os.path.exists(folder) == False:
            os.mkdir(folder)
        
    def save2folder(self, folder, img, prefix = "img", suffix = ""):
        """
        Save input image into specified folder. Create the folder automatically.
        """
        from datetime import datetime
        filename = "%s-%s%s.jpg" % (prefix, datetime.now().strftime('%Y%m%d-%H%M%S-%f'), suffix)
        
        self._createdir(folder)
        res = cv2.imwrite(os.path.join(folder, filename), img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        if res == False:
            errmsg("Cannot write file " + os.path.join(folder, filename))
            
    def draw_line(self, img, st=(0, 0), ed=(320, 240), bgr=(0, 0, 255), thick=1):
        """
         width (x)
        /   \
        +----+
        |\   | \
        | \  |  height (y)
        |  \ | /
        +----+
        """
        width, height = self.get_resolution(img)
        
        x, y = st
        if x <= width and y <= height:
            pass
        else:
            errmsg("Invalid start point: " + str(x) + "," + str(y))
            
        x, y = ed
        if x <= width and y <= height:
            pass
        else:
            errmsg("Invalid end point: " + str(x) + "," + str(y))
            
        return cv2.line(img, st, ed, bgr, thick)
    
    def get_resolution(self, img):
        """
            width (x)
          /       \
        +---------+
        |         | \
        |         |  height (y)
        |         | /
        +---------+
        """

        # If image is grayscale, tuple returned contains only number of rows and columns.        
        height, width, channel = img.shape
        
        return width, height
    
    def bgr2rgb(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    def rgb2bgr(self, img):
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    