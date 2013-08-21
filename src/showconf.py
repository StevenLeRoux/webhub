#!/usr/bin/env python
# _*_ coding: utf-8 _*_

import sys
import os.path
from os import chdir
import time
from time import localtime, strftime
import re

try:
  import yaml
  have_yaml=True
except:
  have_yaml=False

try:
  import ipaddr
  have_ipaddr=True
except:
  have_ipaddr=False


if not have_yaml:
  print
  print "You need to add Yaml lib"
  print
  print "apt-get install python-yaml"
  print
  exit(1)

if not have_ipaddr:
  print
  print "You need to install ipaddr-py"
  print
  print "apt-get install python-ipaddr"
  print "or get it from"
  print "http://code.google.com/p/ipaddr-py/"
  print
#  exit(1)

version = "$Revision: 0.1 $"
cfversion = ""
gents = time.time()
lbdir = os.getcwd()+"/../../../lb/trunk/"


def IntToIP( intip ):
  octet = ''
  for exp in [3,2,1,0]:
    octet = octet + str(intip / ( 256 ** exp )) + "."
    intip = intip % ( 256 ** exp )
  return(octet.rstrip('.'))

def IPToInt( ip ):
  exp = 3
  intip = 0
  for quad in ip.split('.'):
    intip = intip + (int(quad) * (256 ** exp))
    exp = exp - 1
  return(intip)


aphost = {}
apgensvc = {}
aphostgensvc = {}
disabledaphosts = []
appool = {}
#tchost = {}
tcpool = {}
apsvcip = {}
aplist = []
apipsvc = {}
apipbyhost = {}
apsvcbyhost = {}
apsapsnum = {}
tcstcsnum = {}
tcipbypool = {}
tcsvcip = {}
tcipsvc = {}
tcsvclist = []
tciplist = []

#apre = re.compile(r"^([^\s]+)\s+(80|443|8080|8443)\s+(http://([a-z0-9\.-]+):(8080|8443)/)\s*(#.*)?$")
#tcre = re.compile(r"^([^\s]+)\s+(80|443|8080|8443)\s+(http://([a-z0-9-]+)@([a-z0-9\.-]+):([0-9]{4,5})/([a-z0-9-]*))\s*(#.*)?$")

