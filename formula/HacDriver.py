import sys, traceback, os, random, math, json, copy

from Hacjpg import Hacjpg

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

class HacDriver(Hacjpg):
    """
    This is the main class to drive the car. See try2drive method.
    """
    
    def __init__(self, is_debug=False):
        self.hacjpg = Hacjpg()
        
        #
        # Car configurations
        #
        self.spec = {
            # Throttle -1.0 ~ 1.0
            'tho_max': 0.5,
            'tho_min': 0.0,
            'brk_max': 0.6,
            'brk_min': 0.0,
            # Steering angle -45 ~ 45
            'sta_max': 40,
            'sta_min': -40,
            # history
            'history_max': 4,
            # speed error tolerance
            'speed_error_tolerance': 0.001,
            'speed_max': 0.8,
            'speed_min': 0.25,
            'speed_uturn': 0.3,
            'speed_turn': 0.35,
            'speed_update_unit': 0.015,
            'speed_back_limit': -1.0,
            }
        msg("Car spec: " + format(self.spec))
        
        #
        # Save dashboard history
        # 
        self.history = []
        
        #
        # Dynamic data
        #
        self.dyn = {
            # reindeer result
            'reindeer_cpoint': None,
            'reindeer_map_x': None,
            'reindeer_map_y': None,
            'reindeer_angle': None,
            'reindeer_cpoint_angel': None,
            'reindeer_img': None,
            # If I have choice, take right-hand road?
            'road_prefer_left': True,
            'road_prefer_rgb': (0, 0, 255),
            # Expected speed
            'speed': 0.1,
            'speed_inc_cnt': 0,
            'uturn': False,
            'uturn_auto_drive': 0,
            }
        
    def history_create_data(self, dashboard):
        """
        Allocate a new history data by current dashboard
        """
        data = {}
        
        data['sta'] = float(dashboard['steering_angle'])
        data['tho'] = float(dashboard['throttle'])
        data['brk'] = float(dashboard['brakes'])
        
        data['time'] = float(dashboard['time'])
        data['speed'] = float(dashboard['speed'])
        
        return data
        
    def history_update(self, dashboard):
        """
        history = [ new, older, ..., very old ]
        """
        nd = self.history_create_data(dashboard)
        
        history = self.history
        if len(history) < self.spec['history_max']:
            history.insert(0, nd)
        else:
            history.pop()
            history.insert(0, nd)
            
    def history_get(self, idx=0):
        history_max = len(self.history)
        
        if idx >= history_max:
            return None
        else:
            return self.history[idx]
    
    def history_get_sta_avg(self):
        """
        Get average of history sta
        """
        cnt = 0
        sum = 0
        for h in self.history:
            sum = h['sta']
            cnt += 1
            
        return sum / float(cnt)            

    def set_speed(self, speed):
        vbsmsg("Set speed: " + str(speed))
        self.dyn['speed'] = speed
        
        self.dyn['speed_inc_cnt'] = 0
    
    def set_speed_if_negative(self, speed):
        if speed < 0:
            errmsg("Invalid speed" + str(speed))
        
        if self.dyn['speed'] < 0:
            self.dyn['speed'] = speed
            
        self.dyn['speed_inc_cnt'] = 0
            
    def set_speed_if_postive(self, speed):
        if speed > 0:
            errmsg("Invalid speed" + str(speed))
            
        if self.dyn['speed'] > 0:
            self.dyn['speed'] = speed
            
        self.dyn['speed_inc_cnt'] = 0
        
    def update_speed_abs(self, increase=True):
        """
        THO + ABS (Anti-lock Braking System)
        """
        if increase == True:
            if self.dyn['speed_inc_cnt'] >= 4 or self.dyn['speed'] <= 0.4:
                self.dyn['speed_inc_cnt'] = 0
                speed = self.spec['speed_update_unit']
            else:
                speed = (self.spec['speed_update_unit'] / 2.0)
                
            return self.update_speed(speed)
        else:
            """
            Decrease speed but no slower than...
            """
            speed = (self.spec['speed_update_unit'] * 8.0) * (-1)
            return self.update_speed(speed)
            
    def update_speed(self, speed):
        if speed > 0:
            """
            Increase speed by input amount
            """
            self.dyn['speed'] += speed     
            self.dyn['speed_inc_cnt'] += 1
            
            if self.dyn['speed'] >= self.spec['speed_max']:
                self.dyn['speed'] = self.spec['speed_max']
                
            vbsmsg("speed+: " + str(self.dyn['speed']))
        else:
            """
            Decrease speed but no slower than...
            """
            self.dyn['speed_inc_cnt'] = 0
            
            if (self.dyn['speed'] - abs(speed)) < self.spec['speed_min']:
                return False
            
            self.dyn['speed'] -= abs(speed) 
            
            vbsmsg("speed-: " + str(self.dyn['speed']))
            
        self.dyn['speed'] = round(self.dyn['speed'], 4)
        return True
    
    def calibrate_sta(self, sta):
        """
        Make sure sta is in range. Return a reasonable value.
        """
        if sta < 0:
            if sta < self.spec['sta_min']:
                return self.spec['sta_min']
            else:
                return sta
        elif sta > 0:
            if sta > self.spec['sta_max']:
                return self.spec['sta_max']
            else:
                return sta
        
        return 0
    
    def calibrate_sta_sqrt(self, sta):
        """
        Use sqrt to calibrate sta
        """
        output = 0.0
        
        if sta > 0:
            if sta <= 1:
                output = sta / 4.0
            else:
                output = math.sqrt(sta)
        elif sta < 0:
            if sta >= (-1):
                output = sta / 4.0
            else:
                output = math.sqrt(abs(sta)) * (-1)
        
        return round(output, 4)
        
    def confirm_uturn(self):
        """
        Detect there's a uturn by camera history
        """
        ri_img = self.dyn['reindeer_img']
        ri_img_width, ri_img_height = self.hacjpg.get_resolution(ri_img)
        
        ri_cpoint_angle = self.dyn['reindeer_cpoint_angle']
        
        rgb = self.dyn['road_prefer_rgb']
        num_left = self.calc_column_pixel_num_by_rgb(ri_img, 0, rgb)
        num_right = self.calc_column_pixel_num_by_rgb(ri_img, (ri_img_height - 1), rgb)
        
        if abs(ri_cpoint_angle) > 30:
            if ri_cpoint_angle > 0:
                """
                Detect right-side uturn.
                """
                if num_right >= (ri_img_height * 0.8) and num_left < (ri_img_height * 0.2):
                    return True
                
            elif ri_cpoint_angle < 0:
                """
                Detect left-side uturn.
                """
                if num_left >= (ri_img_height * 0.8) and num_right < (ri_img_height * 0.2):
                    return True
            else:
                pass
        
        return False

    def get_sta_param(self):
        """
        Use cpoint angle to generate a line-slope param.
        """
        
        ri_cpoint_angle = self.dyn['reindeer_cpoint_angle']
        
        max = 10.0
        
        
    def calc_expect_sta2(self, dashboard):
        
        latest_hist = self.history_get(0)
        latest_sta = latest_hist['sta']
        
        ri_img = self.dyn['reindeer_img']
        ri_map_y, ri_map_x, ri_cpoint, ri_angle = self.dyn['reindeer_map_y'], self.dyn['reindeer_map_x'], self.dyn['reindeer_cpoint'], self.dyn['reindeer_angle']
        ri_cpoint_angle = self.dyn['reindeer_cpoint_angle']
        
        #
        # angle diff to determin the status of non-strait road
        #
        angle_diff = abs(ri_angle - 90)
        
        # hacking
        ri_cpoint_angle = ((ri_cpoint_angle * 9.0) + (ri_angle - 90)) / 5.0
        
        #
        # Decrease speed while the cpoint is too close.
        #
        ri_cpoint_x, ri_cpoint_y = ri_cpoint

        ri_img_width, ri_img_height = self.hacjpg.get_resolution(ri_img)
        ri_img_width_half, ri_img_height_half = ri_img_width / 2.0, ri_img_height / 2.0
        ri_cpoint_y_diff = abs(ri_cpoint_y - ri_img_height)
        ri_cpoint_x_diff = abs(ri_cpoint_x - ri_img_width_half) 

        #
        # Increase the speed when I am on road.
        #
        RI_CPOINT_X_DIFF_THOLD = ri_img_width_half / 8.0
        RI_CPOINT_Y_DIFF_THOLD = (ri_img_height_half - 4)
       
        print ("cpoint diff: ", ri_cpoint_x_diff, ri_cpoint_y_diff, 
               "cp-angle: ", self.dyn['reindeer_cpoint_angle'], "cp-angle-final: ", ri_cpoint_angle, 
               ", speed: ", dashboard['speed'])
        
        #
        # Adjust wheel
        #
        expect_sta = self.calibrate_sta(ri_cpoint_angle)
        
        if self.confirm_uturn():
            vbsmsg("*** Detect UTURN ***")
            self.dyn['uturn'] = True
            self.set_speed(self.spec['speed_uturn'])
             
            return self.calibrate_sta_sqrt(expect_sta) * 2.5
        else:
            self.dyn['uturn'] = False
            
        if ri_cpoint_x_diff <= RI_CPOINT_X_DIFF_THOLD:
            """
            cpoint x axis is near. (x-)
            """
            if ri_cpoint_y_diff > RI_CPOINT_Y_DIFF_THOLD:
                """
                cpoint y axis is far. (y+)
                """
                expect_sta = self.calibrate_sta_sqrt(expect_sta) / 8.0
                print("x-, y+")
                
                self.update_speed_abs(increase=True)
            else:
                """
                Maybe u-turn
                """
                expect_sta = self.calibrate_sta(expect_sta)
                print("x-, y- *** Caution. Un-expected. Maybe u-turn? ***")
                self.set_speed(self.spec['speed_uturn'])
        else:
            """
            cpoint x axis is far.
            """
            if ri_cpoint_y_diff > RI_CPOINT_Y_DIFF_THOLD:
                """
                cpoint y axis is also far. 
                """
                expect_sta = self.calibrate_sta_sqrt(expect_sta)
                print("x+, y+")
