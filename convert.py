formats = {"KiB": 1024, "KB": 1000,
           "MiB": 1024**2, "MB": 1000**2,
           "GiB": 1024**3, "GB": 1000**3,
           "TiB": 1024**4, "TB": 1000**4}


# Converts shorthand into number of bytes, ex. 1KiB = 1024
def shortToBytes(short):
    if short is not None:
        for format, multiplier in formats.items():
            if format.lower() in short.lower():
                return int(float(short.lower().replace(format.lower(), ""))*multiplier)
        raise Exception("Incorrect parameters for filesize.")
    else:
        return None


# Converts the number of bytes into shorthand expression, ex. 2500 = 2.5KB
def bytesToShort(bytes):
    reverse = dict(reversed(list(formats.items()))).items()
    for format, multiplier in reverse:
        if bytes/multiplier < 1:
            pass
        else:
            return str(round(bytes/multiplier, 2)) + format


# Run tests only if file is ran as standalone.
if __name__ == '__main__':
    # Tests
    print(shortToBytes("103kib"))
    print(shortToBytes("103GIB"))
    print(shortToBytes("0.5TB"))
    print(bytesToShort(105472))
    print(bytesToShort(110595407872))
    print(bytesToShort(500000000000))
