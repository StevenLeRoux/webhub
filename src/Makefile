#
# @(#)$Id: Makefile,v 1.4 2009/10/22 09:55:52 Exp $
#

#
# note that some method are converted from previous webhub version using Apache HTTPD instead of HAProxy.
# These functions still need to be converted : process, status
#

TS=$(shell date +%Y%m%dT%H%M%S)
HAPROXY_HOME=/opt/haproxy
WEBHUB_INFO_HOME=/opt/webhub
WEBHUB_INFO_HOST=@WHINFOHOST@
SVNREPO=http://svn/repos/webhub

help:
	@echo "Available targets:"
	@echo ""
	@echo "    genconf"
	@echo "       Generates the HAProxy configuration files from WebHub.conf"
	@echo ""
	@echo "    syncconf"
	@echo "       Generates the HAProxy configuration then sends it on the WebHub servers"
	@echo ""
	@echo "    backupconf"
	@echo "       Backs up the current configuration deployed on the WebHub servers, configuration is saved in a directory yyyymmddThhmmss"
	@echo ""
	@echo "    yyymmddThhmmss-rollback"
	@echo "       Sends onto the WebHub servers a previously backed up configuration, the directory yyyymmddThhmmss MUST exist"
	@echo ""
	@echo "    checkconf"
	@echo "       Issues a 'haproxyctl configtest' on all WebHub servers"
	@echo ""
	@echo "    restart"
	@echo "       Issues a 'haproxyctl restart' on last WebHub servers"
	@echo ""
	@echo "    stop"
	@echo ""
	@echo "       Issues a 'haproxyctl stop' on all WebHub servers"
	@echo ""
	@echo "    start"
	@echo ""
	@echo "       Issues a 'haproxyctl start' on all WebHub servers"
	@echo ""
	@echo "    status"
	@echo ""
	@echo "       Outputs the status of the different HAProxy nodes"
	@echo ""
	@echo "    testconf"
	@echo ""
	@echo "       Generates the HAProxy configuration files from WebHub.conf just to check if it works, result is discarded"

updateconf:
	@( \
	  res=`svn status WebHub.conf|grep WebHub.conf`;\
	  if [ "$${res}" != "" ]; \
	  then \
	    echo "#### ERROR: Configuration file WebHub.conf is not committed.";\
            exit 1;\
	  fi; \
	 )

checkpython:
	@( \
	  res=`python -V 2>&1|grep "2.5"`;\
	  if [ "$${res}" != "" ]; \
	  then \
	    echo "#### ERROR: You need at least python 2.6 to run Make geninfo.";\
	    exit 1;\
	  fi; \
	)

addyaml2conf: 
	@( \
	  if [ "$(YAML)" != "" ];\
	  then \
		f=../pending/$(YAML);\
		if test -e $$f ;\
		then \
			echo "$$f exists";\
			bash ../src/addconf.sh $(YAML);\
		else \
			echo "$$f not exists";\
		fi;\
	  fi;\
	)

addallyaml: 
	@( \
          for f in `ls -1 ../pending/*$(TARGET).yaml|cut -d "/" -f3`; \
          do \
	    echo $$f;\
            bash ../src/addconf.sh $$f;\
          done; \
	)
	
	
addconf:
	@bash ../src/addconf.sh

showtc:
	python ../src/showconf.py tc < WebHub.conf

showap:
	python ../src/showconf.py ap < WebHub.conf

showsites:
	python ../src/showconf.py sites < WebHub.conf

showmap:
	python ../src/showconf.py map < WebHub.conf

genconf: cleanconf checkpython
	@svn copy $(SVNREPO)/trunk/$(TARGET)/WebHub.conf $(SVNREPO)/tags/$(TARGET)/WebHub.conf-$(TS) -m "tag $(TARGET)/WebHub.conf as WebHub.conf-$(TS)"
	python ../src/genconf.py $(TARGET) < WebHub.conf
	
syncconf: updateconf genconf pushinfo backupconf tcscan
	@for node in $(NODES); do rsync -a -e ssh conf/ root@$${node}:$(HAPROXY_HOME)/etc/ ; done

pushinfo: 
	@rsync -a webhubinfo/. root@$(WEBHUB_INFO_HOST):$(WEBHUB_INFO_HOME)/sites/
	@rsync -a -e ssh tcnok.html root@$(WEBHUB_INFO_HOST):$(WEBHUB_INFO_HOME)/stats/$(TARGET)_tcnok.html

