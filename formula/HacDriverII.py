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

class HacDriverII(Hacjpg):
    """
    This is the main class to drive the car. See try2drive method.
    """
    
    def __init__(self, is_debug=False):
        self.is_debug = is_debug
        
        self.hacjpg = Hacjpg()
        
        #
        # Constant Car configurations
        #
        self.spec = {
            # Throttle -1.0 ~ 1.0. brk 1.0 means throttle -1.0
            'tho_max': 0.4,
            'tho_min': 0.0,
            'tho_unit': 0.001,
            'brk_max': 0.6,
            'brk_min': 0.0,
            'brk_unit': 0.0015,
            # Steering angle -40 ~ 40 degree
            'sta_max': 40,
            'sta_min': -40,
            # history
            'history_max': 16,
            # speed error tolerance
            'speed_max': 1.1,
            'speed_min': 0.6,
            'speed_uturn': 0.7,
            'speed_turn': 0.75,
            'speed_update_unit': 0.015,
            'speed_back_limit': -1.0,
            }
        msg("Car spec: " + format(self.spec))
        
        #
        # Save dashboard history
        # 
        self.history = []
        
        #
        # Dynamic data/configuration
        #
        self.dyn = {
            # reindeer result
            'ri_angle': None,
            'ri_cpoint': None,
            'ri_cpoint_angle': None,
            'ri_cpoint_distance': 0,
            'ri_area_percent': 0,
            'ri_img': None,
            # If I have choice, take right-hand road?
            'road_prefer_left': False,
            'road_prefer_rgb': (0, 0, 255),
            # Expected speed
            'speed': self.spec['speed_min'],
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
        cnt = 0.0
        sum = 0.0
        for h in self.history:
            sum = h['sta']
            cnt += 1.0
            
        return round(sum / cnt, 4)
    
    def history_get_sta_concussion_rate(self, backlog=4):
        """
        Get the sta concussion rate
        """
        
        cnt = 0
        max = len(self.history)
        
        if max <= 1:
            # Need at least 2 history to calculate concussion
            return 0
        
        progress = 0
        prev_sta = 0
        for h in self.history:
            if prev_sta == 0:
                prev_sta = 1 if h['sta'] > 0 else -1
                continue
            
            if prev_sta * h['sta'] < 0:
                prev_sta = 1 if h['sta'] > 0 else -1
                cnt += 1
                
            progress += 1
            if progress >= backlog:
                break
        
        return cnt / float(max)
    
    def history_get_speed(self):
        history = self.history_get(0)
        if history == None:
            return 0.0
        else:
            return history['speed']
        
    def calc_percentage(self, v, base):
        if base == 0:
            errmsg("Invalid input argument")
            return 0
            
        return round(v / float(base), 4) * 100

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
        
        >>> math.sqrt(90) = 9.486832980505138
        >>> math.sqrt(45) = 6.708203932499369
        >>> math.sqrt(30) = 5.477225575051661
        >>> math.sqrt(15) = 3.872983346207417
        >>> math.sqrt(1) = 1.0
        >>> math.sqrt(0.5) = 0.7071067811865476
        """
        output = 0.0
        
        if sta > 0:
            output = math.sqrt(sta)
        elif sta < 0:
            output = math.sqrt(abs(sta)) * (-1)
        
        return round(output, 4)
    
    def calc_expect_sta3(self, dashboard):
        """
           ROAD
              |
              V
        _____________________  
        |   .. /..           |
        |  .. /..            |
        | ...o.cpoint        |
        | ../..              |
        |________o___________
              zero point
        """
        
        zero_point = self.hacjpg.get_resolution(self.dyn['ri_img'])
        zero_point = (zero_point[0] / 2, zero_point[1])
        
        #        
        # Input
        #
        ri_cpoint_angle = self.dyn['ri_cpoint_angle']
        ri_area_percent = self.dyn['ri_area_percent']
        ri_cpoint = self.dyn['ri_cpoint']
        ri_cpoint_x, ri_cpoint_y = ri_cpoint
        ri_cpoint_distance = self.dyn['ri_cpoint_distance']
        speed = self.history_get_speed()
        concussion_rate = self.history_get_sta_concussion_rate(self.spec['history_max'])
        
        #
        # sta calibrate - cpoint angle (-90 ~ 90). The most effective information.
        # 
        out_sta = ri_cpoint_angle
        out_sta = self.calibrate_sta(out_sta)
        out_sta = self.calibrate_sta_sqrt(out_sta)

        #
        # sta calibrate - speed (TBD) 
        #
        
        #
        # sta calibrate - If concussion rate is large. Decrease sta
        # Range: 0.0 ~ 1.0  
        #
        # This can help to reduce left-right-left-right wheel concussion.
        #
        factor = (1.0 - math.sqrt(concussion_rate))
        out_sta *= factor 
        
        #
        # sta calibrate - area, if the area is small, the road is far. Unlock sta
        #
        # Usually 75% in normal road. If it's < 50%, take care.
        #
        if ri_area_percent < 50:
            factor = 250.0 / float(1 + ri_area_percent)
        elif ri_area_percent < 70:
            factor = 180.0 / float(1 + ri_area_percent)
        elif ri_area_percent < 75:
            factor = 150.0 / float(1 + ri_area_percent)
        else:
            factor = 80.0 / float(1 + ri_area_percent)
            
        out_sta *= factor
        
        #
        # Speed management
        #
        if ri_area_percent >= 72:
            # Wheel stable
            self.update_speed_abs(increase=True)
            if abs(self.dyn['ri_angle'] - 90) < 10:
                # Possibly in strait road. Raise speed.
                self.update_speed_abs(increase=True)
        elif ri_area_percent >= 65:
            # Turn
            self.update_speed_abs(increase=False)
        elif ri_area_percent >= 50:
            # Turn
            self.set_speed(self.spec['speed_turn'])
        else:
            # Urgent turn
            self.set_speed(self.spec['speed_uturn'])
        
        return self.calibrate_sta(out_sta)
        

            
    def calc_sta(self, dashboard):
        """
        Calculate steering angle (sta). Depend on camera data.
        """
        if self.dyn['ri_cpoint'] == None:
            """
            Cannot find the road. Do something. plz
            """
            self.set_speed(self.spec['speed_back_limit'])
                    
            if self.dyn['uturn'] == True and self.dyn['uturn_auto_drive'] < 5:
                prev_history = self.history_get(1)
                if prev_history != None:
                    """
                    Try to follow the previous sta. This can help the car to maintain correct direction. 
                    """
                    self.dyn['uturn_auto_drive'] += 1
                    vbsmsg(" * WARNING: uturn auto ctrl" + format(self.history[0]))
                    self.set_speed(self.spec['speed_uturn'])
                    return self.spec['sta_max'] if prev_history['sta'] > 0 else self.spec['sta_min']
        
            return 0.0
        else:
            """
            Go forward
            """
            self.dyn['uturn_auto_drive'] = 0
            
            self.set_speed_if_negative(self.spec['speed_min'])
            expect_sta = round(self.calc_expect_sta3(dashboard), 4)
            if expect_sta > self.spec['sta_max']:
                vbsmsg("Invalid sta " + str(expect_sta))
                expect_sta = self.spec['sta_max']
            elif expect_sta < self.spec['sta_min']:
                vbsmsg("Invalid sta " + str(expect_sta))
                expect_sta = self.spec['sta_min']
            
            vbsmsg("sta: " + str(expect_sta))
            out_sta = expect_sta
            return out_sta
    
    def ______tho(self):
        pass
    
    def calc_tho_fixed_speed(self, dashboard, expect_speed=0.6, can_brake=False):
        """
        The goal of this is to return a tho which can keep the car in target speed.
        """
        latest_hist = self.history_get(0)
        latest_tho = latest_hist['tho']
        latest_brk = latest_hist['brk']
        
        # The latest_hist['speed'] is always positive.
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
                    tho2add = self.spec['tho_unit']
                    tho = latest_tho + tho2add
                    return (tho, 0.0)
            elif speed_diff < 0:
                """
                Too fast. Try to decrease tho
                """
                if abs(speed_diff) >= (abs(expect_speed) / 2.0):
                    """
                    Urgent brake (ABS)
                    """
                    vbsmsg("ABS brake")
                    brk = self.spec['brk_min']
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
                    brk2add = self.spec['brk_unit']
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
            Want to stop. Disable tho, the car will stop soon.
            """
            return (0.0, 0.0)
            
        return (0.0, 0.0)
        
    def calc_tho(self, dashboard):
        """
        Calculate tho value by expect speed. Recommend unit: 0.001
        
        Any tho like 0.0001 seems useless.
        """
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
        latest_hist = self.history_get(0)
        
        img = copy.deepcopy(img_in)
        
        img = self.hacjpg.crosscut(img, 0.55, 1.0)
#         img = self.hacjpg.color_quantization(img)
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
            zero point
        """
        reindeer = self.hacjpg.reindeer3(img, self.dyn['road_prefer_rgb'], prefer_left=self.dyn['road_prefer_left'])
        self.dyn['ri_cpoint'], self.dyn['ri_angle'], self.dyn['ri_area_percent'] = reindeer
        
        self.dyn['ri_img'] = img
        
        if self.is_debug == True:
            img_dbg = copy.deepcopy(img)
            self.hacjpg.draw_text(img_dbg, format(latest_hist['speed']), (0, 12), rgb=(255, 255, 255))
            self.hacjpg.draw_text(img_dbg, format(latest_hist['sta']), (0, 24), rgb=(255, 255, 255))
            self.hacjpg.draw_text(img_dbg, format(latest_hist['tho']), (0, 36), rgb=(255, 255, 255))
            
            self.hacjpg.show_nowait(img_dbg, "reindeer")
        
        if self.dyn['ri_cpoint'] != None:
            # Calculate the angle from zero point to cpoint, can imagine this is the wheel angle!
            zero_point = self.hacjpg.get_resolution(img)
            zero_point = (zero_point[0] / 2, zero_point[1])
            
            cpoint_angle = 90 + self.hacjpg.calc_angle(zero_point, self.dyn['ri_cpoint'])
            self.dyn['ri_cpoint_angle'] = cpoint_angle
            if cpoint_angle >= 90 or cpoint_angle <= -90:
                errmsg("XXX")
                
            self.dyn['ri_cpoint_distance'] = self.hacjpg.calc_distance(zero_point, self.dyn['ri_cpoint'])
        
        
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
    
