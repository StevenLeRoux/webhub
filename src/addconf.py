#!/usr/bin/env python
# _*_ coding: utf-8 _*_

import sys
import os.path
from os import chdir
import time
from time import localtime, strftime
import re
import urllib2
import urllib

# debug_on = True / False
debug_on = False
# dont_proceed : Just read and check yaml file, dont proceed neither generate WebHub.conf
dont_proceed = False

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
  exit(1)


version = "$Revision: 0.1 $"
cfversion = ""
gents = time.time()
lbdir = os.getcwd()+"/../../../lb/trunk/"

if len(sys.argv) > 2 or len(sys.argv) < 2:
  print >> sys.stderr, "Usage : python addconf.py appname.env.yaml"
  exit(1)

chdir("../")

file = "pending/%s" % sys.argv[1]
if not os.path.isfile(file):
  print >> sys.stderr, "ERROR : not able to open your ",file," file..."
  exit(1)

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

ipw = {}
jvmr = {}
dc = []

yactionre =    re.compile(r"^(create|modify|delete)$")
yenvre =     re.compile(r"^(production|uat|sample-env)$") 
ynamere =    re.compile(r"^[^\s]+$")
ylistenre =  re.compile(r"^(8080|8443)$")
yportre =    re.compile(r"^4[0-9]{4}$")
ycontextre = re.compile(r"^/[^\s]*$")
yworkersre = re.compile(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")
#yroutesre =  re.compile(r"^4[0-9]{4}tc[0-9]+$")
yroutesre =  re.compile(r"^[^\s]+$")

instance = yaml.load(open(file))


try:
  action = instance['ACTION']
  if action == 'modify' or action == 'delete':
    print >>  sys.stderr, 'ERROR: Not implemented yet'
    exit(1)
  env = instance['ENV']
  if env == 'production':
    currentaphost = ['aphost-1','aphost-2','aphost-3','aphost-4','aphost-5','aphost-6']
    generic = {'aphost-1':'ap-1';'aphost-2':'ap-2','aphost-3':'ap-3','aphost-4':'ap-4','aphost-5':'ap-5','aphost-6':'ap-6'}
  elif env == 'uat':
    currentaphost = ['aphost-1','aphost-2']
    generic = {'aphost-1':'ap-1','aphost-2':'ap-2'}
  elif env == 'uat2':
    currentaphost = ['aphost-1','aphost-2']
    generic = {'aphost-1':'ap-3','aphost-2':'ap-4'}
  elif env == 'sample-env':
    currentaphost = ['aphost-1011','aphost-1012']
    generic = {'aphost-1011':'ap-1011','aphost-1012':'ap-1012'}
  else:
    print >> sys.stderr,"ERROR: Check for your ENV arg in your YAML file. Exiting... : ",env
    exit(1)
  yname = str(instance['NAME'])
  ylisten = str(instance['LISTEN'])
  yport = str(instance['PORT'])
  ycontext = instance['CONTEXTPATH']
  yworkers = instance['WORKERS']
  yroutes = instance['JVMROUTE']
except:
  print >> sys.stderr,"ERROR: Check for your yaml syntax"
  exit(1)

if debug_on:
	print "YAML loaded :", file
        print "action = ", action
	print "env = ", env
	print "yname = ", yname
	print "yport = ", yport
	print "ycontext = ", ycontext
	print "yworkers = ", yworkers
	print "yroutes = ", yroutes 

m = yactionre.search(action)
if not m:
  print >> sys.stderr,"ERROR: wrong action info in YAML : ",action
  exit(1)

m = yenvre.search(env)
if not m:
  print >> sys.stderr,"ERROR: wrong environment in YAML :",env
  exit(1)
  
m = ynamere.search(yname)
if not m:
  print >> sys.stderr,"ERROR: wrong app name in YAML :",yname
  exit(1)

m = ylistenre.search(ylisten)
if not m:
  print >> sys.stderr,"ERROR: wrong listening port in YAML :",ylisten
  exit(1)
  
m = yportre.search(yport)
if not m:
  print >> sys.stderr,"ERROR: wrong tc port in YAML :",yport
  exit(1)
  
m = ycontextre.search(ycontext)
if not m:
  print >> sys.stderr,"ERROR: wrong context in YAML :",ycontext
  exit(1)
  
for worker in yworkers.keys():
  m = yworkersre.search(yworkers[worker])
  if not m:
    print >> sys.stderr,"ERROR: wrong worker in YAML :",yworkers[worker]
    exit(1)
  
for route in yroutes.keys():
  m = yroutesre.search(yroutes[route])
  if not m:
    print >> sys.stderr,"ERROR: wrong route in YAML : ",yroutes[route]
    exit(1)
  
for rt in yroutes:
  if not rt in yworkers:
    print >> sys.stderr, "ERROR : There is a conflict between routes and workers in your YAML file. Exiting..."
    exit(1)

#dc.extend(yworkers.keys())
#for datacenter in set(dc):
#  ipw[datacenter] = yworkers[datacenter]
#  jvmr[datacenter] = yroutes[datacenter]


# choose the right WebHub.conf for each environment. You can make some env to cohabit in the same WebHub env. (e.g. uat and uat2)

if env in ( "uat" , "uat2" ):
  conf = "uat/WebHub.conf"
else:
  conf = env+"/WebHub.conf"


tmpconf = conf+".tmp"
try:
  os.unlink(tmpconf)
  os.rename(conf,tmpconf)
except:
  os.rename(conf,tmpconf)


aphost = {}
apgensvc = {}
aphostgensvc = {}
disabledaphosts = []
appool = {}
aphipbyhost = {}
#tchost = {}
tcpool = {}
apsvcip = {}
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


apre =       re.compile(r"^apache\s+([^\s]+)-(80|443|8080|8443)\s+(http://(ap-[0-9]+):(8080|8443)/)\s*(#.*)?$")
tcre =       re.compile(r"^tomcat\s+([^\s]+)-(80|443|8080|8443)\s+(http://([a-zA-Z0-9.-]+)@(tc-[0-9]+):(4[0-9]{4})(/[a-zA-Z0-9./-]*))(\s+([1-9]|[1-9][0-9]|100))*\s*(#.*)?$")
#tcre =       re.compile(r"^tomcat\s+([^\s]+)-(80|443|8080|8443)\s+(http://([a-z0-9-]+)@(tc-[0-9]+):(4[0-9]{4})(/[a-zA-Z0-9./-]*))(\s+([1-9]|[1-9][0-9]|100))*\s*(#.*)?$")
aphostre =   re.compile(r"^apachehost\s+(aphost-[0-9]+)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([a-z0-9\.-]+)\s*(OFF)?\s*(#.*)?$")
#tchostre =   re.compile(r"^tomcathost\s+(tchost-[0-9]+)\s+([a-z0-9.-]+)\s*(#.*)?$")
apgensvcre =    re.compile(r"^apachegeneric\s+(ap-[0-9]+)\s+(aphost-[0-9]+)\s*(#.*)?$")
apsvcre =    re.compile(r"^apacheservice\s+(ap-([0-9]+))\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+(aphost-[0-9]+)\s*(#.*)?$")
tcsvcre =    re.compile(r"^tomcatservice\s+(tc-([0-9]+))\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([a-z0-9\.-]+)\s*(#.*)?$")
aliasre =    re.compile(r"^alias\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
nocompre =     re.compile(r"^nocompress\s+([^\s]+)-(80|443|8080|8443)\s+([^\s]+)\s*(#.*)?$")
nofailoverre = re.compile(r"^nofailover\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
hostportre = re.compile(r"^hostport\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
setcookiere = re.compile(r"^setcookie\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
pxysrcaddrre = re.compile(r"^pxysrcaddr\s+([^\s]+)-(80|443|8080|8443)\s+(on|off)\s*(#.*)?$")
xdomainre = re.compile(r"^xdomain\s+([^\s]+)-(80|443|8080|8443)\s+(.*)\s*(#.*)?$")
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


whconf = open(tmpconf,"r")

for line in whconf:
  lineno += 1
  line = line.strip()

  m = aphostre.search(line)

  if m:
    aph = m.group(1).lower()
    aphip = m.group(2)
    app = m.group(3)

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
    #if m.group(7):
    #    iesucksbysite[k] = m.group(7)


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


#create new apacheservice
# here is tree different manner to affect new IP/svc:
# sample-env will pick the last ap-* and increment from the last, and increment the IP from the pool
# production will pick from the last IP and increment regardless the pool. It is a more flat distribution than for sample-env

# basically, sample-env is working pairwise , when a couple of node will be judged full, you change the currentaphost to two new nodes
# production env is working flatly distributing to all nodes in currentaphost too, but not picking the IP in a dedicated address pool by host.

# uat is using virtualhosting so it uses the same addresses (generic service), so we dont create a new service.

newap = {}
if env == "sample-env" or re.match('sample-',env):
  apintbyhost = {}
  lastintbypool = {}
  lastipbypool = {}
  newipbyaphost = {}
  for ap in currentaphost:
    apintbyhost[ap] = []
    for ip in apipbyhost[ap]:
      apintbyhost[ap].append(IPToInt(ip))
  for ap in currentaphost:
    apintbyhost[ap].sort()
    lastintbypool[ap] = apintbyhost[ap].pop()
    lastipbypool[ap] = IntToIP(lastintbypool[ap])
 
  lastsvc = apsapsnum[apipsvc[lastipbypool[currentaphost[1]]]]
  newsvc = lastsvc
 
  for ap in currentaphost:
    newsvc = int(newsvc)+1
 
    newip = IntToIP(int(lastintbypool[ap])+1)
    apsvcip["ap-"+str(newsvc)] = newip
    apsvcbyhost[ap].append("ap-"+str(newsvc))
    newap[ap] = "ap-"+str(newsvc)
elif env == "production":
  apint = {}
  lastint = {}
  lastip = {}
  newipbyaphost = {}
  apint = []
  for ip in apipsvc.keys():
    apint.append(IPToInt(ip))
  apint.sort()
  lastint = apint.pop()
  lastip = IntToIP(lastint)
  
  lastsvc = apsapsnum[apipsvc[lastip]]
  newsvc = lastsvc
  ipadd = 0
  for ap in sorted(currentaphost):
    ipadd += 1
    newsvc = int(lastsvc)+ipadd
    newip = IntToIP(int(lastint)+ipadd)
    apsvcip["ap-"+str(newsvc)] = newip
    apsvcbyhost[ap].append("ap-"+str(newsvc))
    newap[ap] = "ap-"+str(newsvc)
else:
  for ap in currentaphost:
    if ap in generic:
      newap[ap] = generic[ap]

#check presence of tomcatservice
for dc in yworkers.keys():
  if not yworkers[dc] in tciplist:
    tcsvclist.sort()
    lasttcnum = tcsvclist.pop()
    newtcnum = str(int(lasttcnum)+1)
    tcsvclist.append(lasttcnum)
    tcsvclist.append(newtcnum)
    tcpool["tc-"+newtcnum] = "pool-"+dc
    tcsvcip["tc-"+newtcnum] = yworkers[dc]
    tcstcsnum["tc-"+newtcnum] = int(newtcnum)
    tcipbypool["pool-"+dc].append(yworkers[dc])
  else:
    if not yworkers[dc] in tcipbypool["pool-"+dc]:
      print >> sys.stderr,"ERROR, you should check in which datacenter is located the IP of your worker"
      print >> sys.stderr,"ERROR,",yworkers[dc],"does not seem to be on the",dc,"side. Exiting..."
      exit(1)

if env == 'sample-env' or re.match('sample-',env):
  k = yname + '.sample.domain.tld-' + ylisten
elif env == 'production':
  k = yname + '.domain.tld-' + ylisten
elif env == 'uat':
  k = yname + '.uat.domain.tld-' + ylisten


# ap
if not servernamebysite.has_key(k):
  apportbysite[k] = ylisten
  if env == 'sample-env':
    servernamebysite[k] = yname + '.sample.domain.tld'
  elif env == 'production':
    servernamebysite[k] = yname + '.domain.tld'
  elif env == 'uat':
    servernamebysite[k] = yname + '.uat.domain.tld'

else:
  print >> sys.stderr,"ERROR, this site seems to be in conf..."
  exit(1)
for ap in currentaphost:
  if not apsvcsbysite.has_key(k):
    apsvcsbysite[k] = []
  apsvcsbysite[k].append(newap[ap])
# tc
for worker in yworkers.keys():
  # Check the tc ip
  if not tcipsvc.has_key(yworkers[worker]):
      print "ERROR : tcipsvc=",yworkers[worker],"is not known !"
      exit(1)
  tc = tcipsvc[yworkers[worker]]
  rt = yroutes[worker]
  if not tcsvcsbysite.has_key(k):
    tcsvcsbysite[k] = []
  tcsvcsbysite[k].append(tc)
  if not tcroutesbysite.has_key(k):
    tcroutesbysite[k] = []
  tcroutesbysite[k].append(rt)
  if not tcroutebytc.has_key(tc+":"+str(yport)):
    tcroutebytc[tc+":"+str(yport)] = rt
  if not tccontextbysite.has_key(k):
    tccontextbysite[k] = ycontext
  if not tcportbysite.has_key(k):
    tcportbysite[k] = str(yport)
  if not tccheckbysite.has_key(k):
    tccheckbysite[k] = "lb.jsp"


# compress
#  => by default

# nofailover
#  => not by default

# forensic
# => not by default

# balancerto
# => not by default

# backendto
# => not by default

# expire
# => not by default

# cache
#  => by default
#  Anyway, if you want to add a file type cached which is not handled by default template (see genconf.py) you can add it here :

#if not cacheablebysite.has_key(k):
#            cacheablebysite[k] = []
#cacheablebysite[k].append({'match':'^.*\.png$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.gif$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.jpg$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.jpeg$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.bmp$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.css$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.swf$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.jar$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.js$','type':'public','maxage':str(7200)})
#cacheablebysite[k].append({'match':'^.*\.nocache\..*$','type':'no-cache'})
#cacheablebysite[k].append({'match':'^.*\.cache\..*$','type':'public','maxage':str(31536000)})
#cacheablebysite[k].append({'match':'^.*_static_.*$','type':'public','maxage':str(31536000)})

#logheader
# => not by default

# redirect
# => not by default

# rewrite
# => not by default




if dont_proceed:
  exit(1)


marker =  strftime("%Y%m%d%H%M%S", localtime())

cf = open(conf,"w")

cf.write('version ' + cfversion + '\n')

for pool in sorted(appool.keys()):
  cf.write('apachehost\t' + pool + '\t' + appool[pool] + '\t' + aphipbyhost[pool] +  '\n')

if not (re.match('silo',env) or re.search('-prod',env)):
  for apgen in sorted(apgensvc.keys()):
    cf.write('apachegeneric\t' + apgen + '\t' + apgensvc[apgen] + '\n')

for ap in sorted(apsvcbyhost.keys()):
  for svc in apsvcbyhost[ap]:
    cf.write('apacheservice\t' + svc + '\t' + apsvcip[svc] + '\t' + ap + '\n')

for tc in sorted(tcpool.keys()):
  cf.write('tomcatservice\t' + tc + '\t' + tcsvcip[tc] + '\t' + tcpool[tc] + '\n')


sites = []
sites.extend(apsvcsbysite.keys())
sites.extend(tcsvcsbysite.keys())

for site in sorted(set(sites)):
  cf.write('###########' + site + '##########################################\n')
  for apache in apsvcsbysite[site]:
    cf.write('apache     ' + site + '\thttp://' + apache + ':' + apportbysite[site] + '/\n')
  cf.write('\n')
  for tomcat in tcsvcsbysite[site]:
    if tclbfactorbytc.has_key(tomcat+":"+tcportbysite[site]):
      lb = " "+tclbfactorbytc[tomcat+":"+tcportbysite[site]]
    else:
      lb = ""
    if tccontextbysite[site] == "/":
      lbjsp = "/lb.jsp "
    else:
      lbjsp = tccontextbysite[site] + "/lb.jsp"
    cf.write('tomcat     ' + site + '\thttp://' + tcroutebytc[tomcat+":"+tcportbysite[site]] + '@' + tomcat + ':' + tcportbysite[site] + lbjsp + lb + '\n')
  cf.write('\n')
  if aliasbysite.has_key(site):
    cf.write('alias ' + site + '\t' + aliasbysite[site] + '\n')
  if pxysrcaddrbysite.has_key(site):
    cf.write('pxysrcaddr ' + site + '\t' + pxysrcaddrbysite[site] + '\n')
  if xdomainbysite.has_key(site):
    cf.write('xdomain ' + site + '\t' + xdomainbysite[site] + '\n')
  if balancertobysite.has_key(site):
    cf.write('balancerto ' + site + '\t' + str(balancertobysite[site]) + '\n')
    cf.write('\n')
  if backendtobysite.has_key(site):
    cf.write('backendto  ' + site + '\t' + str(backendtobysite[site]) + '\n')
    cf.write('\n')
  if rewritesbysite.has_key(site):
    for rewrite in rewritesbysite[site]:
      cf.write('rewrite  ' + site + '\t"' + rewrite['match'] + '"\t"' + rewrite['target'] + '"\n')
    cf.write('\n')
  if redirectsbysite.has_key(site):
    for redirect in redirectsbysite[site]:
      if redirect.has_key('cond'):
        cf.write('redirect  ' + site + '\t"' + redirect['match'] + '"\t"' + redirect['target'] + '"\t"' + redirect['condtype'] + ':' + redirect['cond'] + '"\n')
      else:
        cf.write('redirect  ' + site + '\t"' + redirect['match'] + '"\t"' + redirect['target'] + '"\n')
    cf.write('\n')
  if expiresbysite.has_key(site):
    for expire in expiresbysite[site]:
      cf.write('expire   ' + site + '\t"' + expire['match'] + '"\t' + expire['expire'] + '\n')
    cf.write('\n')
  if nofailoverbysite.has_key(site):
    cf.write('nofailover ' + site + '\t' + nofailoverbysite[site] + '\n')
  if hostportbysite.has_key(site):
    cf.write('hostport ' + site + '\t' + hostportbysite[site] + '\n')
  if setcookiebysite.has_key(site):
    cf.write('setcookie ' + site + '\t' + setcookiebysite[site] + '\n')
  if nocompressbysite.has_key(site):
    cf.write('nocompress   ' + site + '\t' + nocompressbysite[site] + '\n')
    cf.write('\n')
  if cacheablebysite.has_key(site):
    for cacheable in cacheablebysite[site]:
      if not cacheable['type'] == 'no-cache':
        cf.write('cache      ' + site + '\t"' + cacheable['match'] + '"\t' + cacheable['type'] + '\t' +cacheable['maxage'] + '\n')
      else:
        cf.write('cache      ' + site + '\t"' + cacheable['match'] + '"\t' + cacheable['type'] + '\n')
  cf.write('\n')
  if forensiclogbysite.has_key(site):
    cf.write('forensic   ' + site)

cf.close()

l = 0
new = {}
for ap in currentaphost:
  l += 1
  new[l] = newap[ap]


# hook to produce virtual IP service

if action == "create" and env in [ 'sample-env', 'production']:
  # import config load your api key to call the service API
  from config import *
  if env == "production":
    data = '{"target": "target", "apikey" : "' + apikey + '", "silo": "' + silo +'", "name": "' + yname + '", "nodes": {"1": { "' + new[1] +'": "'+ apsvcip[new[1]] + '"}, "2": { "' + new[2] + '": "' + apsvcip[new[2]] + '"},"3": { "' + new[3] +'": "'+ apsvcip[new[3]] + '"}, "4": { "' + new[4] + '": "' + apsvcip[new[4]] + '"},"5": { "' + new[5] +'": "'+ apsvcip[new[5]] + '"}, "6": { "' + new[6] + '": "' + apsvcip[new[6]] + '"}}, "health": {"proto": "http", "context": "/apcheck"}, "listen": "' + ylisten + '"}'
  else:
    data = '{"target": "target", "apikey" : "' + apikey + '", "silo": "' + silo +'", "name": "' + yname + '", "nodes": {"1": { "' + new[1] +'": "'+ apsvcip[new[1]] + '"}, "2": { "' + new[2] + '": "' + apsvcip[new[2]] + '"}}, "health": {"proto": "http", "context": "/apcheck"}, "listen": "' + ylisten + '"}'
  print data

  # fill your VIP service API
  req = urllib2.Request('http://API:8080/api/v0/vs', data, {'Content-Type': 'application/json'})
  response = urllib2.urlopen(req)
  result = response.read()
  response.close()
  print result


