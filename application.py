# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Request, Response
from werkzeug.debug import DebuggedApplication
import json
import os
import io
import pickle
import threading

# Normal Code
application = Flask(__name__)

print '\n### LOGGING : Flask started ###\n'

# Threading
global lock
lock = threading.Lock()

@application.route('/')

def index():
    
    return render_template('index.html')


@application.route('/audience_reach_queue', methods=["POST"])

def audience_reach_queue():
    
    print "\nAUDIENCE REACH : audience_reach_queue() submitted via 'submit' button"

    from helper_functions import audienceReachQueue,requestIdGenerator
    
    apiPublicKey =  request.form['apiPublicKey']
    apiSecretKey = request.form['apiSecretKey']
    requestID = requestIdGenerator()

    print "\nAUDIENCE REACH : Detected required form fields"

    print "apiPublicKey=" + apiPublicKey
    print "apiSecretKey=" + apiSecretKey        
    print "requestID=",requestID

    # Queue job to request audience data
    
    #thread.start_new_thread(audienceReachQueue,(apiPublicKey,apiSecretKey,requestID))
    initialThead = threading.Thread(target=audienceReachQueue, args=(apiPublicKey,apiSecretKey,requestID))
    initialThead.start()       

    return requestID
    
@application.route('/audience_reach_poll', methods=["POST"])

def audience_reach_grabber_poll():

    from helper_functions import audienceReachCheck
    
    requestID = request.form['requestID']    

    requestdata = audienceReachCheck(requestID)

    return requestdata            

@application.errorhandler(500)

def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')    
    return(e)
    #return 'An internal error occurred.', 500

if __name__ == "__main__":

    application.debug = True
    application.run()