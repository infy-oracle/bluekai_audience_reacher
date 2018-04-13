import sys
import pickle
import json

# +++your code here+++
# Define print_words(filename) and print_top(filename) functions.

def audienceReachQueue(publicKey,privateKey,requestID):

  print "\nAUDIENCEREACH : audienceReachQueue() started"
    
  import os
  import urllib
  import urllib2
  import cookielib
  import urlparse
  import hashlib 
  import hmac
  import base64
  import random    
  import time
  import threading
  
  # Write requestID to memory so we can poll the status of it
  this_request = {} 
  this_request["status"] = "not completed"
  this_request["request_id"] = requestID
  this_request["notes"] = []  
  writeToMem(requestID,this_request)

  # FUNCTION : audienceReachGrabber (threaded)
  def audienceReachGrab(requestID,audienceID,publicKey,privateKey):
    
    global all_requests
    global lock

    print "AUDIENCE REACH : Thread started to get reach for audience ID=" + audienceID    
    print ""
    urlRequest = "http://services.bluekai.com/Services/WS/audiences/" + audienceID

    returned_audience = apiCall(urlRequest,"GET",None,publicKey,privateKey)
    
    if type(returned_audience) is not str:
      
      print "AUDIENCE REACH : API Error : audienceID=" + audienceID + " : trying again"

      audienceReachGrab(requestID,audienceID,publicKey,privateKey)
                  
    else:

      #print "AUDIENCE REACH : audienceID=",audienceID,"pre  : locked=",lock.locked()
      print ""      
      
      if lock.locked() is True:
        print "----------LOCKED!!!-----"
      else:
        print "------NOT LOCKED!!!-----"

      lock.acquire() # lock thread
      if lock.locked() is True:
        print "----------LOCKING!!!-----"
      else:
        print "------NOT LOCKED!!!-----"


      returned_audience = json.loads(returned_audience)
            
      print "AUDIENCE REACH : Thread returned audience data for audienceID=" + audienceID      
      
      audience_reach = str(returned_audience["reach"])      
      audience_reach = "{:,}".format(int(audience_reach))      

      # Update Reach
      print "AUDIENCE REACH : audienceID=" + audienceID + " : writing reach to memory=" + audience_reach + "\n"
      print ""      
      
      this_request = readFromMem(requestID)
      this_request["audiences"][audienceID]["Reach"] = audience_reach

      print json.dumps(this_request["audiences"],indent=4,sort_keys=True)

      #Check if job finished
      if audienceReachCompletion(this_request["audiences"]) is True:

        #Update status if completed
        this_request["status"] = "completed"        

      writeToMem(requestID,this_request)        
                  
      lock.release() # unlock thread

      if lock.locked() is True:
        print "----------LOCKED!!!-----"
      else:
        print "------UNLOCKING!!!-----"


      

      #print "\naudienceID=" + audienceID + " : written to allrequests : " + all_requests[requestID]["audiences"]["data"][audienceID] + "|" + str(int(time.time()))
    
  # FUNCTION : Check number of requests completed
  def audienceReachCompletion(audienceReaches):

    completed = True

    for audienceID in audienceReaches:
      
      if audienceReaches[audienceID]["Reach"] == "In Progress...":

        completed = False

    return completed

  # FUNCTION : apiHelper
  def apiCall(apiURL,requestType,data,publicKey,privateKey):

    #print "\nAPICALL : apiCall() started"
    Url = apiURL

    if(requestType == "GET"):
      newUrl = signatureInputBuilder(Url, 'GET', None,publicKey,privateKey)
      api_call = doRequest(newUrl, 'GET', None)
      return api_call

    elif(requestType == "POST"):
      newUrl = signatureInputBuilder(Url, 'POST', data,publicKey,privateKey)
      api_call = doRequest(newUrl, 'POST', data)
      return api_call

    elif(requestType == "PUT"):
      newUrl = signatureInputBuilder(Url, 'PUT', data,publicKey,privateKey)
      api_call = doRequest(newUrl, 'PUT', data)
      return api_call

    elif(requestType == "DELETE"):
      newUrl = signatureInputBuilder(Url, 'DELETE', None,publicKey,privateKey)
      api_call = doRequest(newUrl, 'DELETE', None)
      return api_call          

  # FUNCTION : Signature Builder
  def signatureInputBuilder(url, method, data,publicKey,bksecretkey):

      #print "\nSIGNATUREINPUTBUILDER : signatureInputBuilder() started\n"
      stringToSign = method
      parsedUrl = urlparse.urlparse(url)
      #print parsedUrl
      stringToSign += parsedUrl.path
      
      # splitting the query into array of parameters separated by the '&' character
      #print parsedUrl.query
      qP = parsedUrl.query.split('&')
      #print qP

      if len(qP) > 0:
          for  qS in qP:
              qP2 = qS.split('=')
              #print qP2
              if len(qP2) > 1:
                  stringToSign += qP2[1]
      
      #print stringToSign
      if data != None :
          stringToSign += data 
      #print "\nString to be Signed:\n" + stringToSign
      
      h = hmac.new(str(bksecretkey), str(stringToSign), hashlib.sha256)

      s = base64.standard_b64encode(h.digest())
      #print "\nRaw Method Signature:\n" + s 
      
      u = urllib.quote_plus(s)
      #print "\nURL Encoded Method Signature (bksig):\n" + u

      newUrl = url 
      if url.find('?') == -1 :
          newUrl += '?'
      else:
          newUrl += '&'
          
      newUrl += 'bkuid=' + publicKey + '&bksig=' + u 

      return newUrl

  # FUNCTION : apiCall
  def doRequest(url, method, data):

      #print "\nDOREQUEST : doRequest() started"
      headers = {"Accept":"application/json","Content-type":"application/json","User_Agent":"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.1) Gecko/20090624 Firefox/3.5"}
      try:
          cJ = cookielib.CookieJar()
          request = None
          if method == 'PUT': 
              request = urllib2.Request(url, data, headers)
              request.get_method = lambda: 'PUT'
          elif  method == 'DELETE' :
              request = urllib2.Request(url, data, headers)
              request.get_method = lambda: 'DELETE'
          elif data != None :
              request = urllib2.Request(url, data, headers)
          else:
              request = urllib2.Request(url, None, headers)  
              opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cJ))
              
              u = opener.open(request)
              rawData = u.read()
              #print "\nResponse Code: 200"
              #print "\nAPI Response:\n" + rawData + "\n"
              #apiResponseParser(rawData,None)
              return rawData

      except urllib2.HTTPError, e:
          print "\nHTTP error: %d %s" % (e.code, str(e)) 
          print "ERROR: ", e.read()
          return None
      except urllib2.URLError, e:
          print "Network error: %s" % e.reason.args[1]
          print "ERROR: ", e.read()
          return None

  # 1 RETURN AUDIENCE LIST AND GET LIST OF IDS

  this_request["notes"].append("AUDIENCE GRAB : Grabbing audiences")
  writeToMem(requestID,this_request)  

  # 1a Call Audiences API to get list of audiences
  print "\nAUDIENCE GRAB : grabbing audiences"
  urlRequest = "http://services.bluekai.com/Services/WS/audiences"
  all_audiences = apiCall(urlRequest,"GET",None,publicKey,privateKey)
  print "AUDIENCE GRAB : audiences should be returned"

  this_request["notes"].append("AUDIENCE GRAB : Audiences found")
  writeToMem(requestID,this_request)  
  
  # 1b Loop through returned audience list, grab Audience IDs and put in list
  this_request["notes"].append("AUDIENCE PARSE : Getting list of all audience IDs and Names")
  writeToMem(requestID,this_request)

  print "\nAUDIENCE PARSE : getting list of all audience IDs"
  audiences = {}
  all_audiences = json.loads(all_audiences)

  for audience in all_audiences["audiences"]:
    audiences[str(audience["id"]).strip()] = audience["name"].strip()

  audience_count = str(len(audiences))

  this_request["notes"].append("AUDIENCE PARSE : " + audience_count + " audiences returned")
  writeToMem(requestID,this_request)

  print "\nAUDIENCE PARSE : List of IDs returned (see below)\n"
  #print audience_ids

  this_request["notes"].append("AUDIENCE PARSE : All audiences parsed and names/IDs noted")
  this_request["audiences"] = {}

  for audienceid in audiences:
    this_request["audiences"][audienceid] = {"Reach":"In Progress...","Name":audiences[audienceid]}
    

  print "\nAUDIENCE PARSE : Audience ID object completed (see below)\n"
  #print this_request["audiences"]

  writeToMem(requestID,this_request)

  # 2 LOOP THROUGH EACH AUDIENCE AND GRAB INVENTORY
  print "\nAUDIENCE REACH : Checking each audience for reach\n"  
  #print audience_ids

  # Thread locking
  global lock
  lock = threading.Lock()

  for eachaudience in audiences:
      
    eachaudience = str(eachaudience).strip()
    print "AUDIENCE REACH : About to start thread for audience ID=" + eachaudience        
    audienceThreads = threading.Thread(target=audienceReachGrab, args=(requestID,eachaudience,publicKey,privateKey))
    audienceThreads.start()       

            
  #this_request["notes"].append("job completed")
  #writeToMem(requestID,this_request)


