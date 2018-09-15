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
    
    def check_path(self, path):
        if os.path.exists(path) == False:
            return False
        
        return True
    
    def open_path(self, path):
        if self.check_path(path) == False:
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
    
    def open_base64(self, base64str):
        jpg = base64.b64decode(base64str)
        
        nparray = numpy.asarray(Image.open(BytesIO(jpg)))
        return nparray
    
    def close(self, jpg):
        del jpg
        
    def overwrite(self, img, path):
        """
        Write an image to the path
        """
        return cv2.imwrite(path, img)
    
    def show(self, img, name="image", waitkey=1):
        """
        Display the img in a standalone window.
        """
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        
        cv2.waitKey(waitkey)
        
    def show_nowait(self, img, name="image"):
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        
    def close_window(self, name="image"):
        cv2.destroyWindow(name)
        
    def close_window_all(self):
        cv2.destroyAllWindows()
            
    def encode2base64_by_path(self, path):
        with open(path, "rb") as image_file:
            str = base64.b64encode(image_file.read())
            return str
    
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
    
    def draw_text(self, img, ascii, pos, rgb=(0, 0, 0)):
        font = cv2.FONT_HERSHEY_PLAIN
        cv2.putText(img, ascii, pos, font, 1, rgb);
        
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
    
    def calc_column_pixel_num_by_rgb(self, img, x, rgb):
        """
        +---------------+
        |       r       |
        |       r       |
        |       b       |
        |       g       |
        +---------------+
        
        Calculate the number of a specific color.
        
        Output:
        number of r = 2
        """
        
        width, height = self.get_resolution(img)
        
        if x >= width or x < 0:
            errmsg("Invalid input argument x: ", format(x))
            
        num = 0
        for y in range(height):
            this_rgb = self.get_pixel_rgb(img, x, y)
            
            if this_rgb == rgb:
                num += 1
               
        return num 
        
    def cut(self, img, ratio_from, ratio_to):
        """
         from    to
           |     |
        +---------------+
        |               |
        |               |
        +---------------+
        """ 
        
        if ratio_to <= ratio_from:
            errmsg("Invalid cut range: " + format(ratio_from) + ", " + format(ratio_to))
            
        tgt_range = (ratio_from, ratio_to)
        tgt_slice = slice(*(int(x * img.shape[1]) for x in tgt_range))
        
        output = img[:, tgt_slice, :]
        return output
    
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
    
    def flatten2rgb_white(self, img):
        #
        # TODO: FIXME
        # 
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
    
    def flatten2rgb(self, img):
        r, g, b = cv2.split(img)
        r_filter = (r == numpy.maximum(numpy.maximum(r, g), b)) & (r >= 120) & (g < 150) & (b < 150)
        g_filter = (g == numpy.maximum(numpy.maximum(r, g), b)) & (g >= 120) & (r < 150) & (b < 150)
        b_filter = (b == numpy.maximum(numpy.maximum(r, g), b)) & (b >= 120) & (r < 150) & (g < 150)
        y_filter = ((r >= 128) & (g >= 128) & (b < 100))

        r[y_filter], g[y_filter] = 255, 255
        b[numpy.invert(y_filter)] = 0

        b[b_filter], b[numpy.invert(b_filter)] = 255, 0
        r[r_filter], r[numpy.invert(r_filter)] = 255, 0
        g[g_filter], g[numpy.invert(g_filter)] = 255, 0

        flattened = cv2.merge((r, g, b))
        return flattened
