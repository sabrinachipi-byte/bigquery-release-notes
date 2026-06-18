from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re

app = Flask(__name__)

# Namespace for Atom feed
NAMESPACE = {'atom': 'http://www.w3.org/2005/Atom'}

def parse_release_notes(xml_content):
    """Parse the Atom feed and extract release notes entries."""
    root = ET.fromstring(xml_content)
    entries = []
    
    for entry in root.findall('atom:entry', NAMESPACE):
        title = entry.find('atom:title', NAMESPACE)
        if title is not None:
            title = title.text
        else:
            title = "Untitled"
            
        entry_id = entry.find('atom:id', NAMESPACE)
        if entry_id is not None:
            entry_id = entry_id.text
        else:
            entry_id = ""
            
        updated = entry.find('atom:updated', NAMESPACE)
        if updated is not None:
            try:
                # Parse ISO 8601 date
                dt = datetime.fromisoformat(updated.text.replace('Z', '+00:00'))
                updated = dt.strftime('%B %d, %Y')
            except:
                updated = updated.text
        else:
            updated = ""
            
        link = entry.find('atom:link', NAMESPACE)
        if link is not None:
            href = link.get('href')
        else:
            href = ""
            
        content = entry.find('atom:content', NAMESPACE)
        if content is not None and content.text:
            # Extract text from HTML content, strip tags
            text = content.text
            # Remove CDATA wrapper if present
            if text.startswith('<![CDATA[') and text.endswith(']]>'):
                text = text[9:-3]
            # Strip HTML tags but keep basic formatting
            text = re.sub(r'<[^>]+>', ' ', text)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
        else:
            text = ""
            
        entries.append({
            'title': title,
            'id': entry_id,
            'date': updated,
            'link': href,
            'content': text,
            # For tweet: include title and a short snippet
            'tweet_text': f"{title}: {text[:200]}{'...' if len(text) > 200 else ''}"
        })
    
    return entries

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/notes')
def get_notes():
    """Fetch and return the release notes as JSON."""
    try:
        url = 'https://docs.cloud.google.com/feeds/bigquery-release-notes.xml'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        entries = parse_release_notes(response.text)
        
        return jsonify({
            'success': True,
            'entries': entries,
            'updated': datetime.now().strftime('%B %d, %Y %I:%M %p')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
