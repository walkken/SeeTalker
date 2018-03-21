#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, send_file

# Libraries created for this program by Ken
from ms_cognitive_imagerec import ms_WhatDoYouSee, ms_WhoDoYouSee, ms_GetFaceAttribs, FaceAttribs
# for Intel Neural Compute Stick 
#from ncs_image_classify import ncs_init, ncs_classify_image, ncs_close
from al_Alerts import al_StartAlertTriggers, al_CancelAlertTriggers
from image_draw import drawFaceRectangles
from eml_Email import eml_SendEmail
# other libraries
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from time import sleep

# Alexa Flask-Ask
import json
import logging
from flask_ask import Ask, statement, question, context as ask_context, request as ask_request, session as ask_session


import operator
import base64
import http.client
import webbrowser

class SelfieAlert:
    countdown_secs = 3
    countdown_interval = 1
    secs_rem = 2
    tmr = None
    requestId = None
    apiEndpoint = None
    apiAccessToken = None
    image = None
    
# import camera driver
##if os.environ.get('CAMERA'):
#    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
#else:
#    from camera import Camera
    
from camera_pi import Camera
camera = Camera()

image_file = 'image_file.png'

# this sound is not guaranteed to be available.  replace sound.  use ffmpeg to translate to Alexa requirements
camera_sound_url = 'https://videotalker.blob.core.windows.net/videoblob/camera_sound_conv.mp3'

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)
ask = Ask(app, "/")

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.launch
def alexa_launch():
 
    return question('See Talker Active, How can I help you?')



@ask.intent('Selfie')
def alexa_Selfie():

    # do selfie countdown, capture image and set time to email photo with WhatDoYouSee for email body
    selfie(True)
    
    response_txt = "You're selfie was taken and will be emailed"
    
    return statement(response_txt)


@ask.intent('WhoDoYouSee')
def alexa_WhoDoYouSee():
    response = "no response"
    response = who_see(fAlexa=True)
        
    return statement(response)

@ask.intent('WhatDoYouSee')
def alexa_whatsee():

    response = "no response"
    response = what_see(fAlexa=True)
    return statement(response)
   
 
@ask.session_ended
def session_ended():

    return "{}", 200

@ask.on_session_started
def new_session():
    log.info('new session started')
    
@app.route('/')
def index():
    """Video streaming home page."""
    print ("index page")
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/what_see')
def what_see(fAlexa=False):

    body = camera.get_frame()
    
    #body = open(image_file, 'rb').read()
    
    parsedText = ms_WhatDoYouSee (body)
   
    imageFile_png = base64.b64encode(body).decode('ascii')   


    if fAlexa:
        return (parsedText)
    else:
        return render_template("what_see.html", what_see = parsedText, what_see_image = imageFile_png)


@app.route('/get_image')
def get_image():
    body = camera.get_frame()
     
    with open(image_file, 'wb') as f:
        f.write(body)
        f.close()
     
    return send_file(image_file, mimetype='image/jpg')



