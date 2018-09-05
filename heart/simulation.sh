#!/bin/sh

if [ "$1" = "" ]; then
	loop="1"
else
	loop="$1" 
fi


time python2.7 ./PseudoHeart.py "$loop"

