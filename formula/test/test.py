
import cv2
import base64
import numpy

from PIL  import Image
from io   import BytesIO

class hacjpg():
    """
    Use this abstract jpg class to simplify image (jpeg) processing by using cv2 module.
    OpenCV tutorial: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html
    
    Depend: cv2, base64
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
    
    def show(self, img, name = "image", scale = 1.0):
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        cv2.waitKey(1)

def test_func1():
    b64img = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCADwAUADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKA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"
    
    myjpg = hacjpg()
    print ("...Convert base64 to an img: " + b64img)
    img = myjpg.open_base64tojpg(b64img)
    
    print ("...Display base 64 img: ", format(img))
    myjpg.show(img)
    

if __name__ == "__main__":
    import time
    
    func = test_func1
    
    print("...Running func: " + str(test_func1))
    func()
    
    time.sleep(8)
