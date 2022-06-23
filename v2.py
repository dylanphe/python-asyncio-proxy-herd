from datetime import datetime
import time
import asyncio
import argparse 

HOST = '127.0.0.1'
PORTS = {
    'Juzang': 12311,
    'Bernard': 12312,
    'Jaquez': 12313,
    'Johnson': 12314,
    'Clark': 12315,
}
COMM = {
    'Juzang': ['Clark', 'Bernard', 'Johnson' ],
    'Bernard': ['Clark', 'Johnson', 'Juzang', 'Jaquez'],
    'Jaquez' : ['Clark', 'Bernard'],
    'Johnson': ['Juzang', 'Bernard'],
    'Clark' : ['Juzang', 'Jaquez'],
}

def print_log(msg):
    now = datetime.now()
    now_str = now.strftime("%m-%d-%Y %H:%M:%S")
    log.write("[ " + now_str + " ] " + arg.ID + ": " + msg + "\n")
    log.flush()
#Class that define how servers communicate with clients and other servers within the herd.
class HerdServerProtocol(asyncio.Protocol):
    # Constructor
    def __init__(self, id, port):
        self.name = id
        self.port = port
    
    async def handle_connection(self, reader, writer):
        data = await reader.readline()
        name = data.decode()
        greeting = "Hello," + name
        writer.write(greeting.encode())
        await writer.drain()
        writer.close()

# To start server 
async def main():
    #starting server
    print_log("Server is starting...")
    server = await asyncio.start_server(lambda: HerdServerProtocol(arg.ID, PORTS[arg.ID]), HOST, PORTS[arg.ID])
    print_log(f"Server is serving on {server.sockets[0].getsockname()}")
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
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        print_log("Server is shut down.")
        log.close()
