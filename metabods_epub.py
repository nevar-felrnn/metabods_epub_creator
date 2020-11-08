import argparse
import logging
import os

import pypub
import requests
from bs4 import BeautifulSoup

log = logging.getLogger()
log.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())


# TODO: Output location

def main(args):
    url = args.url
    log.info("Using URL: {}".format(url))
    response = requests.get(url)
    if args.debug:
        if not os.path.exists(url.split('/')[-1]):
            with (url.split('/')[-1], 'w+') as f:
                f.write(response.content)
        else:
            with (url.split('/')[-1], 'r') as f:
                response = f.read()
    soup = BeautifulSoup(response.content, 'html5lib')
    title = soup.find('h1').text
    log.info("Title is: {}".format(title))
    author = soup.find_all('h5')[0].text.strip().replace(u'\xa0', u' ')[3:]
    log.info("Author is: {}".format(author))
    # chapter_titles = soup.findAll('h5', attrs={"class": "modal-title"})[1:]
    chapter_titles = [x.text for x in soup.findAll('div', attrs={"class": "alert alert-info xy_alertheader"})][:-1]
    for e in chapter_titles:
        log.info("Found Chapter: {}".format(str(e.encode('utf-8'))))
    log.info("Number of chapters found: {}".format(len(chapter_titles)))
    title_string = "{} - by {}".format(str(title.encode('utf-8').strip()), author)
    log.info('Book name is: {}'.format(title_string))
    epub = pypub.Epub(title_string, creator=author)
    for num, z in enumerate(soup.findAll('div', attrs={"class": "xy_partbg p-4"}), start=0):
        try:
            assert chapter_titles[num]
            # TODO: URL is no longer correct, need to find method to pull from page
            log.info('Adding: {}#Part_{}'.format(url, num))
            if num == 0:
                # This is needed to remove the overlay letter from the page
                c = pypub.create_chapter_from_string(
                    "<h1>Part {}</h1>".format(num + 1) + str(
                        z.find('div', attrs={'class': 'xy_overlaytext'})), title=chapter_titles[num])
            else:
                c = pypub.create_chapter_from_string("<h1>Part {}</h1>".format(num + 1) + str(
                    z), title=chapter_titles[num])
            epub.add_chapter(c)
            del (c)
        except ValueError as e:
            raise ValueError(e)
        except IndexError:
            pass
    epub.create_epub(os.getcwd(), epub_name=title_string.replace("  ", " "))


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-u', '--url', help='URL to parse')
    args.add_argument('-d', '--debug', help='Use debug options', default=False)
    args = args.parse_args()
    main(args)
