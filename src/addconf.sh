#!/bin/bash
#
# @(#)$Id: addconf.sh,v 1.0 2010/06/07 14:32:47 c2504 Exp $


#Usage : ./addconf.sh

DATE=`date +%Y%m%d%H%M`
WHROOT=`dirname $0`"/.."
CONFDIR=$WHROOT/pending
SITESDIR=$WHROOT/sites
CONF=$1
ARGS=$#
SCP=scp
rep=0

loadAvailConf() {
	j=1
	for k in `ls -1 $CONFDIR/*.yaml 2> /dev/null |cut -d "/" -f5`; do
		indexconf[$j]=$k
		j=`expr $j + 1`
	done
}

printConf() {
	tput clear
	tput cup 2 10
	tput setaf 3
	echo "SysAdmin Services"
	tput sgr0
	tput cup 4 12
	tput rev
	echo "WebHub Helper"
	tput sgr0
	tput cup 6 10
	echo "Pending confs :"
	tput cup 7 10
	echo "----------------------------"
	tputline=8
	CONFNUMBER=`ls -1 $CONFDIR/*.yaml 2> /dev/null |wc -l`
	if [ $CONFNUMBER != "" ];then
		for ((i=1;i<=$CONFNUMBER;i++));do
			tput cup $tputline 10
			echo "$i. ${indexconf[$i]}"
			tputline=`expr $tputline + 1`
		done
	else
		tput cup $tputline 10
		echo " No pending confs actually..."
	fi
	tputline=`expr $tputline + 1`
}

chooseConf() {
	valid=0
	while [ $valid = 0 ]
	do
		loadAvailConf
		printConf
		tput bold
		tput cup $tputline 10
		read -p "Choose one or (e) to exit : " confid
                tput clear
                tput sgr0
                tput rc
		case $confid in
			"e" ) valid=1;;
			[1-9] ) addYaml2Conf ${indexconf[$confid]};;
			* )  ;;
		esac  
	done
}

addYaml2Conf() { 
	local f=$1
	echo "addYaml2Conf : $f"
	python ../src/addconf.py $f 2>&1 >> /tmp/addconf.log
	if [ $? -eq 0 ];then
		svn mv $CONFDIR/$f $SITESDIR/$f 
		cd $WHROOT
		svn commit -m "$f added" 
		cd - 
	else
		echo "ERROR while processing addconf.py... Exiting"
		exit 1
	fi
}


#
# main
#
#
# Usage : addconf.sh [file.yaml]
#
if [ $# = 0 ]
then
	#Mode Interactif"
	chooseConf
elif [ $# = 1 ]
 	then 
	#Fichier YAML transmis en argument
	addYaml2Conf $1
elif [ $# = 2 ]
 	then 
	#Fichier YAML transmis en argument
	addAllYaml $2
else
	echo "Usage : addconf.sh [file.yaml]"
	exit 1;
fi
exit 0;

