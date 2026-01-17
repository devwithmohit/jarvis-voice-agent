# Web Service

**Language**: Python 3.11+
**Framework**: gRPC (asyncio) + Playwright
**Purpose**: Browser automation and web search integration

## Responsibilities

- Web search (SerpAPI, Bing Search API)
- Browser automation (YouTube, navigation)
- Content extraction from web pages
- Screenshot capture
- Headless browser management

## gRPC Service

Implements `WebService` from `shared/proto/tool.proto`:

- `Search` - Web search with multiple engines
- `NavigateAndExtract` - Navigate to URL and extract content
- `AutomateBrowser` - Automate site-specific actions (YouTube, etc.)
- `Screenshot` - Capture screenshots

## Browser Automation

**Engine**: Playwright (Chromium headless)

**Supported Automation**:

- YouTube: play video, search, pause, volume control
- Google: search, click results
- Generic: navigate, click elements, type text, extract content

**Example**: YouTube Play

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(f"https://youtube.com/watch?v={video_id}")
    await page.click('button[aria-label="Play"]')
```

## Web Search Integration

**Primary**: SerpAPI (Google, Bing, DuckDuckGo)
**Fallback**: Bing Search API

**Search Types**:

- General web search
- News search
- Image search
- Video search

## Content Extraction

**Tools**:

- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML processing
- Playwright - JavaScript-rendered content

**Extraction Modes**:

- `extract_text` - Clean text only (remove HTML tags)
- `extract_links` - All hyperlinks
- `full_html` - Complete HTML source

## Security Considerations

1. **URL Validation**: Block malicious/internal IPs
2. **Rate Limiting**: Max 50 searches/hour per user
3. **Timeout**: 30-second timeout for page loads
4. **Content Filtering**: Block adult/malicious content
5. **Sandboxing**: Browser runs in isolated container

## Dependencies

- `playwright` - Browser automation
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP client for APIs

## Running Locally

```bash
cd services/web-service
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium

python -m app.main
```

## Environment Variables

```
SERPAPI_KEY=your-serpapi-key  # Optional
BING_SEARCH_KEY=your-bing-key  # Optional
PLAYWRIGHT_HEADLESS=true
BROWSER_TIMEOUT=30
MAX_SEARCH_RESULTS=10
```

## Web Search Examples

**Google Search** (via SerpAPI):

```bash
curl -X POST http://localhost:50056/search \
  -d '{"query": "Python async programming", "max_results": 5}'
```

**YouTube Automation**:

```bash
curl -X POST http://localhost:50056/automate \
  -d '{"site": "youtube", "action": "play_video", "parameters": {"video_id": "dQw4w9WgXcQ"}}'
```

## Status

**Phase**: Not yet implemented (Phase 6)
**Next Steps**:

1. Implement SerpAPI integration
2. Build Playwright browser pool
3. Create content extraction pipeline
4. Add YouTube automation actions
5. Implement screenshot capture
6. Add comprehensive error handling and retries
