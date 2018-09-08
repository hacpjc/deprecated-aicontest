import sys, traceback, os, random, math
import json
import copy
    
import cv2, base64, numpy
from PIL  import Image
from io   import BytesIO
from PIL.ImageQt import rgb

def bt():
    try:   
        raise Exception("Manually raise an exception.")
    except Exception:
        traceback.print_stack(file=sys.stderr)
        sys.stderr.flush()
        
def msg(*argv):
    sys.stdout.write("".join(list(argv)) + "\n")
    sys.stdout.flush()

def errmsg(*argv):
    sys.stderr.write(" *** ERROR: ")
    sys.stderr.write("".join(list(argv)) + "\n")
    sys.stderr.flush()
    bt()
    
def vbsmsg(*argv):
    sys.stdout.write("...")
    sys.stdout.write("".join(list(argv)) + "\n")
    sys.stdout.flush()
    
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
    
    def open_path(self, path):
        if os.path.exists(path) == False:
            errmsg("Cannot find file " + path)
            return None
        
        numpy_ndarray = cv2.imread(path)
        
        return numpy_ndarray       
    
    def open_base64tojpg(self, base64img):
        """
        Input: Convert a base64 input into a opencv img object, e.g.
        
        Output: A list of RGB array: [255 255 255] [255 255 255] ...
        """
        jpg = base64.b64decode(base64img)
        nparray = numpy.asarray(Image.open(BytesIO(jpg)))
        
        return nparray
    
    def close(self, jpg):
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
    
    def set_pixel_rgb(self, img, x, y, rgb=(0, 0, 0)):
        r, g, b = rgb
        img[y][x] = [b, g, r]
    
    def get_pixel_rgb(self, img, x, y):
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
                r, g, b = self.get_pixel_rgb(img, x, y)
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
            
    def draw_line(self, img, st=(0, 0), ed=(320, 240), rgb=(255, 0, 0), thick=1):
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
            
        return cv2.line(img, st, ed, self.rgb2bgr(rgb), thick)
    
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
    
    def bgr2rgb(self, bgr):
        b, g, r = bgr
        return (r, g, b)
    
    def rgb2bgr(self, rgb):
        r, g, b = rgb
        return (b, g, r)
    
    def convert_bgr2rgb(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    def convert_rgb2bgr(self, img):
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def color_quantization(self, img_in):
        """
        OpenCV - Color quantization. Reduce noice, i.e. holes in img.
        """
        img = copy.deepcopy(img_in)
        
        Z = img.reshape((-1, 3))
        Z = numpy.float32(Z)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 8 
        ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        center = numpy.uint8(center)
        res = center[label.flatten()]
        res2 = res.reshape((img.shape))
        
        return res2
    
    def crosscut(self, img, ratio_from, ratio_to):
        """
        +---------------+
        |               |
        |               | - from
        |               |
        |               | - to
        |               |
        +---------------+
        """
        if ratio_to <= ratio_from:
            errmsg("Invalid crosscut range: " + format(ratio_from) + ", " + format(ratio_to))
        
        tgt_range = (ratio_from, ratio_to)
        tgt_slice = slice(*(int(x * img.shape[0]) for x in tgt_range))
        
        output = img[tgt_slice, :, :]
        
        return output
    
    def get_unique_colors(self, img):
        """
        Get all colors used in this img.
        """
        output = []
        
        width, height = self.get_resolution(img)
        
        for x in range(width):
            for y in range(height):
                pixel = self.get_pixel_rgb(img, x, y)
                if output.count(pixel) == 0:
                    output.append(pixel)
                    
        return output
    
    def flatten2rgb(self, img):
        width, height = self.get_resolution(img)
        for x in range(0, width):
            for y in range(0, height):
                r, g, b = self.get_pixel_rgb(img, x, y)
                if (r >= 200) and (g >= 200) and (b >= 200):
                    self.set_pixel_rgb(img, x, y, rgb=(255, 255, 255))
                elif (r < 50) and (g < 50) and (b < 50):
                    self.set_pixel_rgb(img, x, y, rgb=(0, 0, 0))
                elif (r >= 120) and (g < 150) and (b < 150):
                    self.set_pixel_rgb(img, x, y, rgb=(255, 0, 0))
                elif (r < 150) and (g >= 120) and (b < 150):
                    self.set_pixel_rgb(img, x, y, rgb=(0, 255, 0))
                elif (r < 150) and (g < 150) and (b >= 120):
                    self.set_pixel_rgb(img, x, y, rgb=(0, 0, 255))
                else:
                    self.set_pixel_rgb(img, x, y, rgb=(0, 0, 0))

        return img
    
    def reindeer(self, img, rgb=(0, 0, 0), prefer_left=True):
        """
        Contest specific calculation. Find the color blocks, calculate the angle.
        
        Use the angle to find-out how to get wheel angle.
        """
        width, height = self.get_resolution(img)
        
        if prefer_left == True:
            rgb_filter = []
            for y in range(height):
                row_data = {}
                row_data['st'] = 0
                row_data['ed'] = 0
     
                is_found = False           
                for x in range(width):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    if (r, g, b) == rgb:
                        if is_found == False:
                            is_found = True
                            row_data['st'] = x
                    elif is_found == True:
                        row_data['ed'] = x
                        break
                        
                rgb_filter.append(row_data)
        else:
            # Prefer right
            rgb_filter = []
            for y in range(height):
                row_data = {}
                row_data['st'] = 0
                row_data['ed'] = 0
     
                is_found = False           
                for x in range(width - 1, -1, -1):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    if (r, g, b) == rgb:
                        if is_found == False:
                            is_found = True
                            row_data['ed'] = x
                    elif is_found == True:
                        row_data['st'] = x
                        break
                        
                rgb_filter.append(row_data)
            
        sum = 0
        h = 1.0
        for y in range(height):
            row = rgb_filter[y]
            avg = (row['st'] + row['ed']) / 2
            sum += avg
            if avg > 0:
                print("avg: " + format(avg))
                h += 1.0
                
            if h >= 10:
                break
        
        real_avg = sum / h
        return real_avg
                
def unitest(path):
    hacjpg = Hacjpg()

    img = hacjpg.open_path(path)
    
    #
    # Input
    #
    hacjpg.show(img, waitkey=0)
    
    #
    # flatten
    #
    img = hacjpg.crosscut(img, 0.5, 1.0)
    hacjpg.show(img, waitkey=0)
    img = hacjpg.color_quantization(img)
    hacjpg.show(img, waitkey=0)
    img = hacjpg.flatten2rgb(img)
    hacjpg.show(img, waitkey=0)
    print (format(hacjpg.get_unique_colors(img)))
    
    hacjpg.reindeer(img, rgb=(0, 0, 255), prefer_left=True)
    
    hacjpg.close(img)
  
if __name__ == "__main__":
    path = ""
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        path = "log/111.jpg"
    
    unitest("log/222.jpg")
    
