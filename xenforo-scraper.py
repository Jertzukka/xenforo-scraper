import argparse
import os
import sys
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser(description='Process scraper arguments.')
parser.add_argument('url', help='URL to a single thread or a forum category.')
parser.add_argument('-c', '--cookie', help="Optional cookie for the web request.")
parser.add_argument('-o', '--output', help="Optional download output location, must exist.")
parser.add_argument('-nd', '--no-directories', help="Do not create directories for threads.", action="store_true")
parser.add_argument('-e', '--external', help="Follow external files from links", action="store_true")
parser.add_argument('-i', '--ignored', help="Ignore files with this string in URL.", nargs="+")
parser.add_argument('-cn', '--continue', help="Skip threads that already have folders for them.")
args = parser.parse_args()

cookies = {'cookie': args.cookie}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
badchars = (';', ':', '!', '*', '/', '\\', '?', '"', '<', '>', '|')


# Requests the URL and returns a BeautifulSoup object.
def requestsite(url):
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
    except TimeoutError:
        print("Timed out Error.")
        pass
    except Exception as e:
        print("Error on {0}".format(url))
        print(e)
        pass

    if response.status_code != 200:
        print("<{0}> Request Error: {1} - {2}".format(url, response.status_code, response.reason))
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


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
            if "/threads/" in link:
                stripped = link[0:link.rfind('/')+1]
                if base_url + stripped not in threads:
                    threads.append(base_url + stripped)
    return threads


# When given an URL, returns all pages for it, for example -page1, -page2, .. -page40 as an Array.
def getpages(url):
    soup = requestsite(url)

    pagetags = soup.select("li.pageNav-page")
    pagenumbers = []
    for button in pagetags:
        pagenumbers.append(button.text)

    try:
        maxpages = max(pagenumbers)
    except ValueError:
        maxpages = 1

    allpages = []
    for x in range(1, int(maxpages)+1):
        allpages.append("{0}page-{1}".format(url, x))

    return allpages


def gettitle(url):
    soup = requestsite(url)
    title = soup.find("h1", "p-title-value").text
    for char in badchars:
        title = title.replace(char, '_')
    return title


def getoutputpath(title):
    entrypath = []
    if args.output:
        entrypath.append(args.output)
    if not args.no_directories:
        entrypath.append(title)
    return entrypath


# Scrapes a single page, creating a folder and placing images into it.
def scrapepage(url):
    # print("Starting scrape on {0}".format(url))

    soup = requestsite(url)
    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))

    title = gettitle(url)

    # Embedded images
    imgtags = soup.findAll("img")
    files = []
    for image in imgtags:
        src = image.attrs['src']
        if base_url + "/attachments/" in src and "/data/attachments/" not in src and src not in files:
            if '.' in '{uri.path}'.format(uri=urlparse(src)):
                files.append(src)
        if args.external and base_url not in src and src[0:4] == 'http' and src not in files:
            files.append(src)
            #print("Found external image:", src)

    # Embedded videos
    videotags = soup.findAll("video")
    for video in videotags:
        children = video.findChildren("source")
        for node in children:
            src = node.attrs['src']
            if src[0:4] != 'http':
                src = base_url + src
            if base_url + "/data/video/" in src and src not in files:
                files.append(src)
            if args.external and base_url not in src:
                files.append(src)
                #print("Found external video:", src)

    # Attachment files
    # attachmenttags = soup.find_all(href=True)
    # for element in attachmenttags:
    #     src = element['href']
    #     if base_url not in src:
    #         src = base_url + src
    #     if base_url + "/attachments/" in src and "upload" not in src and src not in files:
    #         files.append(src)

    if len(files) > 0:
        path = os.path.join(*getoutputpath(title))
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        except FileNotFoundError:
            print("\nOutput folder does not exist. Please create it manually.")
            print("Attempted output folder:", path)
            sys.exit(1)

    for count, i in enumerate(files, start=1):

        try:
            file = requests.get(i, cookies=cookies, headers=headers, timeout=10)
        except TimeoutError:
            print("Timed out Error.")
            pass
        except Exception as e:
            print("Error on {0}".format(i))
            print(e)
            pass

        # Remove last slash if it exists
        if i[-1] == '/':
            i = i[:-1]
        filename = i[i.rfind('/')+1:len(i)]

        if isignored(filename):
            continue

        truncated = (filename[:70] + '..') if len(filename) > 70 else filename
        fullpath = os.path.join(*getoutputpath(title), truncated)

        if not os.path.exists(fullpath):
            print("\x1b[KProgress: {0}/{1} - Downloading file {2}".format(count, len(files), truncated), end="\r")
            try:
                open(fullpath, 'wb').write(file.content)
            except FileNotFoundError:
                print("\nOutput folder does not exist. Please create it manually.")
                print("Attempted folder:", fullpath)
                sys.exit(1)
        else:
            print("\x1b[KProgress: {0}/{1} - Skipping {2}".format(count, len(files), truncated), end="\r")


# Handles arguments and running the other functions based on given input.
def main():
    # Standardize URL to always end in /.
    if args.url[-1] != '/':
        args.url += '/'

    # Remove all extra parameters from the end such as page, post.
    matches = ("/threads/", "/forums/")
    for each in matches:
        if each in args.url:
            try:
                args.url = args.url[0:args.url.index('/', args.url.index(each)+len(each)) + 1]
            except ValueError:
                pass

    # Input is a forum category, find all threads in this category and scrape them.
    if "/forums/" in args.url:
        allthreads = []
        pages = getpages(args.url)
        # Get all pages on category
        for precount, category in enumerate(pages, start=1):
            print("\x1b[KGetting pages from category.. Current: {0}/{1}\r".format(precount, len(pages)))
            allthreads += getthreads(category)
        # Getting all threads from category pages
        for threadcount, thread in enumerate(allthreads, start=1):
            #title = thread[thread.rfind('/', 0, thread.rfind('/'))+1:len(thread)]
            title = gettitle(thread)
            if os.path.exists(os.path.join(*getoutputpath(title))):
                print("Thread already exists, skipping:", title)
                continue
            pages = getpages(thread)
            # Getting all pages for all threads
            print("\x1b[KThread: {0} - ({1}/{2})".format(title, threadcount, len(allthreads)))
            for pagecount, page in enumerate(pages, start=1):
                print("\x1b[KProgress: Page {0}/{1}".format(pagecount, len(pages)), end="\r")
                scrapepage(page)

    # Input is just one thread, get pages and scrape it.
    if "/threads/" in args.url:
        pages = getpages(args.url)
        title = args.url[args.url.rfind('/', 0, args.url.rfind('/')) + 1:len(args.url)]
        # Getting pages all for this single thread.
        print("\x1b[KThread: {0}".format(title))
        for pagecount, page in enumerate(pages, start=1):
            print("\x1b[KProgress: Page {0}/{1}".format(pagecount, len(pages)), end="\r")
            scrapepage(args.url + "page-" + str(pagecount))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt, Exiting.")
        sys.exit(1)
    print("\nDone!")

sys.exit(0)
