MAPS_API_KEY = 'your_key'
MAPS_API_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
from datetime import datetime
import time
import asyncio
import argparse
import aiohttp
import json

HOST = '127.0.0.1'
PORTS = {
    'Bernard': 12311,
    'Clark': 12312,
    'Jaquez': 12313,
    'Johnson': 12314,
    'Juzang': 12315
}
COMM = {
    'Bernard': ['Jaquez', 'Johnson', 'Juzang'],
    'Clark' : ['Jaquez', 'Juzang'],
    'Jaquez' : ['Bernard', 'Clark'],
    'Johnson': ['Bernard', 'Juzang'],
    'Juzang': ['Bernard', 'Clark', 'Johnson']
}

# Print to log file.
def print_log(msg):
    now = datetime.now()
    time_str = now.strftime("%m-%d-%Y %H:%M:%S")
    log.write("[ " + time_str + " ] " + arg.ID + ": " + msg + "\n")
    log.flush()

# Class that define how servers communicate with clients and other servers within the herd.
class ServerProtocol(asyncio.Protocol):
    # Dict to store client recent info
    clients_recent_loc = {}

    # Constructor
    def __init__(self, id, port):
        self.server_name = id
        self.port = port

    # Handle connection to client
    async def handle_connection(self, reader, writer):
        encoded_req = await reader.readline()
        recieved_time = time.time()
        decoded_req = encoded_req.decode() 
        #If there's a request sent from client 
        if (decoded_req.strip()):  
            print_log(f"Request received - {decoded_req.strip()}")
            req = decoded_req.strip().split()
            at_req = decoded_req.strip()
            res = await self.handle_req(req, recieved_time, at_req)
            if res != None:
                if req[0] != "AT":
                    writer.write(res.encode())
                    await writer.drain()
                writer.close()
            else:
                writer.close()
        else:
            writer.close()

    # Generate response for IAMAT command 
    async def handle_IAMAT(self, req, recieved_time):
        client_id = req[1]
        client_coordinate = req[2]
        client_time = req[3]
        time_diff = str(float(recieved_time) - float(client_time))
        if (time_diff[0] != '-'):
            time_diff = f"+{time_diff}"
        # Store rec loc for WHATSAT command
        ServerProtocol.clients_recent_loc[client_id] = [client_coordinate, client_time, time_diff, self.server_name]
        # response to IAMAT
        IAMAT_res = f"AT {self.server_name} {time_diff} {client_id} {client_coordinate} {client_time}\n"
        print_log(f"Response sent - {IAMAT_res.rstrip()}")
        # Flood and Propagate the server location to other servers
        await self.flood(IAMAT_res.strip())
        return IAMAT_res
    
    # Generate response for WHATSAT command 
    async def handle_WHATSAT(self, req):
        client_id = req[1]
        rec_list = ServerProtocol.clients_recent_loc[req[1]]
        client_coordinate =  rec_list[0]
        client_time =  rec_list[1]
        time_diff =  rec_list[2]
        old_server =  rec_list[3]
        #convert rad to meters
        rad = str(int(float(req[2]) * 1000))
        up_bound = int(req[3])
        for i in range(1, len(client_coordinate)):
            if client_coordinate[i] in ["+", "-"]:
                lat = float(client_coordinate[:i])
                lng = float(client_coordinate[i:])
        QUERY_res = await self.query_places(lat, lng, rad, up_bound)
        # response to WHATSAT
        WHATSAT_res = f"AT {old_server} {time_diff} {client_id} {client_coordinate} {client_time}\n{QUERY_res}\n\n"
        print_log(f"Response sent - {WHATSAT_res.rstrip()}")
        return WHATSAT_res
    
    # Send Google HTTP request to GOOGLE PLACE using Google API
    # Inspiration: https://pypi.org/project/aiohttp/
    # Inspiration: https://www.w3schools.com/python/python_json.asp
    async def query_places(self, lat, lng, rad, up_bound):
        print_log(f"Querying Google Places For Nearby Locations")
        async with aiohttp.ClientSession() as session:
            gp_url=f"{MAPS_API_URL}?location={lat},{lng}&radius={rad}&key={MAPS_API_KEY}"
            async with session.get(gp_url) as response:
                query_res = await response.text()
            # Parse query_res
            obj = json.loads(query_res)
            # Limit search result
            obj["results"] = (obj["results"])[:up_bound]
            return json.dumps(obj, indent=4, sort_keys=True).rstrip()

    # Generate response for AT command 
    async def handle_AT(self, req, at_req):
        # Parse AT Command
        main_server = req[1]
        time_diff = req[2]
        client_id = req[3]
        coordinate = req[4]
        client_time = float(req[5])
        # Check if client has already announced his or her location
        if client_id in ServerProtocol.clients_recent_loc.keys():
            # Update the location only if it is the most recent location by checking the time provided by the client
            if client_time > float(ServerProtocol.clients_recent_loc[client_id][1]):
                print_log("Updating existing client's location")
                ServerProtocol.clients_recent_loc[client_id] = [coordinate, client_time, time_diff, main_server]
                await self.flood(at_req)
            else:
                print_log(f"{client_id}'s location is up-to-date")
        else:
            print_log("Initialize new client's location")
            ServerProtocol.clients_recent_loc[client_id] = [coordinate, client_time, time_diff, main_server]
            await self.flood(at_req)

    # Flood the client's location to other running servers
    async def flood(self, at_req):
        client_id = (at_req.split())[3]
        for server in COMM[self.server_name]:
            try:
                reader, writer = await asyncio.open_connection(HOST, PORTS[server])
                print_log(f"Connected to {server}")
                writer.write(at_req.encode())
                await writer.drain()
                print_log(f"Updating {client_id}'s location to server {server}")
                print_log(f"{server} - {self.clients_recent_loc}")
                print_log(f"Connection Dropped with {server}")
                await writer.drain()
                writer.close()
            except:
                # Catch connection error exception if the server is not running
                print_log(f"Error: Cannot connect to server: {server}")

    # Handle resquests from client
    async def handle_req(self, req, recieved_time, at_req):
        # Validate IAMAT command
        if req[0] == "IAMAT":
            # Check if it is the command IAMAT
            if len(req) != 4:
                print_log("Error: IAMAT - Invalid arguments.")
                return
            # Check if the coordinate provided is in correct format
            coordinate = req[2]
            total_syms = (sum(map(lambda x: 1 if x in ['+', '-'] else 0, coordinate))) 
            if total_syms == 2:
                # Extract the lng and lat from the given coord
                if coordinate[0] in ['+', '-']:
                    for i in range(1, len(coordinate)):
                        if coordinate[i] in ["+", "-"]:
                            # Check if lat and lng are valid
                            if abs(float(coordinate[:i])) > 90 or abs(float(coordinate[:i])) < -90:
                                print_log("Error: IAMAT - Latitude(-90 to +90) is out of range.")
                                return
                            if abs(float(coordinate[i:])) < -180 or abs(float(coordinate[i:])) > 180:
                                print_log("Error: IAMAT - Longitude(-180 to +180) is out of range.")
                                return              
            else:
                print_log("Error: IAMAT -  Invalid coordination format.")
                return 
            # Check if timestamp given is valid (float)
            try: 
                isinstance(float(req[3]), float)
            except ValueError:
                print_log("Error: IAMAT - Time Stamp is not valid.")
                return 
            return await self.handle_IAMAT(req, recieved_time)

        # Validate WHATSAT command
        elif req[0] == "WHATSAT":
            # Check if it is the query WHATSAT
            if len(req) != 4:
                print_log("Error: WHATSAT - Invalid arguments.")
                return
            # Check if the client ever announce his or her location
            try: 
                ServerProtocol.clients_recent_loc[req[1]]
            except KeyError:
                print_log(f"Error: WHATSAT - {req[1]}'s location is unknown.")
                return
            try: 
                rad = isinstance(float(req[2]), float)
                up_bound = isinstance(int(req[3]), int)
            except ValueError:
                print_log("Error: WHATSAT - Invalid Radius and Upper Bound Value.")
                return
            if float(req[2]) > 50 or float(req[2]) < 0:
                print_log("Error: WHATSAT - Radius provided is out of range.")
                return
            if int(req[3]) > 20 or int(req[3]) < 0:
                print_log("Error: WHATSAT - Upper Bound provided is out of range. ")
                return
            return await self.handle_WHATSAT(req)
        
        # Validate AT command
        # AT {SERVER_ID} {TIME_DIFF} {CLIENT_ID} {COORDINATE} {TIME_SENT} 
        elif req[0] == "AT":
            # Check if it is the AT command
            if len(req) != 6:
                print_log("Error: AT - Invalid arguments.")
                return
            # Check if SERVER_ID is valid
            if req[1] not in PORTS.keys():
                print_log("Error: AT - Server_ID does not exist.")
                return
            # Check if the coordinate provided is in correct format
            coordinate = req[4]
            total_syms = (sum(map(lambda x: 1 if x in ['+', '-'] else 0, coordinate))) 
            if total_syms == 2:
                # Extract the lng and lat from the given coord
                if coordinate[0] in ['+', '-']:
                    for i in range(1, len(coordinate)):
                        if coordinate[i] in ["+", "-"]:
                            # Check if lat and lng are valid
                            if abs(float(coordinate[:i])) > 90 or abs(float(coordinate[:i])) < -90:
                                print_log("Error: IAMAT - Latitude(-90 to +90) is out of range.")
                                return
                            if abs(float(coordinate[i:])) < -180 or abs(float(coordinate[i:])) > 180:
                                print_log("Error: IAMAT - Longitude(-180 to +180) is out of range.")
                                return 
            # Check if timestamp given is valid
            try: 
                isinstance(float(req[5]), float)
            except ValueError:
                print_log("Error: AT - Time Stamp is not valid.")
                return
            return await self.handle_AT(req, at_req)
        else: 
            print_log(f"Error: \"{at_req.strip()}\" is an invalid command")
            return f"? {at_req}"
            
    # To start server 
    async def serve(self):
        #starting server
        print_log("Server is starting...")
        server = await asyncio.start_server(self.handle_connection, HOST, self.port)
        #serving server
        async with server:
            await server.serve_forever()
        server.close()        

if __name__ == "__main__":
    # Positional arg to parse for server name.
    parser = argparse.ArgumentParser()
    parser.add_argument("ID", type=str, help="Name of the server", choices=["Juzang", "Bernard", "Johnson", "Jaquez", "Clark"])
    arg = parser.parse_args()
    # Creating a log file
    log = open("./logs/" + arg.ID + "-server.log", mode='w')
    # Starting the server
    server = ServerProtocol(arg.ID, PORTS[arg.ID])
    try: 
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print_log("Server is shutting down...")
        log.close()
