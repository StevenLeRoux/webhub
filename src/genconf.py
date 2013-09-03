#!/usr/bin/python
#
# @(#)$Id: genconf.py,v 1.55 2009/11/12 10:44:34 Exp $
#
# (c) 2007 hbs
#   2009 slr
#   2010 slr
#   2013 slr

import os
import sys
import re
import time
try:
  import json
  have_json=True
except:
  have_json=False

if not have_json:
  print
  print "You need to add json libs"
  print
  print "apt-get install python-json"
  print
  exit(1)

###
### Version information
###

version = "$Revision: 1.55 $"
cfversion = ""
gents = time.time()
env = sys.argv[1]

###
### Fowler Noll Vo 1a 64 bits
###

def FNV1a(data):
  seed = 0xcbf29ce484222325L

  for c in data:
    seed ^= ord(c)
    seed *= 0x100000001b3L
    seed &= 0xffffffffffffffffL

  return "%016x" % seed

##
## This script is in charge of generating the HAProxy configurations for the internal reverse proxy layer.
##
## It takes as input a file with lines defining the Apache and Tomcat hosting conf of different services
##
## Several kinds of lines exist:
##
## * Apache host definition
##
##   aphost <NAME> <POOL>
##
## * Apache service definition
##
##   apsvc <NAME> <IP> <APHOST>
##
## * Tomcat host definition
##
##   tchost <NAME> <POOL>
##
## * Tomcat service definition
##
##   tcsvc <NAME> <IP> <TCHOST>
##
## * Apache hosting line
##
##   ap <SITE>-<PORT> http://<APSVC>:<APPORT>/
##
## * Tomcat hosting line
##
##   tc <SITE>-<PORT> http://<TCROUTE>@<TCSVC>:<TCPORT>/<TCCONTEXT> <LBFACTOR>
##
## SITE ::= site for which we are defining the configuration (for example www.cmb.fr)
## PORT ::= external port used for the service, will be used when creating the conf files (e.g. 80)
##    this is not the port the Apache service will listen on
## APSVC::= Apache service (IP) to bind to, the valid apsvc are of the form 'ap-#', they must be
##    declared in this script first
## APPORT::= Port the Apache service will listen on, can be either 8080 or 8443
## TCROUTE::= Tomcat 'jvmRoute' associated with the Tomcat hosting configuration
## TCSVC::= Tomcat service, the IP Tomcat will listen on
## TCPORT::= Tomcat service port, the port Tomcat will listen on, should be >= 40000 <= 49999
##     a single Tomcat application uses the same port on all TCSVC
## TCCONTEXT::= The deployment context of the application
##
## TCLBFACTOR::= LoadFactor 
##
## The script creates a directory hierarchy


 
#
# List of valid apsvc (Apache services) with associated aphost (Apache host)
#

aphost = {}

#
# List of generic apsvc (Apache services) with associated aphost (Apache host)
#

apgensvc = {}
aphostgensvc = {}

#
#
# Disabled aphosts
#

disabledaphosts = []

#
# Pool the different aphosts belong to
#

appool = {}

#
# Address list of aphost for peers 
#

aphipbyhost = {}

#
# List of valid tcsvc (Tomcat services) with associated tchost (Tomcat host)
#

#tchost = {}

#
# Pools the different tchost belong to
#

tcpool = {}

#
# IP address of apsvc
#

apsvcip = {}

#
# IP address of tcsvc
#

tcsvcip = {}
  
#apre = re.compile(r"^([^\s]+)\s+(80|443|8080|8443)\s+(http://([a-z0-9\.-]+):(8080|8443)/)\s*(#.*)?$")
#tcre = re.compile(r"^([^\s]+)\s+(80|443|8080|8443)\s+(http://([a-z0-9-]+)@([a-z0-9\.-]+):([0-9]{4,5})/([a-z0-9-]*))\s*(#.*)?$")

