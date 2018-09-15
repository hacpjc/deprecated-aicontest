import sys, os
import base64
from Hacjpg import Hacjpg

def print_base64_encode(path):
    with open(path, "rb") as image_file:
        str = base64.b64encode(image_file.read())
        print str

def normalize_traffic_sign(path):
    hacjpg = Hacjpg()
    
    print_base64_encode(path)
    img = hacjpg.open_path(path)
    
    # Resize to 50x25, usually can fit.
    resized_img = hacjpg.resize(img, 50, 25)
    
    print(hacjpg.get_unique_colors(resized_img))
    flat_img = hacjpg.flatten2rgb(resized_img)
    print(hacjpg.get_unique_colors(flat_img))
    
    return flat_img    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Command argument: <dir of traffic-sign>")
        
    print ("...input dir path: " + sys.argv[1])
            
    all_traffic_sign = []
    dirpath = "./traffic-sign-input"
    for root, dirs, files in os.walk(dirpath):
        path = root.split(os.sep)
        for file in files:
            print("...Reading file path: " + dirpath + file)
            traffic_sign = normalize_traffic_sign(dirpath + "/" + file)
            data = {'name': file, 'img': traffic_sign}
            all_traffic_sign.append(data)
        
    hacjpg = Hacjpg()    
    for data in all_traffic_sign:
        print("...Output img file: " + dirpath + "/" + data['name'])
        hacjpg.show(data['img'], "traffic-sign", waitkey=0)
        hacjpg.overwrite(data['img'], dirpath + "/" + data['name'])