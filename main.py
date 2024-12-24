from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import pandas as pd
from typing import List, Dict, Union
import json
from datetime import datetime
import re
from pathlib import Path
import instructor
from litellm import completion
from pydantic import BaseModel
import functools
from dotenv import load_dotenv
import os
import logging
import time
from typing import Optional

# Configure logging with colors
class ColorFormatter(logging.Formatter):
    """Custom formatter adding colors to levelnames"""
    
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Add file name and line number
        record.location = f"{record.filename}:{record.lineno}"
        
        return super().format(record)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Console handler with color formatter
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = ColorFormatter('%(asctime)s - %(location)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load environment variables
start_time = time.time()
load_dotenv()
logger.info(f"Environment variables loaded in {time.time() - start_time:.2f}s")

# Check for required AWS credentials
if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
    logger.error("Missing AWS credentials")
    raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are required")

# Initialize FastAPI app
app = FastAPI(title="WhatsApp Chat Summary")
logger.info("FastAPI application initialized")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.debug("CORS middleware configured")

# Initialize instructor client with LiteLLM
client = instructor.from_litellm(completion)
logger.info("Instructor client initialized with LiteLLM")

# Create static directory if it doesn't exist
Path("static").mkdir(exist_ok=True)
logger.debug("Static directory checked/created")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.debug("Static files mounted")

@app.get("/")
async def root():
    logger.debug("Root endpoint accessed - redirecting to index.html")
    return RedirectResponse(url="/static/index.html")

class UserActivity(BaseModel):
    name: str
    count: int

class WordCloudItem(BaseModel):
    text: str
    value: int

class ChatSummary(BaseModel):
    most_active_users: List[UserActivity]
    popular_topics: List[str]
    memorable_moments: List[str]
    emoji_stats: Dict[str, int]
    activity_by_date: Dict[str, int]
    word_cloud_data: List[WordCloudItem]
    holiday_greeting: str

@functools.cache
def get_chat_insights(prompt_text: str) -> ChatSummary:
    start_time = time.time()
    logger.info("Requesting chat insights from Claude")
    try:
        response = client.chat.completions.create(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=1024,
            response_model=ChatSummary,
            caching=True
        )
        logger.info(f"Chat insights received in {time.time() - start_time:.2f}s")
        return response
    except Exception as e:
        logger.error(f"Error getting chat insights: {str(e)}")
        raise

def parse_whatsapp_chat(content: str) -> pd.DataFrame:
    """Parse WhatsApp chat log into a pandas DataFrame."""
    start_time = time.time()
    logger.info("Starting WhatsApp chat parsing")
    
    # WhatsApp timestamp patterns (support multiple formats)
    patterns = [
        r'\[(\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}:\d{2})\]\s(.*?):\s(.*)',
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?\s(?:AM|PM)?) - (.*?): (.*)',
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?) - (.*?): (.*)'
    ]
    
    messages = []
    lines = content.split('\n')
    current_message = ''
    
    logger.debug(f"Processing {len(lines)} lines of chat")
    parsed_count = 0
    
    for line_num, line in enumerate(lines, 1):
        matched = False
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                if current_message:  # Save previous multi-line message
                    messages[-1]['message'] += '\n' + current_message.strip()
                    current_message = ''
                
                timestamp, sender, message = match.groups()
                try:
                    # Try different timestamp formats
                    timestamp = timestamp.strip('[]')
                    parsed_timestamp: Optional[datetime] = None
                    
                    for fmt in ['%d/%m/%Y, %H:%M:%S', '%m/%d/%y, %I:%M:%S %p', '%m/%d/%y, %I:%M %p',
                               '%d/%m/%y, %H:%M:%S', '%d/%m/%y, %H:%M']:
                        try:
                            parsed_timestamp = datetime.strptime(timestamp, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_timestamp is None:
                        logger.warning(f"Could not parse timestamp at line {line_num}: {timestamp}")
                        continue
                    
                    messages.append({
                        'timestamp': parsed_timestamp,
                        'sender': sender.strip(),
                        'message': message.strip()
                    })
                    parsed_count += 1
                    matched = True
                    break
                except Exception as e:
                    logger.error(f"Error parsing message at line {line_num}: {str(e)}")
                    continue
        
        if not matched and line.strip() and messages:  # Continuation of previous message
            current_message += ' ' + line
    
    if not messages:
        logger.warning("No messages were successfully parsed")
        logger.debug(f"First few lines of content: {lines[:5]}")
        return pd.DataFrame(columns=['timestamp', 'sender', 'message'])
    
    df = pd.DataFrame(messages)
    processing_time = time.time() - start_time
    logger.info(f"Successfully parsed {len(df)} messages in {processing_time:.2f}s")
    logger.debug(f"Parsing rate: {len(df)/processing_time:.1f} messages/second")
    return df

@app.post("/api/analyze")
async def analyze_chat(file: UploadFile = File(...)):
    """Analyze uploaded WhatsApp chat log."""
    start_time = time.time()
    logger.info(f"Starting analysis of file: {file.filename}")
    
    try:
        # Read and decode file
        content = await file.read()
        chat_text = content.decode('utf-8')
        logger.debug(f"File decoded successfully, size: {len(chat_text)} characters")
        
        # Parse chat into DataFrame
        df = parse_whatsapp_chat(chat_text)
        
        if len(df) == 0:
            logger.error("No messages could be parsed from the chat file")
            raise HTTPException(status_code=400, detail="No messages could be parsed from the chat file. Please ensure this is a valid WhatsApp chat export.")
        
        # Basic statistics
        logger.debug("Calculating user activity statistics")
        most_active = df['sender'].value_counts().head(5).to_dict()
        
        # Get chat insights using Claude via AWS Bedrock
        logger.debug("Preparing prompt for Claude analysis")
        prompt = f"""Analyze this WhatsApp group chat and provide insights in the following format:
        1. Key topics discussed (max 5)
        2. Three most memorable moments
        3. A festive holiday greeting based on the chat context
        
        Chat sample: {chat_text[:2000]}"""  # Using first 2000 chars as sample
        
        # Get AI insights using instructor with structured output
        response = get_chat_insights(prompt)
        
        # Process chat data
        logger.debug("Processing emoji statistics")
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]')
        emojis = []
        for msg in df['message']:
            emojis.extend(emoji_pattern.findall(str(msg)))
        emoji_counts = {emoji: emojis.count(emoji) for emoji in set(emojis)}
        
        # Activity by date
        logger.debug("Calculating activity by date")
        activity = df.groupby(df['timestamp'].dt.date).size().to_dict()
        activity = {str(k): v for k, v in activity.items()}
        
        # Word cloud data
        logger.debug("Generating word cloud data")
        words = ' '.join(df['message'].astype(str)).lower()
        word_pattern = re.compile(r'\w+')
        word_counts = {}
        for word in word_pattern.findall(words):
            if len(word) > 3:  # Filter out short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Create summary with properly structured data
        summary = ChatSummary(
            most_active_users=[UserActivity(name=k, count=v) for k, v in most_active.items()],
            popular_topics=response.popular_topics,
            memorable_moments=response.memorable_moments,
            emoji_stats=emoji_counts,
            activity_by_date=activity,
            word_cloud_data=[WordCloudItem(text=k, value=v) for k, v in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:50]],
            holiday_greeting=response.holiday_greeting
        )
        
        total_time = time.time() - start_time
        logger.info(f"Analysis completed in {total_time:.2f}s")
        return summary
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
