#!/bin/bash

dir=`ls $1/test/cache`
for d in $dir
do
	echo --------------------------------------------------------
	echo $d
	cat $1/test/cache/$d/regtest/logs/copernicus.log
done