@app.route('/who_see')
def who_see(fAlexa=False):
    
    body = camera.get_frame()
 
    response = ms_WhoDoYouSee (body)
    
    n=0
    if len(response) > 0:
        for face in response:
            n += 1
            faceAttribs = ms_GetFaceAttribs (face)
            if n == 1:
                img = Image.open(BytesIO(body))
        
            upperLeftText = faceAttribs.profile_txt
            upperRightText = ""            

            lowerText1 = "Emotion: %s %2.f%%"% (faceAttribs.top_emotion, faceAttribs.top_emotion_conf)
            lowerText2 = faceAttribs.glasses_txt
        
            drawFaceRectangles(face, img, upperLeftText, upperRightText, lowerText1, lowerText2)
            
            img.save(image_file, 'PNG')
            
            img_str = open(image_file, 'rb').read()
            
            if faceAttribs.glasses == 'NoGlasses':
                glasses_txt = ""
            else:
                glasses_txt = "%s is wearing %s"% (faceAttribs.gender_noun, faceAttribs.glasses)
                
            top_emotion_txt = "%s top emotion is %s at %2.f %% confidence"% (faceAttribs.gender_possessive, faceAttribs.top_emotion, faceAttribs.top_emotion_conf)
            
            iSeeText = "I see a %s age %d %s. %s. "% (faceAttribs.gender, faceAttribs.age, top_emotion_txt, glasses_txt)
            profile = "%s age %d"% (faceAttribs.gender, faceAttribs.age)
            
            if n==1:
                finalText = iSeeText
            else:
                finalText = finalText + iSeeText
                
        # show image on screen which can be saved
        img.show()

                        
        if fAlexa:
            return(finalText)
        else:
            buffer = BytesIO()
            img.save(buffer, 'PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode('ascii')

            return render_template("who_see.html", who_see = finalText, who_see_image = img_str)
 
        
    else:
        iSeeText = "No Face Detected"
        return (iSeeText)

@app.route('/selfie')
def selfie(fAlexa=False):

    print ("starting selfie")
    
    if fAlexa:
        SelfieAlert.requestId = ask_request.requestId
               
        SelfieAlert.apiEndpoint = ask_context.System.apiEndpoint
        SelfieAlert.apiAccessToken = 'Bearer ' + ask_context.System.apiAccessToken
                
       # start downdown for selfie using Alert library
       # SelfieAlert.secs_rem = SelfieAlert.countdown_secs
       # SelfieAlert.tmr = al_StartAlertTriggers (SelfieAlert.countdown_interval, SelfieAlert_Handler)

        for secs in range (SelfieAlert.countdown_secs,0,-1):
            selfie_txt = "Selfie will be taken in " if secs == SelfieAlert.countdown_secs else ""
            secs_txt = "second" if secs == 1 else "seconds"
            if secs != 0:     
                response_txt = ("%s %d %s"% (selfie_txt, secs, secs_txt))
                PostDirective_SpeechText(SelfieAlert.requestId, SelfieAlert.apiAccessToken, response_txt)
                sleep(1)
                 
        #' Smile!
        PostDirective_SpeechText(SelfieAlert.requestId, SelfieAlert.apiAccessToken, "Smile")
    
        # save frame, then aysychronously set timer to email photo later.so that Alexa timout doesn't occur
        SelfieAlert.image = camera.get_frame()
        # Make camera sound
        PostDirective_SpeechText(SelfieAlert.requestId, SelfieAlert.apiAccessToken, GetSound_SSML(camera_sound_url))
        sleep(1)
        
        # take selfie in N seconds
        fRepeatTimer = False #want single countdown (2 secs), not repeated intervals
        timerSecs = 2
        SelfieAlert.tmr = al_StartAlertTriggers (timerSecs, SelfieAlert_EmailHandler, fRepeatTimer)

        return
    else:
        SelfieAlert.image = camera.get_frame() 
        # take selfie in N seconds
        SelfieAlert.tmr = None

        response_txt = SelfieAlert_EmailHandler()
        
        return (response_txt)
    
    

def SelfieAlert_EmailHandler():

    # Image should have been captured earlier
    if SelfieAlert.image != None:
        body = SelfieAlert.image
        
        # Save image to file
        with open(image_file, 'wb') as f:
            f.write(body)
            f.close()

        see_txt = ms_WhatDoYouSee(body)
        print ("see_txt=%s"% see_txt)
        
        if len(see_txt) > 0:
            
            # sending email is optional. This is good for testing, but should use secure storage
            # change this
            # not a good idea to hard code this info, but I used a test email and used as a quick POC for email.  Best to get the info from a secure location.
            fromAddr = 'change this'
            toAddr = 'change this'
            email_pwd = 'change this or reference from a function'
            
            # send email - must define from and to address
            #  this is not secure
            eml_SendEmail(fromAddr, toAddr, email_pwd, "See Talker Selfie", see_txt, image_file)
            response_txt = "Selfie taken and email sent successfully"
 
            img = Image.open(BytesIO(SelfieAlert.image))
            img.show(title=see_txt)

        else:
            response_txt = "There was a problem taking the selfie!"

    
    return (response_txt)

def GetSound_SSML(sound_url):
    # only called once, but might be extended for more sophisticated SSML
    ssml_txt = ("<speak> <audio src='%s' /> </speak>"% sound_url)
    print ("ssml text: %s"% ssml_txt)

    # not using this now, but may be needed for more advanced SSML with a POST
    output_sound = {
    "type": "SSML",
    "ssml": ssml_txt
    #"ssml": "<speak> <audio src=sound_url /> </speak>"
    }
    
    return (ssml_txt)
        



def PostDirective_SpeechText(requestId, apiAccessToken, speech_txt):
    
    directive_hdr = {
        'Content-Type': 'application/json',
        'Authorization': apiAccessToken
    }

    
    directive_body = { 
      "header":{ 
        "requestId":requestId
       },
      "directive":{ 
        "type":"VoicePlayer.Speak",
        "speech":speech_txt}
    }
    
    print("requestId=%s apiToken=%s"% (requestId, apiAccessToken))
    print("speech_txt = %s"% speech_txt)

    try: 
        api_url = 'https://api.amazonalexa.com/v1/directives'
        json_body = json.dumps(directive_body)

        conn = http.client.HTTPSConnection('api.amazonalexa.com')
        response = conn.request("POST", '/v1/directives', json_body, directive_hdr)
        #response = conn.getresponse()

        conn.close()
         
        #response = requests.post(api_url, headers=directive_hdr, data=directive_hdr)
        

        
    except Exception as e:
        print('Error:')
        print(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)