import os
from bs4 import BeautifulSoup

def find_html_files(directory):
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.php')):
                html_files.append(os.path.join(root, file))
    return html_files

def fix_links(html_files):
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"Warning: Could not decode file {html_file} as UTF-8. Skipping.")
            continue

        soup = BeautifulSoup(content, 'html.parser')
        modified = False

        # Fix anchor tags
        for a in soup.find_all('a', href=True):
            link = a['href']
            if not link.startswith(('http://', 'https://', '#', 'tel:', 'mailto:')) and 'external.html' not in link:
                resolved_link = os.path.normpath(os.path.join(os.path.dirname(html_file), link))
                if not os.path.exists(resolved_link):
                    # Attempt to find the file in the root of the web directory
                    potential_fix = os.path.join('veralogixgoup', os.path.basename(link))
                    if os.path.exists(potential_fix):
                        new_link = os.path.relpath(potential_fix, os.path.dirname(html_file))
                        a['href'] = new_link
                        modified = True

        # Fix image tags
        for img in soup.find_all('img', src=True):
            src = img['src']
            if not src.startswith(('http://', 'https://', '\"')) and src != '%url%':
                resolved_src = os.path.normpath(os.path.join(os.path.dirname(html_file), src))
                if not os.path.exists(resolved_src):
                    # Attempt to find the file in the root of the web directory
                    potential_fix = os.path.join('veralogixgoup', os.path.basename(src))
                    if os.path.exists(potential_fix):
                        new_src = os.path.relpath(potential_fix, os.path.dirname(html_file))
                        img['src'] = new_src
                        modified = True

        if modified:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"Fixed links in: {html_file}")

if __name__ == "__main__":
    html_files = find_html_files('veralogixgoup')
    fix_links(html_files)
    print("Link fixing process complete.")
