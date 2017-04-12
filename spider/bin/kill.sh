#!/bin/bash


ps aux | grep iqiyi_multi_spider | awk '{print $2;}'| xargs kill -9 
