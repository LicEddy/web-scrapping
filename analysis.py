import pandas as pd
import vertexai
from vertexai.generative_models import GenerativeModel
import json
import time
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArticleAnalyzer:
    def __init__(self, project_id: str = None, location: str = None):
        """
        Initialize the Article Analyzer with GCP Vertex AI
        
        Args:
            project_id: Your GCP project ID (will use env var if not provided)
            location: GCP region for Vertex AI (will use env var if not provided)
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.location = location or os.getenv('GCP_LOCATION', 'us-central1')
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be provided either as parameter or environment variable")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize Gemini model
        self.model = GenerativeModel("gemini-2.5-pro")
        
        logger.info(f"Initialized ArticleAnalyzer for project {self.project_id}")
    
    def analyze_article(self, article_text: str, max_retries: int = 3) -> Dict:
        """
        Analyze a single article using Gemini API
        
        Args:
            article_text: Full text of the article
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing summary and topics
        """
        # Handle empty or very short articles
        if not article_text or len(article_text.strip()) < 50:
            return {"summary": "Article text is too short or empty", "topics": []}
        
        prompt = f"""

        You're a senior data analyst with a strong background in data analysis and business intelligence. 
        So you know how to communicate strong and complicated insights in a way any business man with no tech background can understand.

        Task: Analyze the following article and provide a summary.

        Taks details:
        1. Create a concise one-sentence summary that captures the main point, it must be at least 15 words and no more than 25.
        2. Identify 3-5 primary topics or keywords that best represent the content
        3. Focus on the most important themes and concepts

        Please respond in valid JSON format:
        {{
            "summary": "Your one-sentence summary here",
            "topics": ["topic1", "topic2", "topic3", "topic4", "topic5"]
        }}

        Example: 

        Article example: 
        
        The supermarket floral department continues to drive sales for supermarkets. While dollar and unit growth have stabilized from the spike during the pandemic, the department is experiencing dollar sales growth and unit growth, according to Circana. This signals that even though consumers are dealing with financial struggles, flowers remain an important part of life.

        The floral department reduced its gross margin to 46% and is keeping shrink at 9%. The floral department is 1.3% of store sales, up from 1.2% in 2023.
        
        Summary example: 

        {{
            "Summary": Flowers remain essential for consumers, showing sales growth and store share increase despite economic challenges.
            "Topics": ["Flowers", "Supermarkets", "Sales", "Growth", "Economic struggles"]
        }}
        
        Readl Article text to analyze:
        {article_text}
        """
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,  # Lower temperature for more consistent output
                        "top_p": 0.8,
                        "max_output_tokens": 10000,
                    }
                )
                
                # Extract and clean response text
                response_text = response.text.strip()
                
                # Clean up markdown formatting
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                # Parse JSON
                try:
                    result = json.loads(response_text)
                    
                    # Validate the response structure
                    if 'summary' in result and 'topics' in result:
                        # Ensure topics is a list
                        if isinstance(result['topics'], list):
                            return {
                                "summary": str(result['summary']).strip(),
                                "topics": [str(topic).strip() for topic in result['topics']]
                            }
                    
                    # If structure is invalid, try manual extraction
                    return self._extract_manually(response_text)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}. Attempting manual extraction.")
                    return self._extract_manually(response_text)
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for article analysis")
                    return {"summary": "Analysis failed due to API error", "topics": []}
        
        return {"summary": "Analysis failed", "topics": []}
    
    def _extract_manually(self, response_text: str) -> Dict:
        """
        Manually extract summary and topics if JSON parsing fails
        """
        try:
            summary = ""
            topics = []
            
            # Try to find summary and topics in the response
            lines = response_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for summary
                if any(keyword in line.lower() for keyword in ['summary', 'main point']) and ':' in line:
                    summary = line.split(':', 1)[1].strip().strip('"\'')
                
                # Look for topics
                elif 'topics' in line.lower():
                    # Try to find the topics in this line or subsequent lines
                    if '[' in line and ']' in line:
                        topics_str = line[line.find('['):line.find(']')+1]
                        try:
                            topics = json.loads(topics_str)
                        except:
                            # Try to extract topics as comma-separated values
                            topics_str = topics_str.strip('[]')
                            topics = [t.strip().strip('"\'') for t in topics_str.split(',')]
                    elif '[' in line:
                        # Topics might span multiple lines
                        topics_lines = [line]
                        for j in range(i+1, min(i+5, len(lines))):
                            topics_lines.append(lines[j])
                            if ']' in lines[j]:
                                break
                        
                        topics_str = ' '.join(topics_lines)
                        topics_str = topics_str[topics_str.find('['):topics_str.find(']')+1]
                        try:
                            topics = json.loads(topics_str)
                        except:
                            topics = []
            
            # Fallback: extract any quoted strings as potential topics
            if not topics:
                import re
                quoted_strings = re.findall(r'"([^"]*)"', response_text)
                if quoted_strings:
                    topics = quoted_strings[:5]  # Take first 5 as topics
            
            return {
                "summary": summary if summary else "Could not extract summary",
                "topics": topics if topics else ["extraction", "failed"]
            }
            
        except Exception as e:
            logger.error(f"Manual extraction failed: {e}")
            return {"summary": "Manual extraction failed", "topics": ["error"]}
    
    def process_csv(self, input_csv_path: str = None, output_csv_path: str = None):
        """
        Process the entire CSV file and generate enriched analysis
        """
        # Use environment variables if paths not provided
        # input_csv_path = input_csv_path or os.getenv('INPUT_CSV_PATH', os.path.join('data', 'scraped_freshproduce_data.csv'))
        input_csv_path = 'data/scraped_freshproduce_data.csv'

        # output_csv_path = output_csv_path or os.getenv('OUTPUT_CSV_PATH', 'analysis_summary.csv')
        output_csv_path = 'data/analysis_summary.csv'
        
        try:
            # Read the CSV file
            df = pd.read_csv(input_csv_path)
            logger.info(f"Loaded {len(df)} articles from {input_csv_path}")
            
            # Display column names to help with debugging
            logger.info(f"Available columns: {list(df.columns)}")
            
            # Try to find the text column (common names)
            text_column = None
            possible_text_columns = ['FullArticleText', 'full_text', 'article_text', 'content', 'text']
            
            for col in possible_text_columns:
                if col in df.columns:
                    text_column = col
                    break
            
            if not text_column:
                logger.error("Could not find article text column. Please ensure your CSV has one of: " + 
                           ", ".join(possible_text_columns))
                return
            
            logger.info(f"Using '{text_column}' column for article text")
            
            # Initialize new columns
            df['Summary'] = ""
            df['Topics'] = ""
            df['ProcessingStatus'] = ""
            
            # Process each article
            total_articles = len(df)
            successful_count = 0
            
            for index, row in df.iterrows():
                logger.info(f"Processing article {index + 1}/{total_articles}")
                
                # Get article text
                article_text = str(row.get(text_column, ''))
                
                # Skip if article text is empty or too short
                if len(article_text.strip()) < 100:
                    logger.warning(f"Skipping article {index + 1}: Text too short or empty")
                    df.at[index, 'Summary'] = "Article text too short or empty"
                    df.at[index, 'Topics'] = "[]"
                    df.at[index, 'ProcessingStatus'] = "skipped_short_text"
                    continue
                
                # Analyze the article
                try:
                    analysis = self.analyze_article(article_text)
                    
                    # Update DataFrame
                    df.at[index, 'Summary'] = analysis['summary']
                    df.at[index, 'Topics'] = json.dumps(analysis['topics'])
                    df.at[index, 'ProcessingStatus'] = "success"
                    successful_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing article {index + 1}: {e}")
                    df.at[index, 'Summary'] = "Processing error occurred"
                    df.at[index, 'Topics'] = "[]"
                    df.at[index, 'ProcessingStatus'] = "error"
                
                # Add delay to avoid rate limiting
                time.sleep(1)
                
                # Save progress every 5 articles
                if (index + 1) % 5 == 0:
                    os.makedirs("csv_temp", exist_ok=True)
                    temp_filename = os.path.join("csv_temp", f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(output_csv_path)}")
                    df.to_csv(temp_filename, index=False)
                    logger.info(f"Progress saved: {index + 1} articles processed to {temp_filename}")
            
            # Ensure data directory exists and save final results
            os.makedirs('data', exist_ok=True)
            final_output_path = os.path.join('data', os.path.basename(output_csv_path))
            df.to_csv(final_output_path, index=False)
            logger.info(f"Analysis complete! Results saved to {final_output_path}")
            logger.info(f"Successfully processed {successful_count}/{total_articles} articles")
            
            # Display sample results
            if successful_count > 0:
                logger.info("\nSample results:")
                successful_rows = df[df['ProcessingStatus'] == 'success'].head(3)
                for idx, row in successful_rows.iterrows():
                    logger.info(f"Article {idx + 1}:")
                    logger.info(f"  Summary: {row['Summary']}")
                    logger.info(f"  Topics: {row['Topics']}")
            
        except FileNotFoundError:
            logger.error(f"Input file {input_csv_path} not found")
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            raise

def main():
    """
    Main function to run the article analysis
    """
    try:
        # Initialize analyzer (will use environment variables)
        analyzer = ArticleAnalyzer()
        
        # Process the CSV
        analyzer.process_csv()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with GCP_PROJECT_ID")
        print("2. Configured Google Cloud authentication")
        print("3. Your input CSV file is in the correct location")

if __name__ == "__main__":
    main()