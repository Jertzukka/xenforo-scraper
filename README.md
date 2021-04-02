## xenforo-scraper

Media scraper for XenForo-based forums written in Python. Supports downloading
images and videos from single thread or from whole forum category. Includes
basic support for printing threads into PDF with pdfkit from wkhtmltopdf.

### Usage

    $ python xenforo-scraper.py url [optional]

    
    positional arguments:
      url                   URL to a single thread or a forum
                            category.
    
    optional arguments:
      -h, --help            show this help message and exit
      -c COOKIE, --cookie COOKIE
                            Optional cookie for the web request.
      -o OUTPUT, --output OUTPUT
                            Optional download output location, must
                            exist.
      -max MAX_FILESIZE, --max-filesize MAX_FILESIZE
                            Set maximum filesize for downloads.
      -min MIN_FILESIZE, --min-filesize MIN_FILESIZE
                            Set minimum filesize for downloads.
      -i IGNORED [IGNORED ...], --ignored IGNORED [IGNORED ...]
                            Ignore files with this string in URL.
      -e, --external        Follow external files from links.
      -nd, --no-directories
                            Do not create directories for threads.
      -cn, --continue       Skip threads that already have folders
                            for them.
      -p, --pdf             Print pages into PDF.
      -ni, --no-images      Don't download images.
      -nv, --no-videos      Don't download videos.


### Notes
- Cookie is expected in format: `cookie1=value1; cookie2=value2`, which is
available from browser developer tools.
- Dependency `wkhtmltopdf` only required if PDF is printed. 
- Filesizes supports both SI and IEC base units, ex. `2KB`, `5.2MiB`.
- `--ignored` supports multiple arguments, leave it last.
