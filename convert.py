formats = {"KiB": 1024, "KB": 1000,
           "MiB": 1024**2, "MB": 1000**2,
           "GiB": 1024**3, "GB": 1000**3,
           "TiB": 1024**4, "TB": 1000**4}


# Converts shorthand into number of bytes, ex. 1KiB = 1024
def shortToBytes(short):
    if short is not None:
        try:
            for format, multiplier in formats.items():
                if format.lower() in short.lower():
                    return int(float(short.lower().replace(format.lower(), ""))*multiplier)
            raise Exception("No match found for unit multipliers ex. KiB, MB.")
        except AttributeError:
            raise Exception("Shorthand must be a string, not integer.")
    else:
        return None


# Converts the number of bytes into shorthand expression, ex. 2500 = 2.5KB
def bytesToShort(bytes):
    reverse = dict(reversed(list(formats.items()))).items()
    for format, multiplier in reverse:
        try:
            if bytes/multiplier > 1:
                return str(round(bytes/multiplier, 2)) + format
        except TypeError:
            raise Exception("Bytes must be an integer.")


# Run tests only if file is ran as standalone.
if __name__ == '__main__':
    # Tests
    import pytest
    assert shortToBytes("103kib") == 105472
    assert shortToBytes("103GIB") == 110595407872
    assert shortToBytes("0.5TB") == 500000000000
    assert bytesToShort(105472) == "105.47KB"
    assert bytesToShort(110595407872) == "110.6GB"
    assert bytesToShort(500000000000) == "500.0GB"
    with pytest.raises(Exception):
        print(bytesToShort("k2jfzsk2"))
    with pytest.raises(Exception):
        print(shortToBytes("ad2wd2"))
    with pytest.raises(Exception):
        print(shortToBytes(25252))
