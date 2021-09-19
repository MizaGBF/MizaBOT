import gzip
import io
import json
import time
import sys

def decompress(inputBytes):
    with io.BytesIO() as bio:
        with io.BytesIO(inputBytes) as stream:
            decompressor = gzip.GzipFile(fileobj=stream, mode='r')
            while True:  # until EOF
                chunk = decompressor.read(8192)
                if not chunk:
                    decompressor.close()
                    bio.seek(0)
                    return bio.read().decode("utf-8")
                bio.write(chunk)
            return None

def compress(inputString):
    with io.BytesIO() as bio:
        bio.write(inputString.encode("utf-8"))
        bio.seek(0)
        with io.BytesIO() as stream:
            compressor = gzip.GzipFile(fileobj=stream, mode='w')
            while True:  # until EOF
                chunk = bio.read(8192)
                if not chunk: # EOF?
                    compressor.close()
                    return stream.getvalue()
                compressor.write(chunk)

if __name__ == "__main__":
    if len(sys.argv) >= 1:
        fn = ' '.join(sys.argv[1:])
        ext = fn.split('.')[-1]
        try:
            with open(fn, "rb") as ifstream:
                if ext == 'json':
                    print(f'Compressing "{fn}"')
                    data = compress(ifstream.read().decode('utf-8'))
                    with open(".".join(fn.split(".")[:-1]) + ".gzip", "wb") as ofstream:
                        ofstream.write(data)
                    print('Done')
                elif ext == 'gzip':
                    print(f'Decompressing "{fn}"')
                    data = decompress(ifstream.read())
                    with open(".".join(fn.split(".")[:-1]) + ".json", "w", encoding="utf-8") as ofstream:
                        ofstream.write(data)
                    print('Done')
                else:
                    print(f'Unknown file type "{ext}"')
        except:
            print(f'Error opening file "{fn}"')
    else:
        print('Please drag and drop on save_gzipper.py" either a .json or .gzip file to compress/decompress it')
    print('Closing this prompt in 10 seconds')
    time.sleep(10)

    with open("save.json", "r") as stream:
        data = compressStringToBytes(stream.read())
    with open("out.gzip", "wb") as stream:
        stream.write(data)