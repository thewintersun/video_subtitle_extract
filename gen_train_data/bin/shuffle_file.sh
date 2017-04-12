#!/bin/bash

awk 'BEGIN{
    srand()
  }
  {
    a = rand()NR;
    b[a]=$0
  }END{
    for(x in b)
      print b[x]
  }' $1

