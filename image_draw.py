import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

 
#Convert width height to a point in a rectangle
def getRectangle(faceDictionary):
    rect = faceDictionary['faceRectangle']
    left = rect['left']
    top = rect['top']
    bottom = top + rect['height']
    right = left + rect['width']
    return ((left, top), (right, bottom))


def drawFaceRectangles(face, image, upperLeftText, upperRightText, lowerText1, lowerText2):

    if len(face) > 0 :
        
        #For each face returned use the face rectangle and draw a red box.
        draw = ImageDraw.Draw(image)

        #font = ImageFont.truetype('/usr/share/fonts/truetype/msttcorefonts/arial.ttf', 10)
        #size = font.getsize(showtext)
        
        (left, top), (right, bottom) = getRectangle(face)
        draw.rectangle(getRectangle(face), outline='red')
        
        font_size = 16
        font_name = "FreeSans.ttf"
        font_path = "/usr/share/fonts//truetype/freefont/%s"% font_name
        font = ImageFont.truetype(font_path, font_size)
        
        # UpperLeftText needs to be required
        (text_width, text_height) = font.getsize(upperLeftText)
        
        if len(upperLeftText) > 0:
            draw.text((left, top-text_height), upperLeftText, font=font)
            if len(upperRightText) > 0:
                draw.text((right-text_width, top-text_height), upperRightText, font=font)
            if len(lowerText1) > 0:
                draw.text((left, bottom), lowerText1, font=font)
            if len(lowerText2) > 0:
                draw.text((left, bottom+text_height), lowerText2, font=font)

        return (True)
    else:
        return (False)
