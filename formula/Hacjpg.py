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
                        
        if len(map_y_uniq) == 0:
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
    
def test_distance():
    
    hacjpg = Hacjpg()
    
    st = (160, 54)
    ed = (0, 0)
    d = hacjpg.calc_distance(st, ed)
    print (d)
      
if __name__ == "__main__":
    
    for root, dirs, files in os.walk("./log"):
        path = root.split(os.sep)
        for file in files:
            print ("...path: ./log/" + file)
            unitest_reindeer3("./log/" + file)
    
