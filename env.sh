TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$PYTHONPATH:$TOPDIR:$TOPDIR/apps:$TOPDIR/py3rd:$TOPDIR/missrv

ACOM_PATH=$TOPDIR/../acom
export PYTHONPATH=$PYTHONPATH:$ACOM_PATH/djapps:$ACOM_PATH
