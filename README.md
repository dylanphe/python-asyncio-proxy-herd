# Asyncio Proxy Server Herd
An application server herd capable of interserver communication built using
Python's asyncio library. (More info can be found in report.pdf)

## Building

Before running the application, Please insert your own Google Places Developer
API key in the assigned area in the source code in order to enable and connect
to the google server. 

## Serving

To run the server simply execute the command below in the directory containing
server.py source code: 

    `python3 server.py {SERVER_ID}`

Notes
-Server_ID can be one of the following, Bernard, Clark, Jaquez, Johnson and
Juzang. 
-To run multiple servers in the herd, you need to start the different in 
different terminal windows or separate  shell session as asyncio is a single
threaded framework. 
-Server are hosted on localhost 127.0.0.1 and the five server ID mentioned
above listen through port 12311 - 12315 respectively.

## Request Commands for 

To send location to the server:

    `IAMAT {Client's ID} {Location} {Time Stamp}`

To query for information about places near other clients' location:

    `WHATSAT {Client's ID} {Radius} {Upper bound limit for search result}
    