#                 self.update_speed_abs(increase=False)
                self.set_speed(self.spec['speed_turn'])
            else:
                """
                CAUTION: uturn
                """
                expect_sta = self.calibrate_sta(expect_sta) / 2.0
                print("x+, y-  *** Caution. uturn ***")
                self.set_speed(self.spec['speed_uturn'])
                
        return expect_sta

    def calc_expect_sta(self, dashboard):
        
        latest_hist = self.history_get(0)
        latest_sta = latest_hist['sta']
        
        ri_img = self.dyn['reindeer_img']
        ri_map_y, ri_map_x, ri_cpoint, ri_angle = self.dyn['reindeer_map_y'], self.dyn['reindeer_map_x'], self.dyn['reindeer_cpoint'], self.dyn['reindeer_angle']
        ri_cpoint_angle = self.dyn['reindeer_cpoint_angle']
        
        #
        # angle diff to determin the status of non-strait road
        #
        angle_diff = abs(ri_angle - 90)
        
        # hacking
        ri_cpoint_angle = ((ri_cpoint_angle * 9.0) + (ri_angle - 90)) / 5.0
        
        #
        # Decrease speed while the cpoint is too close.
        #
        ri_cpoint_x, ri_cpoint_y = ri_cpoint

        ri_img_width, ri_img_height = self.hacjpg.get_resolution(ri_img)
        ri_img_width_half, ri_img_height_half = ri_img_width / 2.0, ri_img_height / 2.0
        ri_cpoint_y_diff = abs(ri_cpoint_y - ri_img_height)
        ri_cpoint_x_diff = abs(ri_cpoint_x - ri_img_width_half) 

        #
        # Increase the speed when I am on road.
        #
        RI_CPOINT_X_DIFF_THOLD = ri_img_width_half / 8.0
        RI_CPOINT_Y_DIFF_THOLD = (ri_img_height_half - 4)
        ANGLE_DIFF_THOLD = 30
       
        print ("cpoint diff: ", ri_cpoint_x_diff, ri_cpoint_y_diff, 
               "cp-angle: ", self.dyn['reindeer_cpoint_angle'], "cp-angle-final: ", ri_cpoint_angle, 
               ", speed: ", dashboard['speed'])
        
        #
        # Adjust wheel
        #
        if ri_cpoint_x_diff <= RI_CPOINT_X_DIFF_THOLD:
            """
            cpoint x axis is near. (x-)
            """
            if ri_cpoint_y_diff > RI_CPOINT_Y_DIFF_THOLD:
                """
                cpoint y axis is far. (y+)
                """
                self.update_speed_abs(increase=True)
            else:
                """
                Maybe u-turn
                """
                self.set_speed(self.spec['speed_uturn'])
        else:
            """
            cpoint x axis is far.
            """
            if ri_cpoint_y_diff > RI_CPOINT_Y_DIFF_THOLD:
                """
                cpoint y axis is also far. 
                """
                self.set_speed(self.spec['speed_turn'])
            else:
                """
                CAUTION: uturn
                """
                self.set_speed(self.spec['speed_uturn'])
                
             
         
        if ri_cpoint_x_diff <= RI_CPOINT_X_DIFF_THOLD and angle_diff < ANGLE_DIFF_THOLD:
            """
            Small diff, cpoint near
            """
            vbsmsg("cpoint is near")
            if ri_cpoint_x > ri_img_width_half:
                # cpoint is at right side
                if ri_angle > 90:
                    """
                        |    /    /
                        |   / o /
                    ____|__/___/
                    """
                    sta = math.sqrt(angle_diff) / 2.0
                    return sta
                else:
                    """
                        |  \   \
                        |   \ o \
                    ____|____\___\
                    """
                    return math.sqrt(angle_diff) / 10.0
            elif ri_cpoint_x < ri_img_width_half:
                # cpoint is at left side
                if ri_angle > 90:
                    """
                      /   /   |
                     / o /    |
                    /__/______|
                    """
                    sta =  math.sqrt(angle_diff)
                    sta /= 10.0
                    sta *= (-1)
                    return sta
                else:
                    """
                    \   \     |
                     \ o \    |
                     _\ _\____|
                    """
                    sta = (angle_diff / 10.0)
                    sta *= (-1)
                    return sta
            else:
                return 0
             
