from bs4 import BeautifulSoup

def remove_styling(html_file, output_file):
    # Read the HTML content
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove <style> tags
    for style_tag in soup.find_all('style'):
        style_tag.decompose()
    
    # Remove <link> tags that are stylesheets
    for link_tag in soup.find_all('link', rel='stylesheet'):
        link_tag.decompose()
    
    # Remove inline styles
    for tag in soup.find_all(style=True):
        del tag['style']
    
    # Save the cleaned HTML to a new file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))
    
    print(f"Styling removed. Cleaned HTML saved to {output_file}")

# Replace 'input.html' and 'output.html' with your actual file paths
remove_styling('easy.html', 'clean_easy.html')