#         width, height = self.get_resolution(img)
#         for x in range(0, width):
#             for y in range(0, height):
#                 r, g, b = self.get_pixel_rgb(img, x, y)
#                 if (r >= 200) and (g >= 200) and (b >= 200):
#                     self.set_pixel_rgb(img, x, y, rgb=(255, 255, 255))
#                 elif (r < 50) and (g < 50) and (b < 50):
#                     self.set_pixel_rgb(img, x, y, rgb=(0, 0, 0))
#                 elif (r >= 120) and (g < 150) and (b < 150):
#                     self.set_pixel_rgb(img, x, y, rgb=(255, 0, 0))
#                 elif (r < 150) and (g >= 120) and (b < 150):
#                     print ("green=", format((r,g,b)))
#                     self.set_pixel_rgb(img, x, y, rgb=(0, 255, 0))
#                 elif (r < 150) and (g < 150) and (b >= 120):
#                     self.set_pixel_rgb(img, x, y, rgb=(0, 0, 255))
#                 else:
#                     self.set_pixel_rgb(img, x, y, rgb=(0, 0, 0))
# 
#         return img
    
    def calc_distance(self, st, ed):
        """
        Calculate the distance between two points
        """
        if st == None or ed == None:
            errmsg("Invalid input argument")
        
        st_x, st_y = st
        ed_x, ed_y = ed
        
        x_diff = abs(st_x - ed_x)
        y_diff = abs(st_y - ed_y)
        
        distance = round(math.sqrt((x_diff * x_diff) + (y_diff * y_diff)), 4)
        
        return distance
    
    def calc_slope(self, st, ed):
        """
        Caclulcate the slope of two points.
        
        (0,0)
        v-----------------
        |
        |           o ed
        |         /
        |       /
        |_____x______
             st
             
        Plz note that 0,0 is at left + top -- for a img.
        """
        x_st, y_st = st
        x_ed, y_ed = ed
        
        x_diff = x_ed - x_st
        y_diff = y_ed - y_st
        
        if y_diff == 0:
            return 0
        else:        
            return x_diff / float(y_diff)
        
    def calc_angle(self, st, ed):
        """
        Caclulcate the angle of two points.
        
        (0,0)
        v-----------------
        |
        |           o ed
        |         /
        |       /
        |_____x______
             st
             
        Plz note that 0,0 is at left + top -- for a img.
        """
        x_st, y_st = st
        x_ed, y_ed = ed
        
        x_diff = x_ed - x_st
        y_diff = y_ed - y_st
        
        angle = numpy.rad2deg(numpy.arctan2(y_diff, x_diff))
        
        return angle

    def reindeer3(self, img, rgb=(0, 0, 0), prefer_left=True):
        """
        Contest specific calculation. Find the color blocks, calculate the angle.
        
                        Find the line in the middle of a road
                       V
        +++++++++++++++++++++++++++
        +    .        /           .
        +  .         /          .
        + .         /         .
        +          /       .
        +         /      .
        +       /      .
        ++++++++++++++++++++++++ 
        
        Then, I can use the angle to find-out how to get wheel angle.
        
        x = [8450.0, 8061.0, 7524.0, 7180.0, 8247.0, 8929.0, 8896.0, 9736.0, 9658.0, 9592.0]
        y = range(len(x))
        best_fit_line = np.poly1d(np.polyfit(y, x, 1))(y)
        """
        width, height = self.get_resolution(img)
    
        point_cnt = 0
        map_y = []
        map_y_uniq = []
        map_x = []
        for y in range(height):
            is_found = False
            
            if prefer_left == True:
                """
                Prefer the color block at left-side
                """
                for x in range(width):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    
                    if (r, g, b) == rgb:
                        point_cnt += 1
                        map_y.append(y)
                        map_x.append(x)
                        
                        if is_found == False:
                            is_found = True
                            map_y_uniq.append(y)
                    elif is_found == True:
                        break
            else:
                """
                Prefer the color block at right-side
                """
                for x in range(width - 1, -1, -1):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    
                    if (r, g, b) == rgb:
                        point_cnt += 1
                        map_y.append(y)
                        map_x.append(x)
                        
                        if is_found == False:
                            is_found = True
                            map_y_uniq.append(y)
                    elif is_found == True:
                        break
                        
        if len(map_y_uniq) < 2:
            return None, None, None
                
        fit_x = numpy.poly1d(numpy.polyfit(map_y, map_x, 1))(map_y_uniq)
        fit_x = [int(x) for x in fit_x]
        
        for idx in range(len(map_y_uniq)):
            #
            # Fix x value if it's out of bound.
            #
            if fit_x[idx] >= width:
                fit_x[idx] = width - 1
                
            if fit_x[idx] < 0:
                fit_x[idx] = 0
                
            y, x = map_y_uniq[idx], fit_x[idx]
            self.set_pixel_rgb(img, x, y, rgb=(255, 255, 255))
            
        central_point_y = int((map_y_uniq[0] + map_y_uniq[-1]) / 2.0)
        central_point_x = int((fit_x[0] + fit_x[-1]) / 2.0)
        
        cv2.circle(img, (central_point_x, central_point_y), 3, (255, 255, 255))
        
        self.draw_line(img, (width / 2, height), (width / 2, 0), (255, 255, 255), 1)
        
        angle = numpy.rad2deg(numpy.arctan2((map_y_uniq[-1] - map_y_uniq[0]), fit_x[-1] - fit_x[0]))
        
        #
        # area percentage
        #
        area_percent = int(round(point_cnt / float(width * height), 4) * 100)
        return (central_point_x, central_point_y), angle, area_percent
    
    def reindeer2(self, img, rgb=(0, 0, 0), prefer_left=True):
        """
        Contest specific calculation. Find the color blocks, calculate the angle.
        
                        Find the line in the middle of a road
                       V
        +++++++++++++++++++++++++++
        +    .        /           .
        +  .         /          .
        + .         /         .
        +          /       .
        +         /      .
        +       /      .
        ++++++++++++++++++++++++ 
        
        Then, I can use the angle to find-out how to get wheel angle.
        
        x = [8450.0, 8061.0, 7524.0, 7180.0, 8247.0, 8929.0, 8896.0, 9736.0, 9658.0, 9592.0]
        y = range(len(x))
        best_fit_line = np.poly1d(np.polyfit(y, x, 1))(y)
        """
        width, height = self.get_resolution(img)
    
        map_y = []
        map_y_uniq = []
        map_x = []
        for y in range(height):
            is_found = False
            
            if prefer_left == True:
                """
                Prefer the color block at left-side
                """
                for x in range(width):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    
                    if (r, g, b) == rgb:
                        map_y.append(y)
                        map_x.append(x)
                        
                        if is_found == False:
                            is_found = True
                            map_y_uniq.append(y)
                    elif is_found == True:
                        break
            else:
                """
                Prefer the color block at right-side
                """
                for x in range(width - 1, -1, -1):
                    r, g, b = self.get_pixel_rgb(img, x, y)
                    
                    if (r, g, b) == rgb:
                        map_y.append(y)
                        map_x.append(x)
                        
                        if is_found == False:
                            is_found = True
                            map_y_uniq.append(y)
                    elif is_found == True:
                        break
                        
        if len(map_y_uniq) == 0:
            return None, None, None, None
                
        fit_x = numpy.poly1d(numpy.polyfit(map_y, map_x, 1))(map_y_uniq)
        fit_x = [int(x) for x in fit_x]
        
        for idx in range(len(map_y_uniq)):
            #
            # Fix x value if it's out of bound.
            #
            if fit_x[idx] >= width:
                fit_x[idx] = width - 1
                
            if fit_x[idx] < 0:
                fit_x[idx] = 0
                
            y, x = map_y_uniq[idx], fit_x[idx]
            self.set_pixel_rgb(img, x, y, rgb=(255, 255, 255))
            
        central_point_y = int((map_y_uniq[0] + map_y_uniq[-1]) / 2.0)
        central_point_x = int((fit_x[0] + fit_x[-1]) / 2.0)
        
        cv2.circle(img, (central_point_x, central_point_y), 3, (255, 255, 255))
        
        self.draw_line(img, (width / 2, height), (width / 2, 0), (255, 255, 255), 1)
        
        angle = numpy.rad2deg(numpy.arctan2((map_y_uniq[-1] - map_y_uniq[0]), fit_x[-1] - fit_x[0]))
        
        return map_y_uniq, fit_x, (central_point_x, central_point_y), angle
        
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
                
                if is_found == True and row_data['ed'] == 0:
                    # The end point is the right edge of picture
                    row_data['ed'] = width
                        
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
                
                if row_data['st'] == 0 and is_found == True:
                    # The start point is the left edge of pic
                    row_data['st'] = 0
                        
                rgb_filter.append(row_data)
            
        sum = 0
        cnt = 0.0
        pdiff_sum = 0
        pdiff_cnt = 0.0
        pavg = 0
        output_pos_sum = (0, 0)
        for y in range(height):
            row = rgb_filter[y]
            
            thisavg = (row['st'] + row['ed']) / 2
            if thisavg == 0:
                continue
            
