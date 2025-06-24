# Web Scraping and Analysis Project

This project is designed to scrape articles from freshproduce.com, extract their content, and perform analysis using Google's Gemini AI model. The project is organized to handle web scraping, data processing, and AI-powered article analysis in a structured manner.

## Project Structure

```
web-scrapping/
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
├── Makefile                # Project commands
├── README.md               # This file
├── analysis.py             # AI analysis module
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── scrapper.py             # Main web scraping script
├── scrapper_legacy.py      # Legacy version of the scraper
├── data/                   # Output data files
│   ├── analysis_summary.csv      # Final analysis output
│   └── scraped_freshproduce_data.csv  # Raw scraped data
├── csv_temp/               # Temporary CSV files
├── html_temp/              # Temporary HTML debug files
└── scraped_data/           # Legacy scraped data (if any)
```

## Features

- **Web Scraping**: Extracts article data from freshproduce.com using Selenium
- **Content Extraction**: Captures article titles, URLs, categories, descriptions, and full text
- **AI-Powered Analysis**: Uses Google's Gemini AI to generate summaries and extract key topics
- **Incremental Saving**: Automatically saves progress to prevent data loss
- **Error Handling**: Robust error handling and logging
- **Temporary File Management**: Organized storage of temporary files in dedicated directories

## Prerequisites

- Python 3.8+
- Google Cloud account with Vertex AI API enabled
- Chrome browser installed (for Selenium)
- ChromeDriver (matching your Chrome version)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd web-scrapping
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with your Google Cloud credentials:
   ```
   GCP_PROJECT_ID=your-project-id
   GCP_LOCATION=us-central1
   ```

## Usage

### 1. Scrape Articles

To scrape articles from freshproduce.com:

```bash
make scrape
```

Or directly:
```bash
python scrapper.py
```

This will:
- Scrape articles from the Global Trade, Technology, and Food Safety categories
- Save the raw data to `scraped_freshproduce_data.csv`
- Save temporary progress files in the `csv_temp/` directory
- Save debug HTML files in the `html_temp/` directory

### 2. Analyze Articles

To analyze the scraped articles using Google's Gemini AI:

```bash
make analyze
```

Or directly:
```bash
python analysis.py
```

This will:
- Process the scraped articles
- Generate summaries and extract topics using Gemini AI
- Save the analysis results to `analysis_summary.csv`
- Save temporary progress files in the `csv_temp/` directory

### 3. Run Complete Pipeline

To run both scraping and analysis in sequence:

```bash
make run
```

## Makefile Commands

- `make install`: Install project dependencies
- `make freeze`: Update requirements.txt with current dependencies
- `make test`: Run tests (if any)
- `make push`: Push changes to the repository
- `make scrape`: Run the web scraper
- `make analyze`: Run the article analysis
- `make run`: Run both scraping and analysis

## Output Files

- `data/scraped_freshproduce_data.csv`: Raw scraped article data
- `data/analysis_summary.csv`: Processed analysis with AI-generated summaries and topics
- `csv_temp/`: Directory for temporary CSV files
- `html_temp/`: Directory for debug HTML files

## Troubleshooting

1. **ChromeDriver Issues**:
   - Ensure ChromeDriver version matches your Chrome browser version
   - Download from: https://chromedriver.chromium.org/downloads

2. **API Authentication**:
   - Ensure your Google Cloud credentials are properly set up
   - Verify that the Vertex AI API is enabled for your project

3. **Rate Limiting**:
   - The script includes delays to avoid rate limiting
   - If you encounter rate limits, increase the delay in the code

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
