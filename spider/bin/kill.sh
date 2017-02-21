#!/bin/bash


ps aux | grep iqiyi_spider | awk '{print $2;}'| xargs kill -9 