#         elif self.dyn['uturn'] == True or self.dyn['uturn_auto_drive'] < 4:
#              
#             vbsmsg(" *** URGENT TURN CAUTION: " + format(self.dyn))
#              
#             if ri_cpoint_x > ri_img_width_half:
#                 # cpoint is at right side
#                 if ri_angle > 90:
#                     """
#                         |    /    /
#                         |   / o /
#                     ____|__/___/
#                     """
#                     sta = angle_diff if angle_diff < self.spec['sta_max'] else self.spec['sta_max']
#                     sta /= 3.0 
#                     return sta
#                 else:
#                     """
#                         |  \   \
#                         |   \ o \
#                     ____|____\___\
#                     """
#                     return math.sqrt(angle_diff)
#             elif ri_cpoint_x < ri_img_width_half:
#                 # cpoint is at left side
#                 if ri_angle > 90:
#                     """
#                       /   /   |
#                      / o /    |
#                     /__/______|
#                     """
#                     sta =  math.sqrt(angle_diff) * (-1)
#                     return sta
#                 else:
#                     """
#                     \   \     |
#                      \ o \    |
#                      _\ _\____|
#                     """
#                     sta = ((angle_diff)) if angle_diff < self.spec['sta_max'] else (self.spec['sta_max'])
#                     sta *= (-1)
#                     sta /= 3.0
#                     return sta
#             else:
#                 return 0
        else:
            """
            Big diff, cpoint is far
            """
            vbsmsg("cpoint is far")
             
            if ri_cpoint_x > ri_img_width_half:
                # cpoint is at right side
                if ri_angle > 90:
                    """
                        |    /    /
                        |   / o /
                    ____|__/___/
                    """
                    sta = math.sqrt(angle_diff)
                    return sta
                else:
                    """
                        |  \   \
                        |   \ o \
                    ____|____\___\
                    """
                    return math.sqrt(angle_diff) / 2.0
            elif ri_cpoint_x < ri_img_width_half:
                # cpoint is at left side
                if ri_angle > 90:
                    """
                      /   /   |
                     / o /    |
                    /__/______|
                    """
                    sta =  math.sqrt(angle_diff) / 2.0
                    sta *= (-1)
                    return sta
                else:
                    """
                    \   \     |
                     \ o \    |
                     _\ _\____|
                    """
                    sta = math.sqrt(angle_diff)
                         
                    sta *= (-1)
                    return sta
            else:
                return 0
            
    def calc_sta(self, dashboard):
        """
        Calculate steering angle (sta). Depend on camera data.
        """
        latest_hist = self.history_get(0)

            
        if self.dyn['reindeer_map_y'] == None:
            """
            Cannot find the road. Do something. plz
            """           
            self.set_speed(self.spec['speed_back_limit'])
                    
            if self.dyn['uturn'] == True and self.dyn['uturn_auto_drive'] < 5:
                self.dyn['uturn_auto_drive'] += 1
                vbsmsg("=== uturn auto ctrl === " + format(self.history[0]))
                self.set_speed(self.spec['speed_uturn'])
                return 30 if latest_hist['sta'] > 0 else -30
        
            return 0
        else:
            """
            Go forward
            """
            self.dyn['uturn_auto_drive'] = 0
            
            self.set_speed_if_negative(self.spec['speed_min'])
            expect_sta = round(self.calc_expect_sta2(dashboard), 4)

            if expect_sta > self.spec['sta_max']:
                vbsmsg("Invalid sta " + str(expect_sta))
                expect_sta = self.spec['sta_max']
            elif expect_sta < self.spec['sta_min']:
                vbsmsg("Invalid sta " + str(expect_sta))
                expect_sta = self.spec['sta_min']
            else:
                vbsmsg("Adjust sta to " + str(expect_sta))
                
            out_sta = expect_sta
            return out_sta
        
    def calc_tho_fixed_speed(self, dashboard, expect_speed=0.6, can_brake=False):
        """
        The goal of this is to return a tho which can keep the car in target speed.
        """
        latest_hist = self.history_get(0)
        latest_tho = latest_hist['tho']
        latest_brk = latest_hist['brk']
        
        speed_diff = abs(expect_speed) - latest_hist['speed']
        
        if self.dyn['uturn'] == True:
            if expect_speed > 0:
                return (0.001, 0.0) # TBD
        
        if expect_speed > 0:
            """
            Want to go ahead. Use brake iff the speed diff is too high
            """
            if speed_diff > 0:
                """
                Too slow. Try tho
                """
                if latest_tho >= self.spec['tho_max']:
                    # Cannot add more tho
                    return (latest_tho, 0.0)
                else:
                    # Add some tho to improve speed
                    tho_left = self.spec['tho_max'] - latest_tho
                    tho2add = tho_left / 200.0
                    tho = latest_tho + tho2add
                    return (tho, 0.0)
            elif speed_diff < 0:
                """
                Too fast. Try to decrease tho
                """
                
                if speed_diff >= (abs(expect_speed) / 2.0):
                    """
                    Urgent brake
                    """
                    brk = self.spec['brk_max']
                    return (0.0, brk)
                
                tho = round(latest_tho * 3 / 4.0, 4)
                return (tho, 0.0)
            else:
                return (latest_tho, 0.0)
        elif expect_speed < 0:
            """
            Want to reverse. Use brake
            """
            if speed_diff > 0:
                """
                Too slow. Try more brk
                """
                if latest_brk >= self.spec['brk_max']:
                    # Cannot add more brake
                    return (0.0, latest_brk)
                else:
                    # Add some brk to improve speed
                    brk_left = self.spec['brk_max'] - latest_brk
                    brk2add = round(brk_left / 100.0, 4)
                    brk = latest_brk + brk2add
                    return (0.0, brk)
            elif speed_diff < 0:
                """
                Too fast. Try to decrease brk
                """
                brk = round(latest_brk * 3 / 4.0, 4)
                return (0.0, brk)
            else:
                return (0.0, latest_brk)
        else:
            """
            Disable tho, the car will stop soon.
            """
            return (0.0, 0.0)
            
        return (0.0, 0.0)
        
    def calc_tho(self, dashboard):
        tho, brk = self.calc_tho_fixed_speed(dashboard, expect_speed=self.dyn['speed'])
        
        if brk > 0:
            return round(brk * (-1), 3)
        else:
            return round(tho, 3)
        
    def camera_task(self, img_in, dashboard):
        """
        Process camera image. Identify my location, the direction, goal, etc.
        
        Output: None
        """
        img = copy.deepcopy(img_in)
        
        img = self.hacjpg.crosscut(img, 0.55, 1.0)
        img = self.hacjpg.color_quantization(img)
        img = self.hacjpg.flatten2rgb(img)
        
        """
        Now I have a img of road data. Try to identify what is a road and what is not.        
        """
