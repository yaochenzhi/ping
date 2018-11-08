SELF=`basename $0`
LOCATED=`dirname $0`
MONITOR=`echo ${SELF} | sed 's/sh/py/'`

ps -ef | grep "${LOCATED}/${MONITOR}" | grep -v grep

if [ "$?" != 0 ];then
    echo "Monitor started at `date +'%Y-%m-%d %H:%M:%S'`"
    echo "... ..."
    python "${LOCATED}/${MONITOR}" >"/tmp/${MONITOR}.log" 2>&1
    echo "Finished at `date +'%Y-%m-%d %H:%M:%S'`"
else
    echo
    echo "Monitor process detected above !"
    echo "EXITING !!!"
fi
