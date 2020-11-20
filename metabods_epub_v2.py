#! /usr/bin/env python3
import argparse
import logging
import os
import urllib

import requests
from bs4 import BeautifulSoup
from ebooklib import epub

log = logging.getLogger()
log.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())


def main(url: str, output: str, debug: bool, series: tuple, dry_run: bool) -> None:
    log.info("Using URL: {}".format(url))
    response = requests.get(url)
    if debug:
        if not os.path.exists(url.split('/')[-1]):
            with (url.split('/')[-1], 'w+') as f:
                f.write(response.content)
        else:
            with (url.split('/')[-1], 'r') as f:
                response = f.read()
    soup = BeautifulSoup(response.content, 'html5lib')
    title = soup.find('h1').text
    log.info("Title is: {}".format(title.encode('utf-8')))
    author = soup.find_all('h5')[0].text.strip().replace(u'\xa0', u' ')[3:]
    log.info("Author is: {}".format(author))
    chapter_titles = [x.text.strip() for x in soup.findAll('div', attrs={"class": "alert alert-info xy_alertheader"})][
                     :-1]
    url_links = [x['name'] for x in soup.findAll('a', attrs={"class": "xy_anchor"})][:-3]
    for e in chapter_titles:
        log.info("Found Chapter: {}".format(str(e)))
    log.info("Number of chapters found: {}".format(len(chapter_titles)))
    title_string = title.strip() + " - by " + author
    log.info('Book name is: {}'.format(title_string.encode('utf-8')))
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author(author)

    # Tried adding series info for calibre, doesn't appear that this data is actually stored in the epub maybe?´
    # if series:
    #     book.add_metadata(namespace="calibre", name='series', value=series[0])
    #     book.add_metadata(namespace="calibre", name='series_index', value=str(series[1]))
    spine = ['nav']
    for num, z in enumerate(soup.findAll('div', attrs={"class": "xy_partbg p-4"}), start=0):
        try:
            log.info("Adding: {}#{}".format(url, url_links[num]))
            c = epub.EpubHtml(title=chapter_titles[num], file_name=f"chap_{num}.xhtml")
            # from pdb import set_trace; set_trace()
            if z.find('div', attrs={'class': 'xy_overlaytext'}):
                # This is needed to remove the overlay letter from the page    
                c.content = (f"<h1>{chapter_titles[num]}</h1>\n" if chapter_titles[num] else "") + str(
                    z.find('div', attrs={'class': 'xy_overlaytext'}))
            else:
                c.content = (f"<h1>{chapter_titles[num]}</h1>\n" if chapter_titles[num] else "") + str(
                    z)
            book.add_item(c)
            spine.append(c)
            # book.toc = (epub.Link(f"chap_{num}.xhtml", chapter_titles[num]))
            del c
        except ValueError as e:
            raise ValueError(e)
        except IndexError:
            pass

    # basic spine
    book.spine = spine

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    if output:
        output = os.path.expanduser(output)
    else:
        output = os.getcwd()
    epub.write_epub(os.path.join(output, f"{title}.epub"), book)


def series_processor(url=None, output=None, debug=None, dry_run=None):
    log.info("Using URL: {}".format(url))
    response = requests.get(url)
    if debug:
        if not os.path.exists(url.split('/')[-1]):
            with (url.split('/')[-1], 'w+') as f:
                f.write(response.content)
        else:
            with (url.split('/')[-1], 'r') as f:
                response = f.read()
    soup = BeautifulSoup(response.content, 'html5lib')
    series_title = (soup.find('h1').text, None)
    if series_title:
        print(f"Series is {series_title}")
    story_list = [x for x in soup.find('ul', attrs={'class': 'list-group list-group-flush'}).findAll('a') if
                  x.attrs['href'].startswith('/mbxy/site/story.php?')]
    for num, story in enumerate(story_list):
        main(url="http://metabods.com" + story['href'], output=output, debug=debug, series=(series_title, num),
             dry_run=dry_run)

if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-u', '--url', help='URL to parse')
    args.add_argument('-d', '--debug', help='Use debug options', default=False)
    args.add_argument('-o', '--output', help='Output location', default=os.getcwd())
    args.add_argument('-y', '--dry-run', help="Dry run the script, don't create any files")
    args = args.parse_args()
    if urllib.parse.urlsplit(args.url).query.startswith('list=series&id='):
        series_processor(url=args.url, output=args.output, debug=args.debug, dry_run=args.dry_run)
    else:
        main(url=args.url, output=args.output, debug=args.debug, dry_run=args.dry_run)
