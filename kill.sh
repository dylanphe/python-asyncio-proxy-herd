#!/bin/bash

kill $( lsof -i:12311 -t ) & kill $( lsof -i:12312 -t ) & kill $( lsof -i:12313 -t ) & kill $( lsof -i:12314 -t ) & kill $( lsof -i:12315 -t )