apre =       re.compile(r"^apache\s+([^\s]+)-(80|443|8080|8443)\s+(http://(ap-[0-9]+):(8080|8443)/)\s*(#.*)?$")
tcre =       re.compile(r"^tomcat\s+([^\s]+)-(80|443|8080|8443)\s+(http://([a-z0-9-]+)@(tc-[0-9]+):(4[0-9]{4})(/[a-zA-Z0-9./-]*))(\s+([1-9]|[1-9][0-9]|100))*\s*(#.*)?$")
aphostre =   re.compile(r"^apachehost\s+(aphost-[0-9]+)\s+([a-z0-9\.-]+)\s*(OFF)?\s*(#.*)?$")
#tchostre =   re.compile(r"^tomcathost\s+(tchost-[0-9]+)\s+([a-z0-9.-]+)\s*(#.*)?$")
apgensvcre = re.compile(r"^apachegeneric\s+(ap-[0-9]+)\s+(aphost-[0-9]+)\s*(#.*)?$")
apsvcre =    re.compile(r"^apacheservice\s+(ap-([0-9]+))\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+(aphost-[0-9]+)\s*(#.*)?$")
tcsvcre =    re.compile(r"^tomcatservice\s+(tc-([0-9]+))\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([a-z0-9\.-]+)\s*(#.*)?$")
aliasre =    re.compile(r"^alias\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
pxysrcaddrre = re.compile(r"^pxysrcaddr\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
xdomainre = re.compile(r"^xdomain\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
nocompre =     re.compile(r"^nocompress\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s*(#.*)?$")
nofailoverre = re.compile(r"^nofailover\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
hostportre = re.compile(r"^hostport\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
setcookiere = re.compile(r"^setcookie\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
forensicre = re.compile(r"^forensic\s+([^\s]+)-(80|443|8080|8443)\s*(#.*)?$")
balancertore = re.compile(r"^balancerto\s+([^\s]+)-(80|443|8080|8443)\s+([0-9]+)\s*(#.*)?$")
backendtore = re.compile(r"^backendto\s+([^\s]+)-(80|443|8080|8443)\s+([0-9]+)\s*(#.*)?$")
expirere =   re.compile(r"^expire\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s+\"([^\"]+)\"\s*(#.*)?$")
cachere =    re.compile(r"^cache\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\"]+)\"\s+(public|private|no-cache)\s*([0-9]+)?\s*(#.*)?$")
logheaderre =re.compile(r"^logheader\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s*(#.*)?$")
redirectre = re.compile(r"^redirect\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\s]+)\"\s+\"([^\"]+)\"(\s+\"([^\"]+):([^\"]+)\")?\s*(#.*)?$")
rewritere =  re.compile(r"^rewrite\s+([^\s]+)-(80|443|8080|8443)\s+\"([^\s]+)\"\s+\"([^\"]+)\"\s*(#.*)?$")
commentre =  re.compile(r"^\s*(#.*)?$")
versionre =  re.compile(r"^version\s+(.*)\s*$")

apsvcsbysite = {}
apportbysite = {}
tccontextbysite = {}
tcportbysite = {}
tcroutesbysite = {}
tcsvcsbysite = {}
tccheckbysite = {}
tcroutebytc = {}
tclbfactorbytc = {}
sitebyap = {}
sitebytc = {}
sitemap = {}
servernamebysite = {}
forensiclogbysite = {}
aliasbysite = {}
pxysrcaddrbysite = {}
xdomainbysite = {}
nocompressbysite = {}
nofailoverbysite = {}
hostportbysite = {}
setcookiebysite = {}
expiresbysite = {}
cacheablebysite = {}
logheadersbysite = {}
redirectsbysite = {}
rewritesbysite = {}
backendtobysite = {}
balancertobysite = {}

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


#    m = tchostre.search(line)
#    
#    if m:
#        tch = m.group(1).lower()
#        tcp = m.group(2)
#        
#        if tcpool.has_key(aph):
#            print >> sys.stderr, lineno,"ERROR","tchost=",tch,"is already defined."
#            error = True
#        else:
#            tcpool[tch] = tcp
#            
#        continue

  m = apsvcre.search(line)

  if m:
    aps = m.group(1).lower()
    apsnum = m.group(2).lower()
    apip = m.group(3)
    aph = m.group(4).lower()

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
        apipsvc[apip] = aps
        apsapsnum[aps] = apsnum
        aplist.append(int(apsnum))
        if not apipbyhost.has_key(aph):
          apipbyhost[aph] = []
        if not apsvcbyhost.has_key(aph):
          apsvcbyhost[aph] = []
        if not apip in apipbyhost[aph]:
          apipbyhost[aph].append(apip)
        if not aps in apsvcbyhost[aph]:
          apsvcbyhost[aph].append(aps)

    continue

  m = tcsvcre.search(line)

  if m:
    tcs = m.group(1).lower()
    tcsnum = m.group(2).lower()
    tcip = m.group(3)
    tcp = m.group(4).lower()

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
        tcipsvc[tcip] = tcs
        tcstcsnum[tcs] = int(tcsnum)
        tcsvclist.append(int(tcsnum))
        tciplist.append(tcip)
        if not tcipbypool.has_key(tcp):
          tcipbypool[tcp] = []
        tcipbypool[tcp].append(tcip)
    continue

  m = nocompre.search(line)

  if m:
    site = m.group(1).lower()
    port = m.group(2)

    k = site + "-" + port

    nocompressbysite[k] = m.group(3).strip()


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
    proxysrcaddr = m.group(3)
    if not pxysrcaddrbysite.has_key(k) and pxysrcaddr == 'on':
      pxysrcaddrbysite[k] = proxysrcaddr

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

    if not hostportbysite.has_key(k):
      hostportbysite[k] = hostport

    continue


  m = setcookiere.search(line)

  if m:
    site = m.group(1).lower()
    port = m.group(2)

    k = site + "-" + port

    setcookie = m.group(3)

    if not setcookiebysite.has_key(k):
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

    if apsvc in apgensvc.keys():
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
        tccontext = ""
    else:
      print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"both context and check MUST be defined."
      error = True

    #print "site=",site,"port=",port,"tcroute=",tcroute,"tcsvc=",tcsvc,"tcport=",tcport,"tccontext=",tccontext,"tccheck=",tccheck

    if not sitebytc.has_key(tc):
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

#        if not tchost.has_key(tcsvc):
#            print >> sys.stderr, lineno,"ERROR","site=",site,"port=",port,"defines tcsvc=",tcsvc,"which is not known"
#            error=True


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
  exit(1)



if sys.argv[1] == "map":
   print sitemap

if sys.argv[1] == "tc":
   print tcsvclist 

if sys.argv[1] == "ap":
   print aplist 

if sys.argv[1] == "sites":
   sites = []
   sites.extend(apsvcsbysite.keys())
   sites.extend(tcsvcsbysite.keys())
   print set(sites)