#             if (prefer_left == True and row['st'] > 0) or (prefer_left == False and row['ed'] != width):
            if 0 == 0:
                print ("efficient thisavg: " + format(thisavg), format(row['st']), format(row['ed']))
                self.set_pixel_rgb(img, thisavg, y, rgb=(0, 255, 0))
                sum += thisavg
                cnt += 1.0
                
                sum_x, sum_y = output_pos_sum
                sum_x += thisavg
                sum_y += y
                output_pos_sum = (sum_x, sum_y)
                
                if pavg == 0:
                    pavg = thisavg
                else:
                    pdiff_sum += thisavg - pavg
                    pdiff_cnt += 1.0
            else:
                print("ignore: ", format(row['st']), format(row['ed']))

        if pdiff_cnt > 0:
            pdiff_avg = pdiff_sum / pdiff_cnt
            
            avg_x, avg_y = output_pos_sum
            output_pos_avg = (avg_x / cnt, avg_y / cnt)
        else:
            pdiff_avg = 0
            output_pos_avg = (0, 0)
            print ("pdiff avg: n/a")

        """
        pdiff < 0, the road looks like:
            ////
           ////
          ////
          
        pdiff > 0, the road looks like:
         \\\\
          \\\\
           \\\\
           
        And use pos avg to identify the position of the road
        """
        return pdiff_avg, output_pos_avg
    
    def resize(self, img, width, height):
        resized_img = cv2.resize(img, (width, height))
        return resized_img
    
    def _calc_row_pixel_in_color(self, img, rgb, width, y):
        cnt = 0
        for x in range(width):
            this_rgb = self.get_pixel_rgb(img, x, y)
            if this_rgb != rgb:
                cnt += 1
                
        return cnt
    
    def _calc_column_pixel_in_color(self, img, rgb, height, x):
        cnt = 0
        for y in range(height):
            this_rgb = self.get_pixel_rgb(img, x, y)
            if this_rgb != rgb:
                cnt += 1
                
        return cnt
    
    def remove_surronding_color(self, img, rgb=(255, 0, 0)):
        #        
        # Top
        #
        width, height = self.get_resolution(img)
        
        remove_cnt = 0
        for y in range(height):
            rgb_cnt = self._calc_row_pixel_in_color(img, rgb, width, y)
                    
            if rgb_cnt == width:
                remove_cnt += 1
            else:
                break
        
        if remove_cnt > 0:
            img = img[remove_cnt:height, :]
        
        #
        # bottom
        #
        width, height = self.get_resolution(img)
        
        remove_cnt = 0
        for y in range(height - 1, 0, -1):
            rgb_cnt = self._calc_row_pixel_in_color(img, rgb, width, y)
            
            if rgb_cnt == width:
                remove_cnt += 1
            else:
                break
        
        if remove_cnt > 0:
            new_height = height - remove_cnt
            img = img[0:new_height, :]
        
        #
        # left
        #
        width, height = self.get_resolution(img)
        
        remove_cnt = 0
        for x in range(width):
            rgb_cnt = self._calc_column_pixel_in_color(img, rgb, height, x)
            
            if rgb_cnt == height:
                remove_cnt += 1
            else:
                break
        
        if remove_cnt > 0:
            img = img[:, remove_cnt:width]
        
        #
        # right
        #
        width, height = self.get_resolution(img)
        
        remove_cnt = 0
        for x in range(width - 1, 0, -1):
            rgb_cnt = self._calc_column_pixel_in_color(img, rgb, height, x)
            
            if rgb_cnt == height:
                remove_cnt += 1
            else:
                break
        
        if remove_cnt > 0:
            new_width = width - remove_cnt
            img = img[:, 0:new_width]
        
        return img
        
