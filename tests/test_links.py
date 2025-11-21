import os
import sys
from bs4 import BeautifulSoup

def test_links():
    broken_links = []
    with open('index.html') as f:
        soup = BeautifulSoup(f, 'html.parser')
        for a in soup.find_all('a', href=True):
            link = a['href']
            if not os.path.exists(link):
                broken_links.append(link)

    if broken_links:
        print('Broken links found:')
        for link in broken_links:
            print(link)

    assert not broken_links, f"Broken links found: {broken_links}"

if __name__ == "__main__":
    test_links()
