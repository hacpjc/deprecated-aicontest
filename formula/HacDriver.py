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
            'history_max': 16,
            # speed error tolerance
            'speed_error_tolerance': 0.001,
            'speed_max': 1.6,
            'speed_min': 0.15,
            'speed_update_unit': 0.01,
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
            'reindeer_img': None,
            # If I have choice, take right-hand road?
            'road_prefer_right': True,
            'road_prefer_rgb': (0, 0, 255),
            # Expected speed
            'speed': 0.1,
            'speed_inc_cnt': 0,
            'urgent_turn': False,
            'urgent_turn_auto_drive': 0,
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
                speed = self.spec['speed_update_unit']
            else:
                speed = (self.spec['speed_update_unit'] / 4.0)
                
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
        
    def calc_sta_simple(self, dashboard, expect_sta=0):
        """
        Maintain the sta to expected value.
        """
        latest_hist = self.history_get(0)
        latest_sta = latest_hist['sta']
        
        return expect_sta
        
        diff_unit = (self.spec['sta_max'] / 1000.0)
        
        if expect_sta > 0:
            """
            Want to turn right
            """
            if latest_sta > expect_sta:
                """
                sta is a little bit big -> turning right too much
                """
                diff = latest_sta - expect_sta
                sta2dec = math.sqrt(diff) / 2.0
                if sta2dec < diff_unit:
                    sta2dec = diff_unit
                
                sta = latest_sta - sta2dec
                return sta
                
            elif latest_sta < expect_sta:
                """
                sta is small -> turning right too small, or turning left...
                """
                if latest_sta < 0:
                    return math.sqrt(expect_sta)                    
                else:
                    diff = expect_sta - latest_sta
                    sta2add = math.sqrt(diff) / 2.0
                    if sta2add < diff_unit:
                        sta2add = diff_unit
                        
                    sta = latest_sta + sta2add
                    return sta
            else:
                return latest_sta
            
        elif expect_sta < 0:
            """
            Want to turn left
            """
            if latest_sta > expect_sta:
                """
                sta is a little bit big -> turning left small, or turning right
                """
                if latest_sta > 0:
                    return math.sqrt(abs(expect_sta)) * (-1)
                else:
                    diff = latest_sta - expect_sta
                    sta2dec = math.sqrt(diff)
                    if sta2dec < diff_unit:
                        sta2dec = diff_unit
                    
                    sta = latest_sta - sta2dec
                    return sta
                
            elif latest_sta < expect_sta:
                """
                sta is small -> turning left too much
                """
                diff = expect_sta - latest_sta
                sta2add = math.sqrt(diff)
                if sta2add < diff_unit:
                    sta2add = diff_unit
                    
                sta = latest_sta + sta2add
                return sta
            else:
                return latest_sta
        else:
            return 0
        
    def is_road_straight(self):
        pass
         
    def calc_expect_sta(self, dashboard):
        ri_map_y, ri_map_x, ri_cpoint, ri_angle = self.dyn['reindeer_map_y'], self.dyn['reindeer_map_x'], self.dyn['reindeer_cpoint'], self.dyn['reindeer_angle']
        
        #
        # angle diff to determin the status of non-strait road
        #
        angle_diff = abs(ri_angle - 90)
        
        #
        # Decrease speed while the cpoint is too close.
        #
        ri_cpoint_x, ri_cpoint_y = ri_cpoint

        ri_img_width, ri_img_height = self.hacjpg.get_resolution(self.dyn['reindeer_img'])
        ri_img_width_half, ri_img_height_half = ri_img_width / 2.0, ri_img_height / 2.0
        ri_cpoint_y_diff = abs(ri_cpoint_y - ri_img_height)
        ri_cpoint_x_diff = abs(ri_cpoint_x - ri_img_width_half) 

        #
        # Increase the speed when I am on road.
        #
        RI_CPOINT_X_DIFF_THOLD = 60
        RI_CPOINT_Y_DIFF_THOLD = 40
        ANGLE_DIFF_THOLD = 30 # Cannot > 45
        
        self.dyn['urgent_turn'] = False
        
        if ri_cpoint_x_diff <= RI_CPOINT_X_DIFF_THOLD:
            if ri_cpoint_y_diff > RI_CPOINT_Y_DIFF_THOLD:
                if angle_diff < ANGLE_DIFF_THOLD:
                    self.update_speed_abs(increase=True)
                else:
                    self.update_speed_abs(increase=False)
            else:
                self.update_speed_abs(increase=False)
        else:
            """
            cpoint is far
            """
            self.update_speed_abs(increase=False)
            
            if angle_diff < ANGLE_DIFF_THOLD:
                pass
            else:
                """
                CAUTION: Urgent turn.
                """
                self.set_speed(self.spec['speed_min'])
                self.dyn['urgent_turn'] = True
        
        #
        # Adjust wheel
        #
        
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
                    sta = angle_diff / 10.0
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
                    sta =  math.sqrt(angle_diff) * (-1)
                    sta /= 4.0
                    return sta
                else:
                    """
                    \   \     |
                     \ o \    |
                     _\ _\____|
                    """
                    sta = (angle_diff / 10.0) * (-1)
                        
                    return sta
            else:
                return 0
            
        elif self.dyn['urgent_turn'] == True:
            
            vbsmsg(" *** URGENT TURN CAUTION")
            
            if ri_cpoint_x > ri_img_width_half:
                # cpoint is at right side
                if ri_angle > 90:
                    """
                        |    /    /
                        |   / o /
                    ____|__/___/
                    """
                    sta = angle_diff if angle_diff < self.spec['sta_max'] else self.spec['sta_max'] 
                    return sta
                else:
                    """
                        |  \   \
                        |   \ o \
                    ____|____\___\
                    """
                    return math.sqrt(angle_diff)
            elif ri_cpoint_x < ri_img_width_half:
                # cpoint is at left side
                if ri_angle > 90:
                    """
                      /   /   |
                     / o /    |
                    /__/______|
                    """
                    sta =  math.sqrt(angle_diff) * (-1)
                    return sta
                else:
                    """
                    \   \     |
                     \ o \    |
                     _\ _\____|
                    """
                    sta = ((angle_diff) * (-1)) if angle_diff < self.spec['sta_max'] else (self.spec['sta_max'] * (-1))
                    return sta
            else:
                return 0
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
                    if angle_diff < 10:
                        sta = math.sqrt(ri_angle - 90)
                    else:
                        sta = angle_diff / 4.0
                    return sta
                else:
                    """
                        |  \   \
                        |   \ o \
                    ____|____\___\
                    """
                    return math.sqrt(angle_diff)
            elif ri_cpoint_x < ri_img_width_half:
                # cpoint is at left side
                if ri_angle > 90:
                    """
                      /   /   |
                     / o /    |
                    /__/______|
                    """
                    sta =  math.sqrt(angle_diff) * (-1)
                    return sta
                else:
                    """
                    \   \     |
                     \ o \    |
                     _\ _\____|
                    """
                    if angle_diff < 10:
                        sta = math.sqrt(angle_diff) * (-1)
                    else:
                        sta = (angle_diff / 4.0) * (-1)
                        
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
            
            if self.dyn['urgent_turn'] == True and self.dyn['urgent_turn_auto_drive'] < 8:
                self.dyn['urgent_turn_auto_drive'] += 1
                vbsmsg("Auto turn ctrl")
                return latest_hist['sta']
            else:
                return 0.0
            
        else:
            """
            Go forward
            """
            self.dyn['urgent_turn_auto_drive'] = 0
            
            self.set_speed_if_negative(self.spec['speed_min'])
            expect_sta = round(self.calc_expect_sta(dashboard), 4)
            vbsmsg("Adjust sta to " + str(expect_sta))
            if expect_sta > self.spec['sta_max']:
                errmsg("Invalid sta " + str(expect_sta))
                
            out_sta = self.calc_sta_simple(dashboard, expect_sta)
            return out_sta
        
    def calc_tho_fixed_speed(self, dashboard, expect_speed=0.6, can_brake=False):
        """
        The goal of this is to return a tho which can keep the car in target speed.
        """
        latest_hist = self.history_get(0)
        latest_tho = latest_hist['tho']
        latest_brk = latest_hist['brk']
        
        speed_diff = abs(expect_speed) - latest_hist['speed']
        
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
                    brk2add = round(brk_left / 50.0, 4)
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
            return brk * (-1)
        else:
            return tho
        
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
        Have two points. The angle of the line is.
        angle = 90 - np.rad2deg(np.arctan2(y[-1] - y[0], x[-1] - x[0]))
        
                    map_x, map_y
             | angle  /
             |      /
             | ?  /o <-- cpoint
             |  / 
        _____|/________
        """
        reindeer = self.hacjpg.reindeer2(img, self.dyn['road_prefer_rgb'])
        self.dyn['reindeer_map_y'], self.dyn['reindeer_map_x'], self.dyn['reindeer_cpoint'], self.dyn['reindeer_angle'] = reindeer
        
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
    
