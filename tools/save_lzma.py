import lzma
import io
import json
import time
import sys

def decompress(inputBytes):
    with io.BytesIO() as bio:
        with io.BytesIO(inputBytes) as stream:
            decompressor = lzma.LZMADecompressor()
            while not decompressor.eof:  # until EOF
                chunk = decompressor.decompress(stream.read(8192), max_length=8192)
                if decompressor.eof:
                    if len(chunk) > 0: bio.write(chunk)
                    bio.seek(0)
                    return bio.read().decode("utf-8")
                bio.write(chunk)
            return None

def compress(inputString):
    with io.BytesIO() as bio:
        bio.write(inputString.encode("utf-8"))
        bio.seek(0)
        buffers = []
        with io.BytesIO() as stream:
            compressor = lzma.LZMACompressor()
            while True:  # until EOF
                chunk = bio.read(8192)
                if not chunk: # EOF?
                    buffers.append(compressor.flush())
                    return b"".join(buffers)
                buffers.append(compressor.compress(chunk))

if __name__ == "__main__":
    if len(sys.argv) >= 1:
        fn = ' '.join(sys.argv[1:])
        ext = fn.split('.')[-1]
        try:
            with open(fn, "rb") as ifstream:
                if ext == 'json':
                    print(f'Compressing "{fn}"')
                    data = compress(ifstream.read().decode('utf-8'))
                    with open(".".join(fn.split(".")[:-1]) + ".lzma", "wb") as ofstream:
                        ofstream.write(data)
                    print('Done')
                elif ext == 'lzma':
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
        print('Please drag and drop on save_lzma.py" either a .json or .lzma file to compress/decompress it')
    print('Closing this prompt in 10 seconds')
    time.sleep(10)