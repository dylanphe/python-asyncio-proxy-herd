import asyncio 

async def main():
    print("1")
    await asyncio.sleep(1) 
    print("2")


if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapse = time.perf_counter() - s 
    print(f"{__file__} executed in {elapse:0.2f} seconds." )