def unitest_reindeer3(path):
    hacjpg = Hacjpg()
    
    print("")

    img = hacjpg.open_path(path)
    
    #
    # Input
    #
    hacjpg.show(img, waitkey=0)
    
    #
    # flatten
    #
    img = hacjpg.crosscut(img, 0.55, 1.0)
    reso_x, reso_y = hacjpg.get_resolution(img)

#     img = hacjpg.color_quantization(img)
    img = hacjpg.flatten2rgb(img)
    print ("color map: ", format(hacjpg.get_unique_colors(img)), "resolution: ", reso_x, reso_y)
    
    v = hacjpg.reindeer3(img, rgb=(0, 0, 255), prefer_left=True)
    print("reindeer2 result: ", v)
    
    cpoint, angle, ap = v
    if cpoint != None:
        (cx, cy) = cpoint
        #
        # These are the major features to define a urgent turn...
        #
        print("angle: ", angle)
        print("cpoint angle: ", hacjpg.calc_angle((reso_x / 2, reso_y), (cx, cy)) + 90)
        print("distance: ", hacjpg.calc_distance((reso_x / 2, reso_y), (cx, cy)))
        print("area percentage: ", ap)

    hacjpg.show(img, waitkey=0)
    ###
    
    hacjpg.close(img)
    