def requestIdGenerator():

  print "\nGLOBAL : requestIdGenerator() called"
  global requestIdCounter

  if "requestIdCounter" not in globals():
    requestIdCounter = "0"

  requestIdCounter = int(requestIdCounter) + 1
  requestIdCounter = str(requestIdCounter)

  print "\nGLOBAL : Generated Request ID = ",requestIdCounter

  return requestIdCounter  

def writeToMem(requestID,data):

  print "\nGLOBAL : writeToMem() called"
  global all_requests

  # if 'all_requests' does not exist in globals() : add it
  if "all_requests" not in globals():

    all_requests = {}

    print "'\nall_requests' not found in globals() : created (see below)\n"
    #print all_requests

  # Adding request into 'all_requests'
  print "\nUpdating 'all_requests' with request " + requestID +  " = " + str(data) + " see below:\n"
  #print data  

  all_requests[requestID] = data

def readFromMem(requestID):

  #print "GLOBAL : readFromMem() called"
  global all_requests

  # if 'all_requests' not found in globals() then return
  if "all_requests" not in globals():

    #print "No requests found"
    return "No requests found"
    
  else:

    # if 'all_requests' exists in globals() : add request
    if requestID in all_requests:
      #print  "'all_requests' : found request = " + requestID
      #print all_requests[requestID]
      return all_requests[requestID]

    else:

      #print "\nRequest not found in 'all_requests' : returning"
      return "No requests found"
    
