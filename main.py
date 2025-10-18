from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import httpx
from lxml import html
from typing import Optional

app = FastAPI(title="Wikipedia Country Outline API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/api/outline", response_class=PlainTextResponse)
async def get_country_outline(country: str = Query(..., description="Country name")):
    """
    Fetch Wikipedia page for a country and return a Markdown outline of all headings.
    
    Args:
        country: Name of the country (e.g., "Vanuatu", "India", "United States")
    
    Returns:
        Plain text Markdown outline with hierarchical headings
    """
    try:
        # Construct Wikipedia URL
        # Replace spaces with underscores for Wikipedia URL format
        country_url = country.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{country_url}"
        
        # Fetch the Wikipedia page
        async with httpx.AsyncClient() as client:
            response = await client.get(wiki_url, follow_redirects=True)
            response.raise_for_status()
        
        # Parse HTML
        tree = html.fromstring(response.content)
        
        # Extract all headings (h1 to h6) from the main content area
        # Wikipedia main content is in div with id="mw-content-text"
        content_div = tree.xpath('//div[@id="mw-content-text"]')[0]
        
        # Get all heading elements in order
        headings = content_div.xpath('.//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6')
        
        # Build Markdown outline
        markdown_lines = []
        
        # Add "Contents" as the first heading (level 2)
        markdown_lines.append('## Contents')
        
        for heading in headings:
            # Get heading level (h1 -> 1, h2 -> 2, etc.)
            level = int(heading.tag[1])
            
            # Get heading text (clean up edit links and other spans)
            # Use .//text() to get all text content, excluding nested elements like [edit]
            text_parts = heading.xpath('.//span[@class="mw-headline"]//text()')
            
            if not text_parts:
                # Fallback: get all text and clean it
                text = ''.join(heading.xpath('.//text()')).strip()
                # Remove [edit] and other brackets
                text = text.replace('[edit]', '').strip()
            else:
                text = ''.join(text_parts).strip()
            
            if text:
                # Keep original heading levels
                markdown_heading = '#' * level + ' ' + text
                markdown_lines.append(markdown_heading)
        
        # Join all lines with newlines
        markdown_outline = '\n\n'.join(markdown_lines)
        
        return markdown_outline
    
    except httpx.HTTPStatusError as e:
        return f"Error: Could not fetch Wikipedia page for '{country}'. Status code: {e.response.status_code}"
    except IndexError:
        return f"Error: Could not find content on Wikipedia page for '{country}'."
    except Exception as e:
        return f"Error: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Wikipedia Country Outline API",
        "usage": "GET /api/outline?country=<country_name>",
        "example": "/api/outline?country=Vanuatu"
    }

# To run this application:
# 1. Save this file as main.py
# 2. Install dependencies: pip install fastapi uvicorn httpx lxml
# 3. Run: uvicorn main:app --host 0.0.0.0 --port 8000
# 4. Access: http://localhost:8000/api/outline?country=Vanuatu