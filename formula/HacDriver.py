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
            'brk_max': 0.1,
            'brk_min': 0.0,
            # Steering angle -45 ~ 45
            'sta_max': 10,
            'sta_min': -10,
            # history
            'history_max': 32,
            # speed error tolerance
            'speed_error_tolerance': 0.001,
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
            'speed': 0.0,
            'road': None,
            'road_diff': 0,
            'cnt': 0
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
        
    def calc_sta_simple(self, dashboard, expect_sta=0):
        latest_hist = self.history_get(0)
        latest_sta = latest_hist['sta']
        latest_speed = latest_hist['speed']
        
        if latest_sta > expect_sta:
            """
            sta is a little bit big -> turning right too much
            """
            diff = latest_sta - expect_sta
            
            return math.sqrt(diff) * (-1)
            
        elif latest_sta < expect_sta:
            diff = expect_sta - latest_sta
            
            return math.sqrt(diff)
        else:
            return 0.0
            
        
    def calc_sta(self, dashboard):
        """
        To turn to the left channel, try: -10 * 10 fps
        """
        road_diff = self.dyn['road_diff']
        
        if road_diff > 0:
            """
            Road at left-hand. Keep sta < 0
            """
            expect_sta = math.sqrt(road_diff) * (-1)
        else:
            """
            Road at right-hand
            """
            expect_sta = math.sqrt(abs(road_diff))
            
        print ("expect sta: " + format(expect_sta))
        return round(self.calc_sta_simple(dashboard, expect_sta), 4)
        
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
                    tho2add = round(tho_left / 30.0, 4)
                    tho = latest_tho + tho2add
                    return (tho, 0.0)
            elif speed_diff < 0:
                """
                Too fast. Try to decrease tho
                """
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
                    brk2add = round(brk_left / 30.0, 4)
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
        width, height = self.hacjpg.get_resolution(img)
        
        self.hacjpg.show(img, "camera", waitkey=1)
        
        self.dyn['speed'] = 0.3
        
        avg = self.hacjpg.reindeer(img, (0, 0, 255))
        
        diff = (width / 2) - avg
        
        self.dyn['road_diff'] = diff
        
        print("dyn:", format(self.dyn))
        
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
        # Calculate tho to maintain speed.
        #
        out_tho = self.calc_tho(dashboard)
        
        #
        # Calculate sta to maintain direction.
        #
        out_sta = self.calc_sta(dashboard)
        
        return out_sta, out_tho
    