def clearFromMem(requestID):

  print "\nGLOBAL : clearFromMem() called"
  global all_requests

  if "all_requests" not in globals():

    print "No requests found"
    return "No requests found"
    
  else:
  
    print "\nGLOBAL : Deleting requestID=" + requestID + " from 'all_requests' object"
    del all_requests[requestID]            

def clearAllMem():

  print "\nGLOBAL : clearAllMem() called"
  global all_requests

  if "all_requests" not in globals():

    print "No requests found"
    return "No requests found"
      
  else:

    all_requests = {}

    print "\nClearing 'all_requests'"    
    
def audienceReachCheck(requestID):

  #print "\nAUDIENCE REACH CHECK : audienceReachCheck() started"
  #print "requestID = " + requestID
  #print ""  

  #Check Pickle for request
  request_data = readFromMem(requestID)
  
  # If no data yet : return 'not completed'
  if request_data == "No requests found":

    #print "\nAUDIENCE REACH CHECK : audienceReachCheck(",requestID,") : no data found in 'all_requests' : returning {'status':'not competed'}"
    data = {"status":"not completed - no requests found yet", "id" : requestID}
    
    return json.dumps(data)

  # If data : return data (and remove from 'all_requests' if 'completed')
  else:
    
    #print "\nAUDIENCE REACH CHECK : audienceReachCheck(",requestID,") : data found in 'all_requests' : see returned below:"
    #print request_data
    print ""

    # Remove from mem if request completed    
    if request_data["status"] == "completed":
      
      #print "\nAUDIENCE REACH CHECK : audienceReachCheck(",requestID,") : removing request from 'all_requests' as no longer required"

      clearFromMem(requestID)
      return json.dumps(request_data)

    if request_data["status"] == "not completed":

      #print "\nAUDIENCE REACH CHECK : audienceReachCheck(",requestID,") : status is 'not completed'"
      #print json.dumps(request_data)
                  
      return json.dumps(request_data)
    
    else:
      
      # return requst data back
      return request_data



