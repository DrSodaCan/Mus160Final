import asyncio
import os

from splitter import demucs_split


#Split all

#1: Get folder location
#2: foreach: attempt demucs_split


def get_files(directory):
    try:
        files = os.listdir(directory)
        return [f for f in files if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        return "Directory not found"
    except NotADirectoryError:
        return 0
    except:
        return 1


async def split_all(directory):

    try:
        print("Getting files")
        filenames = get_files(directory)
        if filenames == 0 or filenames == 1:
            print(f"Exception: {filenames}")
            raise Exception
    except:
        print("Could not get files")
        return
    print("Valid files!")


    for item in filenames:
        print(f"Running split operation on {item}")
        await demucs_split(os.path.join(directory, item))
        print(f"{item} finished!\n")


async def main():
    directory = "C:/Users/Atlas/Music/Splitter Project/"
    print("Starting split")
    await split_all(directory)
    print("")
    print("Split done!")

if __name__ == "__main__":
    asyncio.run(main())
