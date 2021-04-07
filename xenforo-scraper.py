import argparse
import os
import sys
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from convert import shortToBytes, bytesToShort

parser = argparse.ArgumentParser(description='Process scraper arguments.')
parser.add_argument('url', help='URL to a single thread or a forum category.')
parser.add_argument('-c', '--cookie', help="Optional cookie for the web request.")
parser.add_argument('-o', '--output', help="Optional download output location, must exist.")
parser.add_argument('-max', '--max-filesize', help="Set maximum filesize for downloads.")
parser.add_argument('-min', '--min-filesize', help="Set minimum filesize for downloads.")
parser.add_argument('-i', '--ignored', help="Ignore files with this string in URL.", nargs="+")
parser.add_argument('-e', '--external', help="Follow external files from links.", action="store_true")
parser.add_argument('-nd', '--no-directories', help="Do not create directories for threads.", action="store_true")
parser.add_argument('-cn', '--continue', help="Skip threads that already have folders for them.", dest="cont",
                    action="store_true")
parser.add_argument('-p', '--pdf', help="Print pages into PDF.", action="store_true")
parser.add_argument('-ni', '--no-images', help="Don't download images.", action="store_true")
parser.add_argument('-nv', '--no-videos', help="Don't download videos.", action="store_true")
parser.add_argument('-d', '--debug', help=argparse.SUPPRESS, action="store_true")
args = parser.parse_args()

cookies = {'cookie': args.cookie}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/39.0.2171.95 Safari/537.36'}
badchars = (';', ':', '!', '*', '/', '\\', '?', '"', '<', '>', '|')
totaldownloaded = 0
timestamp = 0


# Convert filesizes from shorthand to bytes if arguments are given.
if args.max_filesize or args.min_filesize:
    maxsize = shortToBytes(args.max_filesize)
    minsize = shortToBytes(args.min_filesize)
    if args.debug:
        print(f"File sizes: Max: {bytesToShort(maxsize)}, Min: {bytesToShort(minsize)}")
else:
    maxsize = None
    minsize = None


# Import and prepare cookies for PDF printing.
if args.pdf:
    import pdfkit
    cookielist = []
    if args.cookie:
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        cookie.load(args.cookie)
        for key, morsel in cookie.items():
            cookielist.append((key, morsel.value))


# Requests the URL and returns a BeautifulSoup object.
def requestsite(url):
    if args.debug:
        print("Requesting URL:", url)
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"<{url}> Request Error: {response.status_code} - {response.reason}")
    except TimeoutError:
        print("Timed out Error.")
        pass
    except Exception as e:
        print(f"Error on {url}")
        print(e)
        pass
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


# Function for checking if filename includes any ignored words
def isignored(filename):
    for name in args.ignored:
        if name in filename:
            return True
    return False


# When given a forum category page, returns all threads on that page. Returns an array of all links.
def getthreads(url):
    soup = requestsite(url)
    threadtags = soup.find_all(class_="structItem-title")
    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
    threads = []
    for x in threadtags:
        y = x.find_all(href=True)
        for element in y:
            link = element['href']
            if "threads/" in link:
                stripped = link[0:link.rfind('/') + 1]
                if base_url + stripped not in threads:
                    threads.append(base_url + stripped)
    return threads


# When given an URL, returns all pages for it, for example -page1, -page2, .. -page40 as an Array.
def getpages(soup, url):
    pagetags = soup.select("li.pageNav-page")
    pagenumbers = []
    for button in pagetags:
        pagenumbers.append(button.text)

    try:
        maxpages = max(pagenumbers)
    except ValueError:
        maxpages = 1

    allpages = []
    for x in range(1, int(maxpages) + 1):
        allpages.append(f"{url}page-{x}")
    return allpages


# Inputs a soup-object and returns the title of the thread
def gettitle(soup):
    title = soup.find("h1", "p-title-value").text
    for char in badchars:
        title = title.replace(char, '_')
    return title


# Inputs a title, and returns a path depending on given --output parameter and --no-directories.
def getoutputpath(title):
    entrypath = []
    if args.output:
        entrypath.append(args.output)
    if not args.no_directories:
        entrypath.append(title)
    return entrypath


