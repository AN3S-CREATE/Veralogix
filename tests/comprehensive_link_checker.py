import os
import sys
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

WEBROOT = 'veralogixgoup'

def find_html_files(directory):
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.php')):
                html_files.append(os.path.join(root, file))
    return html_files

def check_links(html_files):
    broken_links = {}
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"Warning: Could not decode file {html_file} as UTF-8. Skipping.")
            continue

        soup = BeautifulSoup(content, 'html.parser')

        # Find all anchor tags
        for a in soup.find_all('a', href=True):
            link = a['href']
            if link.startswith(('http://', 'https://', '#', 'tel:', 'mailto:')) or 'external.html' in link or link == '%url%':
                continue

            link_without_query = link.split('?')[0]

            if link_without_query.startswith('/'):
                # Handle root-relative paths
                resolved_link = os.path.normpath(os.path.join(WEBROOT, link_without_query.lstrip('/')))
            else:
                # Resolve the link path relative to the current file
                resolved_link = os.path.normpath(os.path.join(os.path.dirname(html_file), link_without_query))

            if not os.path.exists(resolved_link):
                if html_file not in broken_links:
                    broken_links[html_file] = []
                broken_links[html_file].append(link)

        # Find all image tags
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith(('http://', 'https://', '\"')) or src == '%url%' or '\"' in src:
                continue

            # Resolve the image path relative to the current file
            resolved_src = os.path.normpath(os.path.join(os.path.dirname(html_file), src))

            if not os.path.exists(resolved_src):
                if html_file not in broken_links:
                    broken_links[html_file] = []
                broken_links[html_file].append(src)

    return broken_links

if __name__ == "__main__":
    html_files = find_html_files('veralogixgoup')
    broken_links = check_links(html_files)

    if broken_links:
        print('Broken links found:')
        for file, links in broken_links.items():
            print(f'  In file: {file}')
            for link in links:
                print(f'    - {link}')
        sys.exit(1)
    else:
        print('All links are valid.')
        sys.exit(0)