class HacTrafficSignDetection(Hacjpg):
    def __init__(self, scale=(50, 25)):
        self.hacjpg = Hacjpg()
        
        self.spec = {}
        self.spec['scale'] = scale
        self.spec['rgb'] = (255, 0, 0) # Traffic sign is in red.
        
        # A traffic sign should at least > this size
        self.spec['detect_width_min'] = 30
        self.spec['detect_height_min'] = 10
        self.spec['error_tolerance'] = 2 # pixel

        self.db = []
        
    def _debug_bitmap_nparray(self, bitmap):
        
        height, width = bitmap.shape
        
        for y in range(height):
            for x in range(width):
                if bitmap[y][x] == 1:
                    sys.stdout.write("O")
                else:
                    sys.stdout.write(".")
            sys.stdout.write("\n")
        
    def _compile_traffic_sign(self, img):
        """
        Compile traffic sign features into a signature.
        """
        width, height = self.spec['scale']
        
        """
        Compile a left turn sign into a true/false table like:
        
        ...O...........
        ..OOOOOOOOOOOOO
        OOOOOOOOOOOOOOO
        .OOOOOOOOOOOOOO
        ..O............     
        
        Convert this table into a numpy array so that I can do logical and.
        """
        this_bitmap = numpy.zeros([height, width], dtype=numpy.int8)
        
        for y in range(height):
            for x in range(width):
                r, g, b = self.hacjpg.get_pixel_rgb(img, x, y)
                if (r, g, b) == self.spec['rgb']:
                    this_bitmap[y][x] = 1
                else:
                    this_bitmap[y][x] = 0
        
        return this_bitmap
    
    def img2traffic_sign(self, img):
        img = self.hacjpg.flatten2rgb(img)
        self.hacjpg.remove_surronding_color(img, rgb=(255, 0, 0))
        
        width, height = self.spec['scale']
        resized_img = self.hacjpg.resize(img, width, height)
        flat_img = self.hacjpg.flatten2rgb(resized_img)
        
        return flat_img
    
    def add_traffic_sign_by_base64(self, base64data, name=None):
        img = self.hacjpg.open_base64(base64data)
        img = self.hacjpg.convert_bgr2rgb(img)
        
