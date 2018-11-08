SELF=`basename $0`
LOCATED=`dirname $0`
# CHECKER=`echo ${SELF} | tr sh py`
CHECKER=`echo ${SELF} | sed 's/sh/py/'`

ps -ef | grep "${LOCATED}/${CHECKER}" | grep -v grep

if [ "$?" != 0 ];then
    echo "Checker started at `date +'%Y-%m-%d %H:%M:%S'`"
    echo "... ..."
    python "${LOCATED}/${CHECKER}" >"/tmp/${CHECKER}.log" 2>&1
    echo "Finished at `date +'%Y-%m-%d %H:%M:%S'`"
else
    echo
    echo "Checker process detected above !"
    echo "EXITING !!!"
fi