#         self.decide_road_prefer_rgb(img, dashboard)
        
        """
        Have two points. The angle of the line is.
        angle = 90 - np.rad2deg(np.arctan2(y[-1] - y[0], x[-1] - x[0]))
        
                    map_x, map_y
             | angle  /
             |      /
             | ?  /o <-- cpoint
             |  / 
        _____|/________
            zero point
        """

        reindeer = self.hacjpg.reindeer2(img, self.dyn['road_prefer_rgb'], prefer_left=self.dyn['road_prefer_left'])
        self.dyn['reindeer_map_y'], self.dyn['reindeer_map_x'], self.dyn['reindeer_cpoint'], self.dyn['reindeer_angle'] = reindeer
        
        if self.dyn['reindeer_cpoint'] != None:
            # Calculate the angle from zero point to cpoint, can imagine this is the wheel angle!
            zero_point = self.hacjpg.get_resolution(img)
            zero_point = (zero_point[0] / 2, zero_point[1])
            cpoint_angle = 90 + self.hacjpg.calc_angle(zero_point, self.dyn['reindeer_cpoint'])
            self.dyn['reindeer_cpoint_angle'] = cpoint_angle
            if cpoint_angle >= 90 or cpoint_angle <= -90:
                errmsg("XXX")
        
        self.hacjpg.show(img, "reindeer", waitkey=1)
        self.dyn['reindeer_img'] = img
        
    def try2drive(self, img, dashboard):
        """
        Input: {"status": "0", "throttle": "0.0200", "brakes": "0.0000",
               "speed": "0.4392", "steering_angle": "0.0000", "time": "1.380", "lap": "1"}
        Output: (sta, tho)
        """ 
        out_sta, out_tho = (0.0, 0.0)
        
        #
        # Save dashboard history
        #
        self.history_update(dashboard)
        
        #        
        # Process camera image. Identify my location, the direction, goal, etc.
        #
        self.camera_task(img, dashboard)
        
        #
        # Calculate sta to maintain direction.
        #
        out_sta = self.calc_sta(dashboard)
        
        #
        # Calculate tho to maintain speed.
        #
        out_tho = self.calc_tho(dashboard)

        return out_sta, out_tho
    