#         self.hacjpg.show(img, name="test", waitkey=0)

        traffic_sign_img = self.img2traffic_sign(img)
        
        traffic_sign = {'img': traffic_sign_img, 'path': '.na', 'name': name}
        traffic_sign['bitmap'] = self._compile_traffic_sign(traffic_sign['img'])
        
        #
        # Save traffic sign data
        #
        self.db.append(traffic_sign)
        
    def add_traffic_sign_by_path(self, path, name=None):
        """
        Add a traffic sign pattern
        """
        print(self.hacjpg.encode2base64_by_path(path))
        
        #
        # Read file
        #
        if self.check_path(path) == False:
            return False
        
        img = self.hacjpg.open_path(path)
        
        if name == None:
            name = path
            
        flat_img = self.img2traffic_sign(img)
        
        traffic_sign = {'img': flat_img, 'path': path, 'name': name}
        traffic_sign['bitmap'] = self._compile_traffic_sign(traffic_sign['img'])
        
        #
        # Save traffic sign data
        #
        self.db.append(traffic_sign)
        
        return True
        
    def walk_traffic_sign(self, func):
        """
        Visit every traffic sign and execute input func
        """
        for s in self.db:
            func(s)
            
    def detect_object(self, img):
        """
        Find an object in img
        """
        pass
    
    def logical_diff(self, a, b):
        height, width = a.shape
        if b.shape != a.shape:
            errmsg("Invalid input data" + format(a.shape) + format(b.shape))
        
        diff = (a - b)
        
        cnt = 0
        for y in range(height):
            for x in range(width):
                if diff[y][x] != 0:
                    cnt += 1
        
        return cnt
    
    def mean_square_error(self, a, b):
        """
        Calculate mean square error of two img.
        NOTE: Assume the input img are in the same dimension.
        
                               1
        mean square error = _______ * (SUM(I(i, j) - K(i, j)] ^ 2) 
                             m * n 
        """
        
        height, width = a.shape
        if b.shape != a.shape:
            errmsg("Invalid input data" + format(a.shape) + format(b.shape))
        
        sum_part = numpy.sum((a - b) ** 2)
        mse = sum_part / float(width * height)
        
        return mse
    
    def fetch_square(self, img, pos_x, pos_y, width, height):
        """
        Try to match a square-like block at target position. 
        At least 2x2. 1x1 = dot, right?
        
            /-------+
           /|       |
          / | square|
         /  |       |
        /   |_______|
        """
        
        #
        # Find the max possible width
        #
        max_x_expect = width
        for x in range(pos_x, width):
            rgb = self.get_pixel_rgb(img, x, pos_y)
            
            if rgb != (255, 255, 255):
                pass
            else:
                forgive_mode = False
                if pos_y < height - self.spec['error_tolerance']:
                    for yy in range(pos_y + 1, pos_y + self.spec['error_tolerance']):
                        yyrgb = self.get_pixel_rgb(img, x, yy)
                        if yyrgb != (255, 255, 255):
                            forgive_mode = True
                            break
                
                if forgive_mode == True:
                    continue
                else:
                    max_x_expect = x
                    break
        
        #
        # Find the max possible square
        #
        max_x = max_x_expect
        max_y = pos_y
        need_stop = False
        for y in range(pos_y + 1, height):
            pixel_cnt = 1
            for x in range(pos_x + 1, max_x):
                rgb = self.get_pixel_rgb(img, x, y)
                
                if rgb != (255, 255, 255):
                    pixel_cnt += 1
                else:
                    #
                    # Forgive non-smooth edge
                    #
                    forgive_mode = False
                    if y < height - self.spec['error_tolerance']:
                        for yy in range(y + 1, y + self.spec['error_tolerance']):
                             
                            yyrgb = self.get_pixel_rgb(img, x, yy)
                            if yyrgb != (255, 255, 255):
                                forgive_mode = True
                                break
                             
                    if forgive_mode == False:
                        break
                    else:
                        pixel_cnt += 1

                                 
            if pixel_cnt < ((max_x_expect - pos_x) * 0.9):
                max_y = y
                need_stop = True
                break
            elif pixel_cnt < (max_x - pos_x):
                max_x = pos_x + pixel_cnt
        
            if need_stop == True:
                max_y = y
                break
                
        output_width = (max_x - pos_x)
        output_height = (max_y - pos_y)
        
        if output_width < 2 or output_height < 2:
            return None
        else:
            return (max_x, max_y)                
    
    def filter_out_square(self, img, pos_x, pos_y, width, height):
        for y in range(pos_y, pos_y + height):
            for x in range(pos_x, pos_x + width):
                self.hacjpg.set_pixel_rgb(img, x, y, rgb=(255, 255, 255))
           
        return img         
    
    def walk_object(self, img, func):
        """
        Walk the img, find object and execute func
        """
        output = []
        
        width, height = self.hacjpg.get_resolution(img)
        
        for y in range(height - self.spec['detect_height_min']):
            for x in range(width):
                rgb = self.get_pixel_rgb(img, x, y)
                # Handle with non-white pixel
                if rgb != (255, 255, 255):
                    square = self.fetch_square(img, x, y, width, height)
                    if square == None:
                        continue
                    elif (square[0] - x) < self.spec['detect_width_min'] or (square[1] - y) < self.spec['detect_height_min']:
                        continue
                    
                    object = img[y:square[1], x:square[0], :]
                    new_output = func(object)
                    if new_output != None:
                        output.append(new_output)
