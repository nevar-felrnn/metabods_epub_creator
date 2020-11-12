import argparse
import logging
import os
import requests

from bs4 import BeautifulSoup
from ebooklib import epub

log = logging.getLogger()
log.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())


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
    log.info("Title is: {}".format(title.encode('utf-8')))
    author = soup.find_all('h5')[0].text.strip().replace(u'\xa0', u' ')[3:]
    log.info("Author is: {}".format(author))
    chapter_titles = [x.text.strip() for x in soup.findAll('div', attrs={"class": "alert alert-info xy_alertheader"})][:-1]
    url_links = [x['name'] for x in soup.findAll('a', attrs={"class": "xy_anchor"})][:-3]
    for e in chapter_titles:
        log.info("Found Chapter: {}".format(str(e)))
    log.info("Number of chapters found: {}".format(len(chapter_titles)))
    title_string = title.strip() + " - by " + author
    log.info('Book name is: {}'.format(title_string.encode('utf-8')))
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author(author)
    spine = ['nav']
    for num, z in enumerate(soup.findAll('div', attrs={"class": "xy_partbg p-4"}), start=0):
        try:
            log.info("Adding: {}#{}".format(url, url_links[num]))
            c = epub.EpubHtml(title=chapter_titles[num], file_name=f"chap_{num}.xhtml")
            if num == 0:
                # This is needed to remove the overlay letter from the page    
                # c = pypub.create_chapter_from_string(
                    # "<h1>Part {}</h1>".format(num + 1) + str(
                        # z.find('div', attrs={'class': 'xy_overlaytext'})), title=chapter_titles[num])
                c.content = f"<h1>Part {num + 1}</h1>\n" if chapter_titles[num] else "" + str(
                        z.find('div', attrs={'class': 'xy_overlaytext'}))
            else:
                # c = pypub.create_chapter_from_string("<h1>Part {}</h1>".format(num + 1) + str(
                #     z), title=chapter_titles[num].encode('utf-8'))
                c.content = f"<h1>Part {num + 1}</h1>\n" if chapter_titles[num] else "" + str(
                    z)
            book.add_item(c)
            spine.append(c)
            # book.toc = (epub.Link(f"chap_{num}.xhtml", chapter_titles[num]))
            del (c)
        except ValueError as e:
            raise ValueError(e)
        except IndexError:
            pass
    
    # basic spine
    book.spine = spine
    
    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output = None
    if args.output:
        output = os.path.expanduser(args.output)
    else:
        output = os.getcwd()
    from pdb import set_trace; set_trace()
    epub.write_epub(os.path.join(output, f"{title}.epub"), book)


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-u', '--url', help='URL to parse')
    args.add_argument('-d', '--debug', help='Use debug options', default=False)
    args.add_argument('-o', '--output', help='Output location', default=os.getcwd())
    args = args.parse_args()
    main(args)
