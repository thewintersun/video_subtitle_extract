#!/bin/bash

ps axu | grep download | awk '{print $2;}' | xargs kill -9 