apre =   re.compile(r"^apache\s+([^\s]+)-(80|443|8080|8443)\s+(http://(ap-[0-9]+):(8080|8443)/)\s*(#.*)?$")
tcre =   re.compile(r"^tomcat\s+([^\s]+)-(80|443|8080|8443)\s+(http://([a-z0-9-]+)@(tc-[0-9]+):(4[0-9]{4})(/[a-zA-Z0-9./-]*))(\s+([1-9]|[1-9][0-9]|100))*\s*(#.*)?$")
aphostre =   re.compile(r"^apachehost\s+(aphost-[0-9]+)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([a-z0-9\.-]+)\s*(OFF)?\s*(#.*)?$")
#tchostre =   re.compile(r"^tomcathost\s+(tchost-[0-9]+)\s+([a-z0-9.-]+)\s*(#.*)?$")
apgensvcre =  re.compile(r"^apachegeneric\s+(ap-[0-9]+)\s+(aphost-[0-9]+)\s*(#.*)?$")
apsvcre =  re.compile(r"^apacheservice\s+(ap-[0-9]+)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+(aphost-[0-9]+)\s*(#.*)?$")
tcsvcre =  re.compile(r"^tomcatservice\s+(tc-[0-9]+)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([a-z0-9\.-]+)\s*(#.*)?$")
aliasre =  re.compile(r"^alias\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
compre =   re.compile(r"^compress\s+([^\s]+)-(80|443|8080|8443)((\s+(text|application)[^\s]+)+)(\s+(iesucks))?\s*(#.*)?$")
nofailoverre = re.compile(r"^nofailover\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
hostportre = re.compile(r"^hostport\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
setcookiere = re.compile(r"^setcookie\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
pxysrcaddrre = re.compile(r"^pxysrcaddr\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
xdomainre = re.compile(r"^xdomain\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
forensicre = re.compile(r"^forensic\s+([^\s]+)-(80|443|8080|8443)\s*(#.*)?$")
balancertore = re.compile(r"^balancerto\s+([^\s]+)-(80|443|8080|8443)\s+([0-9]+)\s*(#.*)?$")
backendtore = re.compile(r"^backendto\s+([^\s]+)-(80|443|8080|8443)\s+([0-9]+)\s*(#.*)?$")
expirere =   re.compile(r"^expire\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s+\"([^\"]+)\"\s*(#.*)?$")
cachere =  re.compile(r"^cache\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\"]+)\"\s+(public|private|no-cache)\s*([0-9]+)?\s*(#.*)?$")
nocachere =  re.compile(r"^nocache\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
logheaderre =re.compile(r"^logheader\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s*(#.*)?$")
redirectre = re.compile(r"^redirect\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\s]+)\"\s+\"([^\"]+)\"(\s+\"([^\"]+):([^\"]+)\")?\s*(#.*)?$")
rewritere =  re.compile(r"^rewrite\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\s]+)\"\s+\"([^\"]+)\"\s*(#.*)?$")
commentre =  re.compile(r"^\s*(#.*)?$")
versionre =  re.compile(r"^version\s+(.*)\s*$")

#
# Apache hosts associated with each site - Each can only be associated once with a given site
#

apsvcsbysite = {}

#
# Apache port by site
#

apportbysite = {}

#
# Tomcat contexts associated with each site - Must be the same for all Tomcat instances for this site
#
tccontextbysite = {}

#
# Tomcat port associated with each site - Must be the same for all Tomcat instances for this site
#
tcportbysite = {}

#
# Tomcat jvmroutes associated with each site - A jvmroute can only be associated with one instance for the site
#
tcroutesbysite = {}

#
# Tomcat services associated with each site - Each can only be associated once with a given site
#
tcsvcsbysite = {}

#
# Tomcat check associated with each site.
#
tccheckbysite = {}

#
# Tomcat routes associated with each tcsvc:tcport
#
tcroutebytc = {}

#
# Tomcat loadfactor associated with each tcsvc:tcport
#
tclbfactorbytc = {}

#
# Tomcat loadfactor associated with each site
#
#tclbfactorbysite = {}

#
# Sites by apsvc:apport
#
sitebyap = {}

#
# sites by tcsvc:tcport
#
sitebytc = {}

#
# sites by apsvc
#
sitemap = {}

#
# Server name by site
#
servernamebysite = {}

#
# Forensic logging by site
#
forensiclogbysite = {}

#
# MIME types to compress by site
#
compressbysite = {}

#
# ServerAlias by site
#
aliasbysite = {}

#
# Proxy Source Address by site
#
pxysrcaddrbysite = {}

#
# Cross Domain Access-Control-Allow-Origin by site
#
xdomainbysite = {}

#
# Disable compression if sucking browser
#
iesucksbysite = {}

#
# nofailover by site
#
nofailoverbysite = {}

#
# hostport by site
#
hostportbysite = {}

#
# setcookie by site
#
setcookiebysite = {}

#
# Expire specifications by site
#
expiresbysite = {}

#
# Cacheable content by site
#
cacheablebysite = {}

#
# Log headers by site
#
logheadersbysite = {}

#
# Redirections by site
#
redirectsbysite = {}

#
# Rewrite rules by site
#
rewritesbysite = {}

#
# Backend timeout by site
#
backendtobysite = {}
DEFAULT_BACKEND_TO = 30

#
# Balancer timeout by site
#
balancertobysite = {}
DEFAULT_BALANCER_TO = 0

#
# Default Connect timeout (in ms)
#
DEFAULT_CONNECT_TO = 5000

#
# collect frontend ids
#
fidlist = []

lineno = 0
error=False

for line in sys.stdin:
  lineno += 1

  line = line.strip()
  
  m = aphostre.search(line)
  if m:
    aph = m.group(1).lower()
    app = m.group(2)
  
    if appool.has_key(aph):
      print >> sys.stderr, lineno,"ERROR","aphost=",aph,"is already defined."
      error = True
    else:
      appool[aph] = app

    if aphipbyhost.has_key(aph):
      print >> sys.stderr, lineno,"ERROR","aphost=",aph,"already has an IP defined."
      error = True
    else:
      aphipbyhost[aph] = aphip
    
  #
  # Append the aphost to the list of disabled aphosts if 'disabled' was specified
  #
  
    if m.group(3) == "OFF":
      disabledaphosts.append(aph)
    
    continue

  m = apgensvcre.search(line)
  if m:
    aps = m.group(1)
    aph = m.group(2).lower()
  
    if apgensvc.has_key(aps):
      print >> sys.stderr, lineno,"ERROR","apgensvc=",aps,"is already defined."
      error = True
    else:
      if not aphostgensvc.has_key(aph):
        aphostgensvc[aph] = []
      aphostgensvc[aph].append(aps)
      apgensvc[aps] = aph
    
    continue

  m = apsvcre.search(line)
  if m:
    aps = m.group(1).lower()
    apip = m.group(2)
    aph = m.group(3).lower()
      
    if aphost.has_key(aps):
      print >> sys.stderr, lineno,"ERROR","apsvc=",aps,"is already defined."
      error = True
    else:
      if apip in apsvcip.values():
        print >> sys.stderr, lineno,"ERROR","apsvc=",aps,"defines IP address",apip,"which is already assigned."
        error = True
      else:
        aphost[aps] = aph
        apsvcip[aps] = apip
  
    continue

  m = tcsvcre.search(line)
  if m:
    tcs = m.group(1).lower()
    tcip = m.group(2)
    tcp = m.group(3).lower()
      
    # FIXME, check tcpool
    if tcpool.has_key(tcs):
      print >> sys.stderr, lineno,"ERROR","tcsvc=",tcs,"is already defined."
      error = True
    else:
      if tcip in tcsvcip.values():
        print >> sys.stderr, lineno,"ERROR","tcsvc=",tcs,"defines IP address",tcip,"which is already assigned."
        error = True
      else:
        tcpool[tcs] = tcp
        tcsvcip[tcs] = tcip
    
    continue
  
  m = compre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    compressbysite[k] = m.group(3)
    if m.group(7):
      iesucksbysite[k] = m.group(7)
  	
  
    continue

  m = aliasre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    aliasbysite[k] = m.group(3)
  
    continue

  m = pxysrcaddrre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    pxysrcaddr = m.group(3)
  
    if not pxysrcaddrbysite.has_key(k) and pxysrcaddr == 'on':
      pxysrcaddrbysite[k] = pxysrcaddr
  
    continue

  m = xdomainre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    xdomainbysite[k] = m.group(3)
  
    continue


  m = nofailoverre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    nofailover = m.group(3)
  
    if not nofailoverbysite.has_key(k):
      nofailoverbysite[k] = nofailover
  	
    continue

  m = hostportre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    hostport = m.group(3)
  
    if not hostportbysite.has_key(k) and hostport == "on":
      hostportbysite[k] = hostport
  	
    continue

  m = setcookiere.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
  
    k = site + "-" + port
  
    setcookie = m.group(3)
  
    if not setcookiebysite.has_key(k) and setcookie == "off":
      setcookiebysite[k] = setcookie
  	
    continue


  m = forensicre.search(line)
  if m:
    forensiclogbysite[m.group(1).lower() + "-" + m.group(2)] = True
    continue  
  
  m = apre.search(line)
  if m:  
    site = m.group(1).lower()
    port = m.group(2)
    
    k = site + "-" + port
  
    servernamebysite[k] = site
    
    apsvc = m.group(4).lower()
    apport = m.group(5)
    
    ap = apsvc + ":" + apport
    
    #print "site=",site,"port=",port,"apsvc=",apsvc,"apport=",apport
    if not apsvc in apgensvc.keys():
      if sitebyap.has_key(ap):
        print >> sys.stderr, lineno,"ERROR","apsvc",apsvc,"apport=",apport,"already assigned to site",sitebyap[ap]
        error=True
      else:
        sitebyap[ap] = k
     
    if not apsvcsbysite.has_key(k):
      apsvcsbysite[k] = []
      
    if apsvc in apsvcsbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines apsvc=",apsvc,"several times"
      error=True
    else:
      apsvcsbysite[k].append(apsvc)
  
    #
    # Check that apsvc is known
    #
    
    if not aphost.has_key(apsvc):
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines apsvc=",apsvc,"which is not known"
      error=True
      
    #
    # Check Apache service Port
    #
      
    if not apportbysite.has_key(k):
      apportbysite[k] = apport
      
    if not sitemap.has_key(apsvc):
      sitemap[apsvc] = {}
    if not sitemap[apsvc].has_key(apport):
      sitemap[apsvc][apport] = []
    sitemap[apsvc][apport].append(k)
      
    if apport != apportbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines apport=",apport,"when apport should be",apportbysite[k]
  
    continue
  
  m = tcre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
      
    tcroute = m.group(4)
    tcsvc = m.group(5).lower()      
    tcport = m.group(6)
    tccheck = m.group(7)
    tc = tcsvc + ":" + tcport
    tclbfactor = m.group(9)
  
    m = re.search(r"^(/[^/]+)?(/.*)$", tccheck)
    if m:
      tccontext = m.group(1)
      #tccheck = m.group(2)
      
      if tccontext == None:
        tccontext = "/"
    else:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"both context and check MUST be defined."
      error = True
          
    #print "site=",site,"port=",port,"tcroute=",tcroute,"tcsvc=",tcsvc,"tcport=",tcport,"tccontext=",tccontext,"tccheck=",tccheck
      
    if sitebytc.has_key(tc):
      print >> sys.stderr, lineno,"WARNING","tcsvc",tcsvc,"tcport=",tcport,"already assigned to site",sitebytc[tc]
      #error=True
    else:
      sitebytc[tc] = k
  
    #
    # Check Tomcat Host
    #
      
    if not tcsvcsbysite.has_key(k):
      tcsvcsbysite[k] = []
      
    if tcsvc in tcsvcsbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcsvc=",tcsvc,"several times"
      error=True
    else:
      tcsvcsbysite[k].append(tcsvc)
      
    #
    # Check Tomcat Route
    #
      
    if not tcroutesbysite.has_key(k):
      tcroutesbysite[k] = []
    if tcroute in tcroutesbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcroute=",tcroute,"several times"
      error=True
    else:
      tcroutesbysite[k].append(tcroute)
       
    # A tcsvc:tcport is being reused, issue a warning or an error if the route differs
    if tcroutebytc.has_key(tc):
      if tcroutebytc[tc] != tcroute:
        print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcsvc=",tcsvc,"tcport=",tcport,"with route=",tcroute,"when it is already defined with route=",tcroutebytc[tc]
        error=True
      else:
        print >> sys.stderr, lineno,"WARNING","site=",site,"port=",port,"defines tcsvc=",tcsvc,"tcport=",tcport,"which is already defined"
    else:
      tcroutebytc[tc] = tcroute
          
    #
    # Check Tomcat Context
    #
      
    if not tccontextbysite.has_key(k):
      tccontextbysite[k] = tccontext
      
    if tccontext != tccontextbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tccontext=",tccontext,"when tccontext should be",tccontextbysite[k]
  
    #
    # Check Tomcat Port
    #
      
    if not tcportbysite.has_key(k):
      tcportbysite[k] = tcport
      
    if tcport != tcportbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcport=",tcport,"when tcport should be",tcportbysite[k]
  
    #
    # Check Tomcat Check
    #
      
    if not tccheckbysite.has_key(k):
      tccheckbysite[k] = tccheck
      
    if tccheck != tccheckbysite[k]:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tccheck=",tccheck,"when tccheck should be",tccheckbysite[k]
      error = True
    
  
    #
    # Set Tomcat LoadFactor
    #
      
    if not tclbfactor is None and not tclbfactorbytc.has_key(tc):
      tclbfactorbytc[tc] = tclbfactor
    
    #
    # Check that Tomcat host is known
    #
      
  #  if not tchost.has_key(tcsvc):
  #    print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcsvc=",tcsvc,"which is not known"
  #    error=True
  
  
    continue

  m = expirere.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
  
    expirematch = m.group(3)
    expiretime = m.group(4)
    
    # Define an empty array if it is not yet initialized
    # We need an array as the order of location match MUST be preserved
    # @see: http://httpd.apache.org/docs/2.2/sections.html#mergin
    
    if not expiresbysite.has_key(k):
      expiresbysite[k] = []
      
    expiresbysite[k].append({ 'match':expirematch, 'expire':expiretime })
    
    continue
  
  m = cachere.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
  
    cachematch = m.group(3)
    cachetype = m.group(4)
    cachemaxage = m.group(5)
    
    if not cacheablebysite.has_key(k):
      cacheablebysite[k] = []
      
    cacheablebysite[k].append({'match':cachematch,'type':cachetype,'maxage':cachemaxage})
    
    continue
  
  m = logheaderre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
  
    logheader = m.group(3).lower()
      
    if not logheadersbysite.has_key(k):
      logheadersbysite[k] = []
      
    logheadersbysite[k].append(logheader)  
    
    if logheader == "server":
      print >> sys.stderr,"WARNING header Server is not correctly logged, you may reconsider logging it."
      
    continue
  
  m = redirectre.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
  
    match = m.group(3)
    target = m.group(4)
    if m.group(5):
      condtype = m.group(6)
      cond = m.group(7)
    
    # Initialize an array (we need to keep the redirects in the order they were defined in)
    if not redirectsbysite.has_key(k):
      redirectsbysite[k] = []
  
    if not m.group(6):
      redirectsbysite[k].append({'match':match,'target':target})
    else:
      redirectsbysite[k].append({'condtype':condtype,'cond':cond,'match':match,'target':target})
    
    continue


  m = rewritere.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
      
    k = site + "-" + port
  
    match = m.group(3)
    target = m.group(4)
    
    # Initialize an array (we need to keep the rewrites in the order they were defined in)
    if not rewritesbysite.has_key(k):
      rewritesbysite[k] = []
      
    rewritesbysite[k].append({'match':match,'target':target})
    
    continue
  
  
  m = versionre.search(line)
  if m:
    if cfversion != "":
      print >> sys.stderr,lineno,"ERROR version already defined."
      error=True
      
    cfversion = m.group(1)
    continue
 
  #
  # Balancer timeout
  # Time to wait for a backend connection to become available
  # Should not be more than 5 seconds
  #
  
  m = balancertore.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
    to = int(m.group(3))
    
    k = site + "-" + port
  
    if balancertobysite.has_key(k):
      print >> sys.stderr,lineno,"WARNING previous value for balancer timeout existed (%s), overriding." % balancertobysite[k]    
  
    balancertobysite[k] = to
    continue

  #
  # Backend timeout
  # Time to wait for a response from a backend
  # The value depends on the expected performance of the backend
  #
  
  m = backendtore.search(line)
  if m:
    site = m.group(1).lower()
    port = m.group(2)
    to = int(m.group(3))
    
    k = site + "-" + port
  
    if backendtobysite.has_key(k):
      print >> sys.stderr,lineno,"WARNING previous value for backend timeout existed (%s), overriding." % backendtobysite[k]    
  
    backendtobysite[k] = to
    continue
  
  if commentre.search(line):
    continue
  
  # Anything else is an error
  print >> sys.stderr, lineno, "ERROR, invalid syntax on line: %s" % line
  error = True
  
#
# Check that each site has at least one tcsvc and one apsvc
#

sites = []
sites.extend(apsvcsbysite.keys())
sites.extend(tcsvcsbysite.keys())

for site in set(sites):  
  if not apsvcsbysite.has_key(site):
    print >> sys.stderr, "ERROR","site=",site,"does not define any apsvc"
    error=True
  
  if not tcsvcsbysite.has_key(site):
    print >> sys.stderr, "ERROR","site=",site,"does not define any tcsvc"
    error=True
      
#
# Loop through the sites
#
tcnok = 0

for site in set(sites):
  #print site
  appools = []
  tcpools = []
  aphosts = []
#  tchosts = []
  gen = 0

  # Check that a site is assigned to several pools, if not emit a WARNING
  for apsvc in apsvcsbysite[site]:
    #print "  ",apsvc
    aphosts.append(aphost[apsvc])
    appools.append(appool[aphost[apsvc]])
    if apsvc in apgensvc.keys():
      gen = 1
  
  for tcsvc in tcsvcsbysite[site]:  
    #print "  ",tcsvc
#   tchosts.append(tchost[tcsvc])
    tcpools.append(tcpool[tcsvc])
  if env in ( "sample-env" , "production" ):
    if len(set(appools)) < 2:
      print >> sys.stderr, "WARNING, site=",site,"is assigned to only one Apache pool."
  if len(set(tcpools)) < 2:
    if env in ( "sample-env" , "production" ):
      print >> sys.stderr, "WARNING, site=",site,"is assigned to only one Tomcat pool."
    tcnok += 1

  if not gen == 1:
    if len(set(aphosts)) != len(aphosts):
      print >> sys.stderr, "ERROR, site=",site,"is assigned several times to the same aphost (Apache host)."
      error = True

  #
  # Check that the service is assigned to at least one aphost that is not disabled
  #
  
  validaphost = False
  
  for aph in aphosts:
    if aph not in disabledaphosts:
      validaphost = True
      break
  
  if not validaphost:
    print >> sys.stderr, "WARNING, site=",site,"is only assigned to Apache hosts that are OFF, it will therefore not be accessible."   


# if any site has only one TC pool, generate a stats chart
if tcnok != 0:
  tcok = len(set(sites)) - tcnok
  ptcok = tcok * 100 / len(set(sites))
  ptcnok = tcnok * 100 / len(set(sites))
  stats = open("tcnok.html","w")
  stats.write("<html><body>")
  stats.write("<img src=\"http://chart.apis.google.com/chart?cht=p&chs=550x200&chd=t:" + str(ptcnok) + "," + str(ptcok) + "&chl=Only%20One%20Tomcat%20(" + str(tcnok) + ")|Ok%20(" + str(tcok) + ")\">")
  stats.write("</body></html>\n")
  stats.close()
else:
  stats = open("tcnok.html","w")
  stats.write("<html><body>")
  stats.write("TC 100% OK")
  stats.write("</body></html>\n")
  stats.close()

#
# Check appool/aphost/tcpool/tchost
#

for aph in aphost.values():
  if not appool.has_key(aph):
    print >> sys.stderr, "ERROR, aphost=",aph,"is not assigned to a pool."
    error=True
  
#
# Check apgensvc 
#
for aps in apgensvc.keys():
  if not appool.has_key(apgensvc[aps]):
    print >> sys.stderr, "ERROR, apgensvc=",aps,"is assigned to a host not in pool"
    error=True
  if not aphost.has_key(aps):
    print >> sys.stderr, "ERROR, apgensvc=",aps,"is not described as an apacheservice"
    error=True
  
#for tch in tchost.values():
#  if not tcpool.has_key(tch):
#    print >> sys.stderr, "ERROR, tchost=",tch,"is not assigned to a pool."
#    error=True

#
# Check if cfversion is set
#

if cfversion == "":
  print >> sys.stderr,"ERROR, version of the configuration file MUST be defined."
  error=True
  
#
# Bail out if there is an error
#
  
if error:
  print >> sys.stderr, "Correct the above ERROR first"
  exit(1)

#
# Check the balancer and backend timeouts for extravagant values
#

balancertolimit = 5
for site in balancertobysite.keys():
  if balancertobysite[site] > balancertolimit:
    print >> sys.stderr,"WARNING, balancer timeout for site %s is set to %d, values greater than %d are discouraged." % (site,balancertobysite[site],balancertolimit)

backendtolimit = 30
for site in backendtobysite.keys():
  if backendtobysite[site] > backendtolimit:
    print >> sys.stderr,"WARNING, backend timeout for site %s is set to %d, values greater than %d are discouraged." % (site,backendtobysite[site],backendtolimit)

#
# Ok, now we have checked that everything was fine, we can create the configuration files
#


# Start off by creating a target directory

if os.path.exists("conf"):
  print >> sys.stderr, "ERROR, directory 'conf' exists, run this script from another directory."
  exit(1)
if os.path.exists("webhubinfo"):
  print >> sys.stderr, "ERROR, directory 'webhubinfo' exists, run this script from another directory."
  exit(1)

  
os.mkdir("conf")
os.mkdir("webhubinfo")

# Create backend directory

os.mkdir("conf/frontend")
os.mkdir("conf/backend")

# Create a subdirectory per aphost

for aph in set(aphost.values()):
  os.mkdir("conf/" + aph)

# Create the common 'haproxy template config'
  
ha_template = open("conf/haproxy.cpp", "w")
  
ha_template.write("global\n")
ha_template.write("  log 127.0.0.1 local1\n")
ha_template.write("  stats socket /var/run/haproxy.sock\n")
ha_template.write("  pidfile  /var/run/haproxy.pid\n")
ha_template.write("  maxconn  10000\n")
ha_template.write("  user   haproxy\n")
ha_template.write("  group  haproxy\n")
ha_template.write("  daemon\n")
ha_template.write("  chroot /opt/haproxy/jail\n")
ha_template.write("defaults\n")
ha_template.write("  mode http\n")
ha_template.write("  log global\n")
ha_template.write("  timeout connect 5s\n")
ha_template.write("  timeout client 10s\n")
ha_template.write("  timeout tarpit 10s\n")
ha_template.write("  timeout server 30s\n")
ha_template.write("  timeout http-request 5s\n")
ha_template.write("  timeout http-keep-alive 15s\n")
ha_template.write("  option forceclose\n")
ha_template.write("  option httplog\n")
ha_template.write("  option redispatch\n")
ha_template.write("  option contstats\n")
ha_template.write("  option dontlognull\n")
ha_template.write("  option log-separate-errors\n")
ha_template.write("  option log-health-checks\n")
ha_template.write("  option forwardfor except 127.0.0.1\n")
ha_template.write("  option tcp-smart-accept\n")
ha_template.write("  option tcp-smart-connect\n")
ha_template.write("  compression algo gzip\n")
ha_template.write("  compression offload\n")
ha_template.write("  compression type text/plain\n")
ha_template.write("  compression type text/html\n")
ha_template.write("  compression type application/xml\n")
ha_template.write("  compression type text/xml\n")
ha_template.write("  compression type text/css\n")
ha_template.write("  compression type application/javascript\n")
ha_template.write("  compression type application/x-javascript\n")
ha_template.write("  compression type text/javascript\n")
ha_template.write("  compression type application/json\n")
ha_template.write("  compression type application/atom+xml\n")
ha_template.write("  compression type text/calendar\n")
ha_template.write("  compression type text/csv\n")
ha_template.write("  compression type application/rss+xml\n")
ha_template.write("  compression type text/tab-separated-values\n")
ha_template.write("  compression type application/opensearchdescription+xml\n")
ha_template.write("  compression type text/x-asm\n")
ha_template.write("  compression type text/x-c\n")
ha_template.write("  compression type text/x-component\n")
ha_template.write("  compression type text/x-csrc\n")
ha_template.write("  compression type text/x-diff\n")
ha_template.write("  compression type text/x-makefile\n")
ha_template.write("  compression type application/x-msdos-program\n")
ha_template.write("  compression type text/x-patch\n")
ha_template.write("  compression type text/x-perl\n")
ha_template.write("  compression type application/x-python\n")
ha_template.write("  compression type text/x-python\n")
ha_template.write("  compression type application/x-ruby\n")
ha_template.write("  compression type application/x-sh\n")
ha_template.write("  compression type application/x-shellscript\n")
ha_template.write("  compression type application/x-wais-source\n")
ha_template.write("  compression type application/pkix-attr-cert\n")
ha_template.write("  compression type application/x-git-upload-pack-advertisement\n")
ha_template.write("  compression type image/x-icon\n")
ha_template.write("  default-server maxconn 1000 maxqueue 1000 inter 5s fastinter 200 downinter 30s rise 3 fall 2 slowstart 1s\n\n")
ha_template.write("  peers %s\n" % env)
for apachehost in aphipbyhost.keys():
  ha_template.write("    peer %s:1024\n" % aphipbyhost[apachehost])

# Create a config file for a site on each aphost it is assigned to (via)
#lbid = 0

#info = {}

for aps in sitemap.keys():
  aph = aphost[aps]
  apip = apsvcip[aps]
  for apport in sitemap[aps].keys():
    if len(sitemap[aps][apport]) > 1:
      apstype = 'generic'
      fid = FNV1a(str(sitemap[aps][apport]))
    else:
      apstype = 'unique'
      site = sitemap[aps][apport][0]
      fid = FNV1a(site)
#    info["env"] = env
#    info["url"] = "http://"+site
#    apaches = []
#    tomcats = []
    cf_frontend = open("conf/frontend/" + fid + ".frontend", "w")
    cf_frontend.write("  acl site_dead nbsrv(bk_%s)  lt 1\n" % FNV1a(sitemap[aps][apport][0]))
    cf_frontend.write("  monitor-uri /hapcheck\n")
    cf_frontend.write("  monitor fail if site_dead\n")
    cf_frontend.write("  tcp-request inspect-delay 20s\n")
    cf_frontend.write("  tcp-request content reject if ! HTTP\n")
#  cf_frontend.write("  errorfile 502 /Oops/502.http\n")
#  cf_frontend.write("  errorfile 503 /Oops/503.http\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .html .htm .phpt\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .jpg .jpeg .gif .png .bmp .tif .tiff .eps .ai .nef .ico .swf\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .css .js\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .txt .sql .csv .log\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .tar .tgz .gz .bz2 .rar .zip .Z .7z .jar\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .exe .msi .cab .dmg\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .doc .docx .xls .pdf .ppt .pptx .pps .psd .rtf .indd .rbs .pst\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .mid .midi .wav .mp3 .aiff .m4a .rm .wma .ra\n")
    cf_frontend.write("  acl p-url_statics  path_end -i .mp4 .avi .mpg .mpeg .mpv .mkv .dv .mov .wmv .flv .f4v .fla .mpga .aif .vob .ogg\n")
    cf_frontend.write("  acl p-url_static_  path_sub -i _static_ .cache.\n")
    cf_frontend.write("  acl p-nocache      path_sub -i .nocache.\n")
    cf_frontend.write("  rsprep ^Server:.* Server:\ awh\n")
    cf_frontend.write("  rspadd Vary:\ User-Agent\n")
    cf_frontend.write("  rspidel ^Etag\n")
    for site in sitemap[aps][apport]:
      alias = 0
      siteid = FNV1a(site)
      ctx = tccontextbysite[site]
      if ctx == "/":
            ctx = ""
      #cf_frontend.write("  acl h-hostport-%s      hdr(host) -i  %s:%s\n" % (siteid,servernamebysite[site],apportbysite[site]))
      cf_frontend.write("  acl h-host-%s      hdr_dom(host) -i  %s\n" % (siteid,servernamebysite[site]))
      if not ctx == "":
        cf_frontend.write("  acl p-context-%s      path_beg  %s\n" % (siteid,ctx))

      cf_frontend.write("  acl p-tccheck-%s      path_beg  /tccheck\n" % siteid)

      if aliasbysite.has_key(site):
        alias = '1'
        cf_frontend.write("  acl h-host-alias-%s      hdr_dom(host) -i %s\n" % (siteid,aliasbysite[site]))

      if xdomainbysite.has_key(site):
        for url in eval(xdomainbysite[site]):
          cf_frontend.write('  acl h-origin-%s-%s  hdr(Origin) -i %s\n' % (siteid,FNV1a(url),url))
          if alias == '0':
            cf_frontend.write('rspadd Access-Control-Allow-Origin: %s if h-origin-%s-%s h-host-%s\n' % (url,siteid,FNV1a(url),siteid))
          else:
            cf_frontend.write('rspadd Access-Control-Allow-Origin: %s if h-origin-%s-%s h-host-%s or h-origin-%s-%s h-host-alias-%s\n' % (url,siteid,FNV1a(url),siteid,siteid,FNV1a(url),siteid))

      if redirectsbysite.has_key(site):
        for redirect in redirectsbysite[site]:
          cf_frontend.write("  acl p-301-%s-%s  path_reg %s\n" % (siteid,FNV1a(redirect['match']),redirect['match']))
          if redirect.has_key('cond'):
            cf_frontend.write("  acl x-301-%s-%s  %s %s\n" % (siteid,FNV1a(redirect['condtype'] + redirect['cond']),redirect['condtype'].replace('HTTP_HOST','hdr_dom(host)'),redirect['cond']))
            cf_frontend.write("  redirect code 301 location %s if x-301-%s-%s p-301-%s-%s\n" % (redirect['target'],siteid,FNV1a(redirect['condtype'] + redirect['cond']),siteid,FNV1a(redirect['match'])))
          else:
            cf_frontend.write("  redirect code 301 prefix %s if p-301-%s-%s\n" % (redirect['target'],siteid,FNV1a(redirect['match'])))

      cf_frontend.write("  reqrep ^(.*)$  %s/lb.jsp          if p-tccheck-%s\n" % (ctx,siteid))
      if not ctx == "":
        cf_frontend.write("  reqirep ^/(.*)$           %s/\\1              if !p-context-%s\n" % (ctx,siteid))

      if aliasbysite.has_key(site):
        #cf_frontend.write("  reqrep ^Host:\ (.*)$      X-Forwarded-Host:\ \\1 if h-host-%s or h-host-alias-%s\n" % (siteid,siteid))
        #cf_frontend.write("  reqadd Host:\ %s:%s if h-host-%s or h-host-alias-%s\n" % (servernamebysite[site],apportbysite[site],siteid,siteid))
        cf_frontend.write("  reqrep ^Host:.* Host:\ %s:%s if h-host-%s or h-host-alias-%s\n" % (servernamebysite[site],apportbysite[site],siteid,siteid))
        if not ctx == "":
          cf_frontend.write("  redirect code 301 prefix  %(foo)s/                if !p-context-%(bar)s h-host-%(bar)s or !p-context-%(bar)s h-host-alias-%(bar)s\n" % {'foo': ctx, 'bar': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s_statics if h-host-%(foo)s p-url_statics !p-nocache !p-url_static_ or h-host-alias-%(foo)s p-url_statics !p-nocache !p-url_static_\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s_static_ if h-host-%(foo)s p-url_static_ !p-nocache or h-host-alias-%(foo)s p-url_static_ !p-nocache\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s_nocache if h-host-%(foo)s p-nocache or h-host-alias-%(foo)s p-nocache\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s if h-host-%(foo)s or h-host-alias-%(foo)s\n" % {'foo': siteid})
      else:
        #cf_frontend.write("  reqrep ^Host:\ (.*)$    X-Forwarded-Host:\ \\1 if h-host-%s \n" % (siteid))
        #cf_frontend.write("  reqadd  Host:\ %s:%s if h-host-%s \n" % (servernamebysite[site],apportbysite[site],siteid))
        cf_frontend.write("  reqrep ^Host:.*  Host:\ %s:%s if h-host-%s \n" % (servernamebysite[site],apportbysite[site],siteid))
        if not ctx == "":
          cf_frontend.write("  redirect code 301 prefix  %s/                if !p-context-%s  h-host-%s\n" % (ctx,siteid,siteid))
        cf_frontend.write("  use_backend bk_%(foo)s_statics if h-host-%(foo)s p-url_statics !p-nocache !p-url_static_\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s_static_ if h-host-%(foo)s p-url_static_ !p-nocache\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s_nocache if h-host-%(foo)s p-nocache\n" % {'foo': siteid})
        cf_frontend.write("  use_backend bk_%(foo)s if h-host-%(foo)s\n" % {'foo': siteid})

    
    cf_frontend.close()
    for site in sitemap[aps][apport]:
      siteid = FNV1a(site)
      cf_backend = open("conf/backend/" + siteid + ".backend", "w")
      if backendtobysite.has_key(site):
        cf_backend.write("  timeout server %ss\n" % backendtobysite[site])
      cf_backend.write("  balance roundrobin\n")
#      cf_backend.write("  option httpchk HEAD %s/lb.jsp HTTP/1.0\n" % ctx)
#      cf_backend.write("  http-check expect status 200\n")
      cf_backend.write("  option redispatch\n")
      cf_backend.write("  retries 1\n")
      cf_backend.write("  cookie JSESSIONID preserve indirect\n")
      cf_backend.write("  stick-table type string len 40 size 5M expire 30m\n")
      cf_backend.write("  stick store-response set-cookie(JSESSIONID) table bk_%s\n" % siteid)
      cf_backend.write("  stick on cookie(JSESSIONID) table bk_%s\n" % siteid)
      cf_backend.write("  stick on url_param(JSESSIONID) table bk_%s\n" % siteid)

      tcid = 0
      for tcs in tcsvcsbysite[site]:
        tcid += 1
        cf_backend.write("  rspadd X-AWH-Route:\ %s  if { srv_id %s }\n" % (tcroutebytc[tcs + ":" + tcportbysite[site]],tcid))
        cf_backend.write("  rspadd X-AWH-Worker:\ %s  if { srv_id %s }\n" % (tcsvcip[tcs],tcid))
        cf_backend.write("  http-response set-header Cache-Control no-store,no-cache\n")
        if tclbfactorbytc.has_key(tcs + ":" + tcportbysite[site]):
          loadfactor = tclbfactorbytc[tcs + ":" + tcportbysite[site]]
        else:
          loadfactor = 100
        #cf_backend.write("  server %s %s:%s weight %s check cookie %s\n" % (tcs,tcsvcip[tcs],tcportbysite[site],loadfactor,tcroutebytc[tcs + ":" + tcportbysite[site]]))
        cf_backend.write("  server %s %s:%s weight %s cookie %s\n" % (tcs,tcsvcip[tcs],tcportbysite[site],loadfactor,tcroutebytc[tcs + ":" + tcportbysite[site]]))

      # Backend dedicated to statics files

      cf_backend.write("  backend bk_%s_statics\n" % siteid)
      cf_backend.write("    http-response set-header Cache-Control no-cache=\"Set-Cookie,Set-Cookie2\",max-age=604800\n")
      for tcs in tcsvcsbysite[site]:
        if tclbfactorbytc.has_key(tcs + ":" + tcportbysite[site]):
          loadfactor = tclbfactorbytc[tcs + ":" + tcportbysite[site]]
        else:
          loadfactor = 100
        cf_backend.write("    server %s %s:%s weight %s cookie %s\n" % (tcs,tcsvcip[tcs],tcportbysite[site],loadfactor,tcroutebytc[tcs + ":" + tcportbysite[site]]))
 
     # Backend dedicated to explicitly static content

      cf_backend.write("  backend bk_%s_static_\n" % siteid)
      cf_backend.write("    http-response set-header Cache-Control no-cache=\"Set-Cookie,Set-Cookie2\",max-age=31536000\n")
      for tcs in tcsvcsbysite[site]:
        if tclbfactorbytc.has_key(tcs + ":" + tcportbysite[site]):
          loadfactor = tclbfactorbytc[tcs + ":" + tcportbysite[site]]
        else:
          loadfactor = 100
        cf_backend.write("    server %s %s:%s weight %s cookie %s\n" % (tcs,tcsvcip[tcs],tcportbysite[site],loadfactor,tcroutebytc[tcs + ":" + tcportbysite[site]]))


     # Backend dedicated to explicitly not cached content

      cf_backend.write("  backend bk_%s_nocache\n" % siteid)
      cf_backend.write("    http-response set-header Cache-Control no-store,no-cache,max-age=0,must-revalidate\n")
      for tcs in tcsvcsbysite[site]:
        if tclbfactorbytc.has_key(tcs + ":" + tcportbysite[site]):
          loadfactor = tclbfactorbytc[tcs + ":" + tcportbysite[site]]
        else:
          loadfactor = 100
        cf_backend.write("    server %s %s:%s weight %s cookie %s\n" % (tcs,tcsvcip[tcs],tcportbysite[site],loadfactor,tcroutebytc[tcs + ":" + tcportbysite[site]]))

      cf_backend.close()
#    apnum = 0
#    for aps in apsvcsbysite[site]:
#      apnum += 1
#    apaches.append({'ip': apip , 'port': apportbysite[site]})
#    info["apaches"] = apaches
    cf_bind = open("conf/" + aph + "/" + fid + ".bind", "w")
    cf_bind.write("frontend ft_%s\n" % fid)
    if apstype == 'unique':
      cf_bind.write("  bind %s:%s name %s\n" % (apip, apport,site))
    else:
      cf_bind.write("  bind %s:%s name generic_%s\n" % (apip, apport,fid))
    cf_bind.write("#include <%s.frontend>\n\n" % fid)
    for site in sitemap[aps][apport]:
      cf_bind.write("backend bk_%s\n" % FNV1a(site))
      #if apstype == 'unique':
      #  if pxysrcaddrbysite.has_key(site):
      cf_bind.write("  source %s\n" % apip)
      cf_bind.write("#include <%s.backend>\n\n" % FNV1a(site))
    cf_bind.close()
    if not fid in fidlist:
      ha_template.write("#include <%s.bind>\n\n" % fid)
      fidlist.append(fid)

#  whinfo = open("webhubinfo/" + site + ".json" , "w")
#  whinfo.write (json.dumps(info,indent=2))
#  whinfo.close()
  
    #lbid += 1
ha_template.close()

#
# Generate list of tomcat services to be used by rule tcscan in Makefile (nmap scan)
#

portsbyhost = {}

for tc in sitebytc.keys():
    (tchost,tcport) = tc.split(":")

    if not portsbyhost.has_key(tchost):
        portsbyhost[tchost] = []

    portsbyhost[tchost].append(tcport)

scan = open ("tcscan.ref", "w")

for host in portsbyhost.keys():
  scan.write(tcsvcip[host])
  portsbyhost[host].sort()
  for port in portsbyhost[host]:
    scan.write(' %s' % port)
  scan.write('\n')
  
scan.close()

#
# Generate a list of tcchecks
#
tcchecks = open("conf/tcchecks.conf", "w")

for site in set(sites):
  for tcs in tcsvcsbysite[site]:
    tcchecks.write('%s\thttp://%s:%s%s\n' % (site,tcsvcip[tcs],tcportbysite[site],tccheckbysite[site]))
       
tcchecks.close()