warnforce:
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "!!!                                                       !!!"
	@echo "!!!   FORCING is HIGHLY discouraged, you've been warned   !!!"
	@echo "!!!                                                       !!!"
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

forcesyncconf: warnforce updateconf genconf pushinfo backupconf
	@for node in $(NODES); do rsync -a -e ssh conf/ root@$${node}:$(HAPROXY_HOME)/etc/ ; done

backupconf:
	@( \
	for node in $(NODES); \
	do \
	  mkdir -p $(TS)/$${node}; \
	  rsync -a -q -e ssh root@$${node}:$(HAPROXY_HOME)/etc $(TS)/$${node}; \
	done; \
	echo "####";\
	echo "#### Configuration has been backed up in $(TS)";\
	echo "####";\
	)

checkconf:
	@( \
	for node in $(NODES); \
	do \
	  echo "#### $${node} ";\
	  ssh root@$${node} $(HAPROXY_HOME)/bin/haproxyctl configtest;\
	done; \
	)

#process:
#	@( \
#	for apache in $(APACHE); \
#	do \
#	  echo "#### $${apache} ";\
#	  ssh root@$${apache} "ps ax|grep haproxy|wc -l";\
#	done; \
#	)

cleanconf:
	rm -rf conf webhubinfo tcnok.html

cleaninfo:
	@ssh root@$(WEBHUB_INFO_HOST) rm -f $(WEBHUB_INFO_HOME)/sites/*.json ;\

%-rollback:
	@( \
	conf=$(subst -rollback,,$@); \
	if [ ! -d $${conf} ]; \
	then \
	  echo "####";\
	  echo "#### ERROR: Directory $${conf} does not exist, cannot rollback conf";\
	  echo "####";\
          exit -1; \
	fi; \
	for node in $(NODES); \
	do \
	  mkdir -p $(TS)/$${node}; \
	  rsync -a -e ssh $${conf}/$${node}/conf root@$${node}:$(HAPROXY_HOME)/; \
	done \
	)

restart: checkconf
	@( \
	for node in $(NODES); \
	do \
	  ssh root@$${node} $(HAPROXY_HOME)/bin/haproxtyctl restart;\
	done ;\
	)

reload: checkconf
	@( \
	for node in $(NODES); \
	do \
	  ssh root@$${node} $(HAPROXY_HOME)/bin/haproxyctl reload;\
	done ;\
	)

stop: checkconf
	@( \
	for node in $(NODES); \
	do \
	  ssh root@$${node} $(HAPROXY_HOME)/bin/haproxyctl stop;\
	done ;\
	)

start: checkconf
	@( \
	for node in $(NODES); \
	do \
	  ssh root@$${node} $(HAPROXY_HOME)/bin/haproxyctl start;\
	done ;\
	)

status:
	@( \
	for node in $(NODES); \
	do \
	  echo "NODE::=$${node}";\
	  ssh root@$${node} 'printf "GET /server-status HTTP/1.0\r\n\r\n"|nc 127.0.0.1 8080';\
	done ;\
	)|python ../src/webstatus.py

tcscan:
	@( \
	for node in $(NODES); \
	do \
	  echo "NODE::=$${node}";\
	  cut -f 1 -d ' ' tcscan.ref|ssh root@$${node} nmap -sS -P0 -p40000-40999 -oX - -iL -;\
	done; \
	echo "ENDNODE";\
	)|python ../src/tcscan.py tcscan.ref

testconf:
	@( \
	mkdir -p testconf.$$$$;\
	cd testconf.$$$$;\
	python ../../src/genconf.py $(TARGET) < ../WebHub.conf;\
	cd ..;\
	rm -rf testconf.$$$$;\
	)

%-diff:
	@( \
	find conf -type f > diffconf.$$$$ ;\
	conf=$(subst -diff,,$@); \
	for node in $(NODES);\
	do \
          pushd $${conf}/$${node};\
	  cat ../../diffconf.$$$$ | while read file;\
	  do \
	    diff $${file} ../../$${file} >> ../../diffconf-$${apache}.$$$$;\
	  done;\
	  popd;\
	done;\
	md5=`md5sum diffconf-*.$$$$|cut -f 1 -d ' '|sort -u|wc -l`;\
	rm diffconf.$$$$;\
	if [ $${md5} -ne 1 ];\
	then\
	  echo "PREVIOUS CONFIGURATION IS NOT IDENTICAL ON ALL HAPROXIES";\
	  exit 1;\
	fi;\
	)

