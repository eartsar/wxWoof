import sys, os, errno, socket, getopt, commands, tempfile
import cgi, urllib, BaseHTTPServer
from SocketServer import ThreadingMixIn
import ConfigParser
import shutil, tarfile, zipfile
import struct

maxdownloads = 1
TM = object
compressed = 'gz'
upload = False

def find_ip ():
    
    candidates = []
    for test_ip in ["192.0.2.0", "198.51.100.0", "203.0.113.0"]:
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.connect ((test_ip, 80))
        ip_addr = s.getsockname ()[0]
        s.close ()
        if ip_addr in candidates:
            return ip_addr
        candidates.append (ip_addr)
    
    return candidates[0]

    
class FileServHTTPRequestHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "Simons FileServer"
    protocol_version = "HTTP/1.0"
    filename = "."
    
    def log_request (self, code='-', size='-'):
        if code == 200:
            BaseHTTPServer.BaseHTTPRequestHandler.log_request (self, code, size)
    
    
    def do_POST (self):
        global maxdownloads, upload
        
        if not upload:
            self.send_error (501, "Unsupported method (POST)")
            return
        
        maxdownloads -= 1
        
        if maxdownloads < 1:
            httpd.shutdown()
      
      # taken from
      # http://mail.python.org/pipermail/python-list/2006-September/402441.html
      
        ctype, pdict = cgi.parse_header (self.headers.getheader ('Content-Type'))
        form = cgi.FieldStorage (
                        fp = self.rfile,
                        headers = self.headers,
                        environ = {'REQUEST_METHOD' : 'POST'},
                        keep_blank_values = 1,
                        strict_parsing = 1)
         
        if not form.has_key ("upfile"):
            self.send_error (403, "No upload provided")
            return
      
        upfile = form["upfile"]
      
        if not upfile.file or not upfile.filename:
            self.send_error (403, "No upload provided")
            return
        
        upfilename = upfile.filename
      
        if "\\" in upfilename:
            upfilename = upfilename.split ("\\")[-1] 
            upfilename = os.path.basename (upfile.filename)
            destfile = None
        
        for suffix in ["", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9"]:
            destfilename = os.path.join (".", upfilename + suffix)
            try:
                destfile = os.open (
                    destfilename,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0644)
                
                break
            except OSError, e:
                if e.errno == errno.EEXIST:
                    continue
                raise
        
        if not destfile:
            upfilename += "."
            destfile, destfilename = tempfile.mkstemp (prefix = upfilename, dir = ".")
        
        print >>sys.stderr, "accepting uploaded file: %s -> %s" % (upfilename, destfilename)
        
        shutil.copyfileobj (upfile.file, os.fdopen (destfile, "w"))
        
        if upfile.done == -1:
            self.send_error (408, "upload interrupted")
        
        txt = """\
                <html>
                  <head><title>Woof Upload</title></head>
                  <body>
                    <h1>Woof Upload complete</title></h1>
                    <p>Thanks a lot!</p>
                  </body>
                </html>
              """
        self.send_response (200)
        self.send_header ("Content-Type", "text/html")
        self.send_header ("Content-Length", str (len (txt)))
        self.end_headers ()
        self.wfile.write (txt)
        
        return
    
   
    def do_GET (self):
        global maxdownloads, compressed, upload
        
        # Form for uploading a file
        if upload:
            txt = """\
                 <html>
                   <head><title>Woof Upload</title></head>
                   <body>
                     <h1>Woof Upload</title></h1>
                     <form name="upload" method="POST" enctype="multipart/form-data">
                       <p><input type="file" name="upfile" /></p>
                       <p><input type="submit" value="Upload!" /></p>
                     </form>
                   </body>
                 </html>
               """
            self.send_response (200)
            self.send_header ("Content-Type", "text/html")
            self.send_header ("Content-Length", str (len (txt)))
            self.end_headers ()
            self.wfile.write (txt)
            return
        
        # Redirect any request to the filename of the file to serve.
        # This hands over the filename to the client.
        
        self.path = urllib.quote (urllib.unquote (self.path))
        location = "/" + urllib.quote (os.path.basename (self.filename))
        if os.path.isdir (self.filename):
            if compressed == 'gz':
                location += ".tar.gz"
            elif compressed == 'bz2':
                location += ".tar.bz2"
            elif compressed == 'zip':
                location += ".zip"
            else:
                location += ".tar"
            
        if self.path != location:
            txt = """\
                <html>
                   <head><title>302 Found</title></head>
                   <body>302 Found <a href="%s">here</a>.</body>
                </html>\n""" % location
            self.send_response (302)
            self.send_header ("Location", location)
            self.send_header ("Content-Type", "text/html")
            self.send_header ("Content-Length", str (len (txt)))
            self.end_headers ()
            self.wfile.write (txt)
            return
        
        maxdownloads -= 1
        
        if maxdownloads < 1:
            httpd.shutdown()
        
        type = None
        
        if os.path.isfile (self.filename):
            type = "file"
        elif os.path.isdir (self.filename):
            type = "dir"
        
        if not type:
            print >> sys.stderr, "can only serve files or directories. Aborting."
            sys.exit (1)
        
        self.send_response (200)
        self.send_header ("Content-Type", "application/octet-stream")
        if os.path.isfile (self.filename):
            self.send_header ("Content-Length", os.path.getsize (self.filename))
        self.end_headers ()
        
        try:
            if type == "file":
                datafile = file (self.filename)
                shutil.copyfileobj (datafile, self.wfile)
                datafile.close ()
            elif type == "dir":
                if compressed == 'zip':
                    ezfile = EvilZipStreamWrapper (self.wfile)
                    zfile = zipfile.ZipFile (ezfile, 'w', zipfile.ZIP_DEFLATED)
                    stripoff = os.path.dirname (self.filename) + os.sep
                    
                    for root, dirs, files in os.walk (self.filename):
                        for f in files:
                            filename = os.path.join (root, f)
                            if filename[:len (stripoff)] != stripoff:
                                raise RuntimeException, "invalid filename assumptions, please report!"
                            zfile.write (filename, filename[len (stripoff):])
                    zfile.close ()
                else:
                    tfile = tarfile.open (mode=('w|' + compressed), fileobj=self.wfile)
                    tfile.add (self.filename,
                        arcname=os.path.basename(self.filename))
                    tfile.close ()
        except Exception, e:
            print e
            print >>sys.stderr, "Connection broke. Aborting"
    


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
   """Handle requests in a separate thread"""


def serve_files (filename, maxdown = 1, ip_addr = '', port = 8080):
    global maxdownloads, httpd
    
    maxdownloads = maxdown
    
    # We have to somehow push the filename of the file to serve to the
    # class handling the requests. This is an evil way to do this...
    
    FileServHTTPRequestHandler.filename = filename
    
    try:
        httpd = ThreadedHTTPServer ((ip_addr, port), FileServHTTPRequestHandler)
    except socket.error as e:
        print >>sys.stderr, "cannot bind to IP address '%s' port %d" % (ip_addr, port)
        print >>sys.stderr, str(e)
        sys.exit (1)
    except Exception as e:
        print "Something unbelievable happened."
        print str(e)
        sys.exit(2)
    
    if not ip_addr:
        ip_addr = find_ip ()
    if ip_addr:
        print "Now serving on http://%s:%s/" % (ip_addr, httpd.server_port)
    
    httpd.serve_forever ()
    return True


def launch (filename):
    global cpid, upload, compressed
    
    maxdown = 1
    port = 8080
    ip_addr = ''
    
    defaultport = port
    defaultmaxdown = maxdown
    retcode = serve_files (filename, maxdown, ip_addr, port)
    return retcode