#                     img = self.filter_out_square(img, x, y, square[0] - x, square[1] - y)
                    
                    return output
                    
        return output

    def _detect_traffic_sign(self, subimg):
        """
        Try to find the traffic sign at input img...really.
        """
#         self.hacjpg.show(subimg, name="sign", waitkey=0)
        #
        # Preprocessing - Remove surronding black
        #
        subimg = self.hacjpg.remove_surronding_color(subimg, rgb=(255, 0, 0))
        
        height, width = self.get_resolution(subimg)
        if height == 0 or width == 0:
            return None

        subimg = self.resize(subimg, self.spec['scale'][0], self.spec['scale'][1])
        
        subimg_bitmap = self._compile_traffic_sign(subimg)
        
        output = None
        select_mse = None
        select_diff = None
        for ts in self.db:
            mse = self.mean_square_error(subimg_bitmap, ts['bitmap'])
            diff = self.logical_diff(subimg_bitmap, ts['bitmap'])
            
            if mse >= 0.36 or diff > 350:
                # Filter-out not so good match
                continue 
            
            if output == None:
                output = {'name': ts['name'], 'mse': mse, 'diff': diff}
                select_mse = mse
                select_diff = diff
            elif diff < select_diff and mse < select_mse:
                output = {'name': ts['name'], 'mse': mse, 'diff': diff}
                select_mse = mse
                select_diff = diff
        
        return output
                
    def detect_traffic_sign(self, img):
        """
        Try to find the traffic sign at input img.
        
        Output: A list of matched traffic sign data.
        """
#         import time
        
#         st = time.time()
        #
        # Input pre-processing
        #
        img_crosscut = self.hacjpg.crosscut(img, 0, 0.35)
        img_cut = self.hacjpg.cut(img_crosscut, 0.3, 0.7)
        img_flatten = self.hacjpg.flatten2rgb_white(img_cut)
#         mid = time.time()
        #
        # Try to find traffic sign object and execute func
        #
        output = self.walk_object(img_flatten, self._detect_traffic_sign)
        
#         ed = time.time()
        
#         print(ed - st, mid - st)
        
        return output
    
    def detect_traffic_sign_by_path(self, path):
        if self.hacjpg.check_path(path) == False:
            print(" *** ERROR: Cannot open file: ", path)
            return []
        
        img = self.hacjpg.open_path(path)
        
        return self.detect_traffic_sign(img)
    
if __name__ == "__main__":
    
    htsd = HacTrafficSignDetection((50, 25))
    
    for root, dirs, files in os.walk("./traffic-sign-input"):
        path = root.split(os.sep)
        for file in files:
            print ("...path: " + file)
            htsd.add_traffic_sign_by_path("./traffic-sign-input/" + file, name=None)

    def show_traffic_sign(ts):
        hacjpg = Hacjpg()
        hacjpg.show(ts['img'], "traffic-sign", waitkey=0)
    
#     htsd.walk_traffic_sign(show_traffic_sign)
    
    res = htsd.detect_traffic_sign_by_path("./log/" + "img-20180912-223137-664000.jpg")
    print (res)
    for root, dirs, files in os.walk("./log"):
        path = root.split(os.sep)
        for file in files:
            print ("...path: " + file)
            res = htsd.detect_traffic_sign_by_path("./log/" + file)
            print(res)
        
    