# Scrapes a single page, creating a folder and placing images into it.
def scrapepage(url):
    soup = requestsite(url)
    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
    title = gettitle(soup)
    path = os.path.join(*getoutputpath(title))
    files = []



    # Embedded images
    if not args.no_images:
        imgtags = soup.findAll("img")
        for image in imgtags:
            src = image.attrs['src']
            if base_url in src and "attachments/" in src and "data/attachments/" not in src and src not in files:
                if '.' in '{uri.path}'.format(uri=urlparse(src)):
                    files.append(src)
            if args.external and base_url not in src and src.startswith('http') and src not in files:
                files.append(src)

    # Embedded videos
    if not args.no_videos:
        videotags = soup.findAll("video")
        for video in videotags:
            children = video.findChildren("source")
            for node in children:
                src = node.attrs['src']
                if not src.startswith('http'):
                    src = base_url + src
                if base_url in src and "video/" in src and src not in files:
                    files.append(src)
                if args.external and base_url not in src:
                    files.append(src)

    # Media
    attachmenttags = soup.find_all(href=True)
    for element in attachmenttags:
        src = element['href']
        fullimage = src + "full/"
        if "media/" in src and base_url in src and fullimage not in files:
            files.append(fullimage)

    if args.debug:
        print(files)

    if len(files) > 0 or args.pdf:
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        except FileNotFoundError:
            print("\nOutput folder does not exist. Please create it manually.")
            print("Attempted output folder:", path)
            sys.exit(1)

    if args.pdf:
        pagenumber = url[url.rfind('page'):len(url)]
        pdfkit.from_url(url, os.path.join(path, pagenumber + '.pdf'), options={'cookie': cookielist})

    for count, i in enumerate(files, start=1):

        # Remove last slash if it exists
        if i[-1] == '/':
            filename = i[:-1]
        else:
            filename = i

        # Remove /full ending
        if filename.endswith("/full"):
            filename = filename[:-5]

        # Set everything after last / as filename
        filename = filename[filename.rfind('/') + 1:len(filename)]

        if args.ignored is not None and isignored(filename):
            continue

        truncated = (filename[:60] + '..') if len(filename) > 60 else filename
        fullpath = os.path.join(*getoutputpath(title), filename)

        if args.debug:
            print("Saving to:", fullpath)

        if not os.path.exists(fullpath):
            try:
                req = requests.get(i, stream=True, cookies=cookies, headers=headers, timeout=10)
                filesize = int(req.headers['Content-length'])
                if (maxsize is None or (maxsize is not None and filesize <= maxsize)) and (
                        minsize is None or (minsize is not None and filesize >= minsize)):
                    global totaldownloaded
                    global timestamp
                    difference = time.time() - timestamp
                    print(
                        f"\x1b[KSpeed: {bytesToShort(totaldownloaded / difference)}/s Progress: {count}/{len(files)}"
                        f" - DL: {truncated} ({bytesToShort(filesize)})", end="\r")
                    with open(fullpath, 'wb') as file:
                        for chunk in req.iter_content(chunk_size=4096):
                            file.write(chunk)
                    totaldownloaded += filesize
                else:
                    print(
                        f"\x1b[KProgress: {count}/{len(files)} - Wrong filesize {truncated} ({bytesToShort(filesize)})",
                        end="\r")

            except Exception as e:
                if args.debug:
                    print(f"Error on {i}, Reason {e}")
                pass
        else:
            print(f"\x1b[KProgress: {count}/{len(files)} - Skipping {truncated}", end="\r")


# Handles and launches other functions based on URL.
def main():

    # Standardize URL to always end in /.
    if args.url[-1] != '/':
        args.url += '/'

    # Remove all extra parameters from the end such as page, post.
    matches = ("threads/", "forums/")
    for each in matches:
        if each in args.url:
            try:
                args.url = args.url[0:args.url.index('/', args.url.index(each) + len(each)) + 1]
            except ValueError:
                pass

    # Input is a forum category, find all threads in this category and scrape them.
    if "forums/" in args.url:
        allthreads = []
        pages = getpages(requestsite(args.url), args.url)

        # Get all pages on category
        for precount, category in enumerate(pages, start=1):
            print(f"\x1b[KGetting pages from category.. Current: {precount}/{len(pages)}\r")
            allthreads += getthreads(category)

        # Getting all threads from category pages
        for threadcount, thread in enumerate(allthreads, start=1):
            soup = requestsite(thread)
            pages = getpages(soup, thread)
            title = gettitle(soup)
            truncated = (title[:75] + '..') if len(title) > 75 else title

            global totaldownloaded
            global timestamp
            totaldownloaded = 0
            timestamp = time.time()
            if args.cont and os.path.exists(os.path.join(*getoutputpath(title))):
                    print("Thread already exists, skipping:", truncated)
                    continue
            print(f"\x1b[KThread: {truncated} - ({threadcount}/{len(allthreads)})")

            # Getting all pages for all threads
            for pagecount, page in enumerate(pages, start=1):
                print(f"\x1b[KProgress: Page {pagecount}/{len(pages)}", end="\r")
                scrapepage(page)

    # Input is just one thread, get pages and scrape it.
    if "threads/" in args.url:
        soup = requestsite(args.url)
        pages = getpages(soup, args.url)
        title = gettitle(soup)

        # Getting pages all for this single thread.
        print("\x1b[KThread: {0}".format(title))
        for pagecount, page in enumerate(pages, start=1):
            print(f"\x1b[KProgress: Page {pagecount}/{len(pages)}", end="\r")
            scrapepage(args.url + "page-" + str(pagecount))


# Launch main function on file run and handle keyboard interrupt.
try:
    main()
except KeyboardInterrupt:
    print("\nKeyboard interrupt, Exiting.")
    sys.exit(1)
print("\nDone!")
sys.exit(0)
