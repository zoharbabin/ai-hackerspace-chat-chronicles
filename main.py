import string
import re
import os
import logging
import hashlib
import json
import time
from typing import Optional
from typing import List, Dict
from datetime import datetime, timedelta
import asyncio
import functools
from collections import Counter
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
import pandas as pd
import instructor
from litellm import completion
from pydantic import BaseModel
from dotenv import load_dotenv

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

# Load environment variables and configuration
start_time = time.time()
load_dotenv()
logger.info("Environment variables loaded in %.2fs", time.time() - start_time)

# Check for required environment variables
required_vars = {
    "AWS_ACCESS_KEY_ID": "AWS Access Key ID",
    "AWS_SECRET_ACCESS_KEY": "AWS Secret Access Key",
    "SENTIMENT_MODEL": "Sentiment Analysis Model",
    "CHAT_INSIGHTS_MODEL": "Chat Insights Model"
}

missing_vars = [name for var, name in required_vars.items() if not os.getenv(var)]
if missing_vars:
    logger.error("Missing required environment variables: %s", ', '.join(missing_vars))
    raise ValueError(f"Required environment variables are missing: {', '.join(missing_vars)}")

# Load model configurations
SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL")
CHAT_INSIGHTS_MODEL = os.getenv("CHAT_INSIGHTS_MODEL")
logger.info("Using models - Sentiment: %s, Chat Insights: %s", SENTIMENT_MODEL, CHAT_INSIGHTS_MODEL)

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

# Create static and cache directories if they don't exist
Path("static").mkdir(exist_ok=True)
Path("gh_static_front/analyzed_data").mkdir(parents=True, exist_ok=True)
logger.debug("Static and analyzed_data directories checked/created")

# Cache directory path
CACHE_DIR = Path("gh_static_front/analyzed_data")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/gh_static_front", StaticFiles(directory="gh_static_front"), name="gh_static_front")
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

class SentimentScore(BaseModel):
    score: float

class SentimentData(BaseModel):
    date: str
    sentiment: float
    messages: List[str]

class ViralMessage(BaseModel):
    message: str
    replies: int
    reactions: int
    thread: List[str]

class SharedLink(BaseModel):
    url: str
    replies: int
    reactions: int
    context: str

class MediaItem(BaseModel):
    type: str  # 'image', 'video', 'GIF', 'sticker'
    sender: str
    timestamp: str
    reactions: int

class MediaStats(BaseModel):
    total_media_shared: int
    media_by_type: Dict[str, int]
    top_media_sharers: List[UserActivity]
    most_reacted_media: List[MediaItem]

class ChatSummary(BaseModel):
    most_active_users: List[UserActivity]
    popular_topics: List[str]
    memorable_moments: List[str]
    emoji_stats: Dict[str, int]
    activity_by_date: Dict[str, int]
    word_cloud_data: List[WordCloudItem]
    holiday_greeting: str
    sentiment_over_time: List[SentimentData]
    happiest_days: List[SentimentData]
    saddest_days: List[SentimentData]
    viral_messages: List[ViralMessage]
    shared_links: List[SharedLink]
    chat_poem: str
    media_stats: MediaStats

def calculate_md5(content: bytes) -> str:
    """Calculate MD5 hash of file content."""
    return hashlib.md5(content).hexdigest()

def get_cached_result(file_hash: str) -> Optional[ChatSummary]:
    """Try to get cached analysis result."""
    cache_file = CACHE_DIR / f"{file_hash}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ChatSummary(**data)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error reading cache file: %s", str(e))
            return None
    return None

def save_to_cache(file_hash: str, result: ChatSummary):
    """Save analysis result to cache."""
    cache_file = CACHE_DIR / f"{file_hash}.json"
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result.dict(), f)
        logger.info("Analysis result cached to %s", cache_file)
    except (OSError, TypeError) as e:
        logger.error("Error saving to cache: %s", str(e))

# Pre-compile regex patterns
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF]')
WORD_PATTERN = re.compile(r'\w+')
# Unicode control characters to remove
UNICODE_CONTROL_CHARS = re.compile(r'[\u200e\u200f\u202a-\u202f]+')

def clean_message(text: str) -> str:
    """Remove Unicode control characters and normalize whitespace."""
    return UNICODE_CONTROL_CHARS.sub('', text).strip()

# Pre-compile pattern for media messages
MEDIA_PATTERN = re.compile(r'(?:‎)?\[?(?:\d{2}/\d{2}/\d{4},\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\]?\s)?(?:.*?):\s?(?:‎)?(?:(image|video|GIF|sticker|audio|document) omitted|<attached: \d+-(\w+)-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.(jpg|jpeg|png|gif|mp4|webp|pdf|doc|docx)>)')

# Valid media types
VALID_MEDIA_TYPES = {'image', 'video', 'gif', 'sticker', 'audio', 'document'}

# File extension mappings
MEDIA_TYPE_MAP: dict[str, str] = {
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'webp': 'image',
    'mp4': 'video',
    'pdf': 'document',
    'doc': 'document',
    'docx': 'document'
}

# Pre-compile patterns for system messages to filter out
SYSTEM_MESSAGE_PATTERNS = [
    re.compile(r'.*joined using this group\'s invite link'),  # Group joins
    re.compile(r'.*created this group'),  # Group creation
    re.compile(r'Your security code with.*'),  # Security code changes
    re.compile(r'.*changed their phone number'),  # Phone number changes
    re.compile(r'Messages and calls are end-to-end encrypted.*'),  # Encryption notice
    re.compile(r'This message was deleted'),  # Deleted messages
]
WHATSAPP_PATTERNS = [
    re.compile(r'\[(\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}:\d{2})\]\s(.*?):\s(.*)'),
    re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?\s(?:AM|PM)?) - (.*?): (.*)'),
    re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?) - (.*?): (.*)')
]

@functools.cache
def get_chat_insights(prompt_text: str) -> ChatSummary:
    task_start_time = time.time()
    logger.info("Requesting chat insights from Claude")
    try:
        response = client.chat.completions.create(
            model=CHAT_INSIGHTS_MODEL,
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=2048,
            response_model=ChatSummary,
            caching=True
        )
        logger.info("Chat insights received in %.2fs", time.time() - task_start_time)
        return response
    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error("Error getting chat insights: %s", str(e))
        raise

# Common words to filter out
COMMON_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'all', 'am', 'an', 'and', 'any', 
    'anybody', 'anyone', 'anything', 'are', 'as', 'at', 'be', 'because', 'been', 
    'being', 'both', 'but', 'by', 'can', 'come', 'could', 'day', 'did', 'do', 
    'each', 'either', 'every', 'everybody', 'everyone', 'everything', 'few', 
    'for', 'from', 'get', 'give', 'go', 'good', 'had', 'has', 'have', 'he', 'her', 
    'here', 'him', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'just', 
    'know', 'like', 'look', 'make', 'many', 'maybe', 'me', 'mine', 'more', 
    'most', 'much', 'must', 'my', 'myself', 'new', 'no', 'nobody', 'none', 'not', 
    'nothing', 'now', 'nowhere', 'of', 'on', 'once', 'one', 'only', 'or', 'our', 
    'ours', 'ourselves', 'out', 'over', 'people', 'perhaps', 'same', 'say', 'see', 
    'she', 'should', 'so', 'some', 'somebody', 'someone', 'something', 
    'somewhere', 'stuff', 'such', 'take', 'than', 'that', 'the', 'their', 
    'theirs', 'them', 'themself', 'themselves', 'then', 'there', 'therefore', 
    'these', 'they', 'thing', 'things', 'think', 'this', 'those', 'thus', 'time', 
    'to', 'two', 'up', 'us', 'use', 'using', 'very', 'want', 'was', 'way', 'we', 
    'well', 'were', 'what', 'when', 'which', 'who', 'will', 'with', 'would', 
    'year', 'you', 'your', 'yours', 'yourself', 'yourselves'
}

def process_message_stats(message: str) -> tuple[list, dict, dict]:
    """
    Process a single message for emojis and words.
    Enhanced to normalize words (remove punctuation, simple contractions, 
    possessives) before checking against COMMON_WORDS.
    """
    
    def normalize_word(word: str) -> str:
        """Return a 'normalized' version of the word for improved matching."""
        # Lowercase the word
        w = word.lower()
        # Strip leading/trailing punctuation
        w = w.strip(string.punctuation)
        # Remove simple possessives ('s) at the end (e.g., "John's" -> "john")
        w = re.sub(r"'s$", "", w)
        # Remove common contractions at the end (e.g., "can't" -> "can", "you're" -> "you")
        w = re.sub(r"'(d|m|ve|re|ll|t)$", "", w)
        return w
    
    # Extract emojis
    emojis = EMOJI_PATTERN.findall(str(message))
    
    # Get all candidate words and filter them
    words = []
    for raw_word in WORD_PATTERN.findall(str(message)):
        norm_word = normalize_word(raw_word)
        if (
            len(norm_word) > 3 and          # Remove very short words
            norm_word not in COMMON_WORDS and  # Filter out common words (using normalized form)
            not norm_word.isdigit() and    # Remove pure numbers
            'http' not in norm_word        # Remove URLs or partial URLs
        ):
            words.append(norm_word)
    
    return emojis, Counter(emojis), Counter(words)

def parse_whatsapp_chat(content: str) -> tuple[pd.DataFrame, List[MediaItem]]:
    """Parse and clean WhatsApp chat log, returning the cleaned DataFrame and media items."""
    task_start_time = time.time()
    logger.info("Starting WhatsApp chat parsing")
    
    messages = []
    media_items = []
    lines = content.split('\n')
    current_message = ''
    
    logger.debug("Processing %d lines of chat", len(lines))
    parsed_count = 0
    
    for line_num, line in enumerate(lines, 1):
        matched = False
        cleaned_line = clean_message(line)
        for pattern in WHATSAPP_PATTERNS:
            match = pattern.match(cleaned_line)
            if match:
                if current_message:  # Save previous multi-line message
                    cleaned_current = clean_message(current_message)
                    messages[-1]['message'] += '\n' + cleaned_current
                    current_message = ''
                
                timestamp, sender, message = match.groups()
                # Clean the sender and message
                sender = clean_message(sender)
                message = clean_message(message)

                # Check for media messages
                media_match = MEDIA_PATTERN.match(message)
                if media_match:
                    try:
                        # Extract media type from the match
                        # Groups: (1) = omitted type, (2) = attached type, (3) = file extension
                        omitted_type = media_match.group(1)
                        attached_type = media_match.group(2) # pylint: disable=unused-variable
                        file_extension = media_match.group(3)
                        
                        # Determine media type based on available information
                        media_type = None
                        if omitted_type:
                            media_type = omitted_type.lower()
                        elif file_extension:
                            media_type = file_extension.lower()
                        
                        # Normalize to lowercase
                        normalized_type = media_type.lower() if media_type else ''
                        
                        # First check if it's a valid media type directly
                        if normalized_type in VALID_MEDIA_TYPES:
                            mapped_type = normalized_type
                        else:
                            # If not, check if it's a known file extension
                            mapped_type = MEDIA_TYPE_MAP.get(normalized_type, 'unknown')
                            if mapped_type == 'unknown':
                                logger.warning("Unknown media type encountered: %s", media_type)
                        
                        # Create the media item
                        media_item = MediaItem(
                            type=mapped_type,
                            sender=sender,
                            timestamp=timestamp,
                            reactions=0  # Will be updated later when processing reactions
                        )
                        
                        # Add to media items list
                        media_items.append(media_item)
                        
                        # Replace the original message with a standardized format
                        message = f"[Media: {mapped_type.upper()}] shared by {sender}"
                        
                        # Log the media item for debugging
                        logger.debug("Processed media item: %s from %s at %s", mapped_type, sender, timestamp)
                        
                    except (AttributeError, IndexError) as e:
                        logger.error("Error processing media message at line %d: %s", line_num, str(e))

                # Skip system messages - message is already cleaned
                if any(pattern.match(message) for pattern in SYSTEM_MESSAGE_PATTERNS):
                    continue
                    
                try:
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
                        logger.warning("Could not parse timestamp at line %d: %s", line_num, timestamp)
                        continue
                    
                    messages.append({
                        'timestamp': parsed_timestamp,
                        'sender': sender.strip(),
                        'message': message.strip()
                    })
                    
                    parsed_count += 1
                    matched = True
                    break
                except (ValueError, AttributeError) as e:
                    logger.error("Error parsing message at line %d: %s", line_num, str(e))
                    continue
        
        if not matched and line.strip() and messages:  # Continuation of previous message
            current_message += ' ' + line
    
    if not messages:
        logger.warning("No messages were successfully parsed")
        logger.debug("First few lines of content: %s", lines[:5])
        return pd.DataFrame(columns=['timestamp', 'sender', 'message']), []
    
    df = pd.DataFrame(messages)
    processing_time = time.time() - task_start_time
    logger.info("Successfully parsed %d messages and %d media items in %.2fs", len(df), len(media_items), processing_time)
    logger.debug("Parsing rate: %.1f messages/second", len(df)/processing_time)
    
    return df, media_items

def analyze_media_stats(df: pd.DataFrame, media_items: List[MediaItem]) -> MediaStats:
    """Analyze media sharing statistics with enhanced reaction tracking."""
    # Count media by type
    media_by_type = Counter(item.type for item in media_items)
    
    # Count media shares by user
    media_by_user = Counter(item.sender for item in media_items)
    top_sharers = [
        UserActivity(name=user, count=int(count))
        for user, count in media_by_user.most_common(5)
    ]
    
    # Update reaction counts for media items with improved detection
    for item in media_items:
        try:
            # Parse the timestamp
            media_time = datetime.strptime(item.timestamp, '%d/%m/%Y, %H:%M:%S')
            window_start = media_time
            window_end = media_time + timedelta(minutes=30)  # Reduced window for more accurate reaction tracking
            
            # Get messages in the time window
            window_messages = df[
                (df['timestamp'] >= window_start) &
                (df['timestamp'] <= window_end)
            ]
            
            # Count reactions (emojis) in the time window
            reactions = 0
            for msg in window_messages['message']:
                # Skip the media message itself
                if '[Media:' in str(msg):
                    continue
                    
                # Count emojis as reactions
                emoji_count = len(EMOJI_PATTERN.findall(str(msg)))
                
                # Check for reaction-specific patterns
                reaction_patterns = ['👍', '❤️', '😂', '😮', '😢', '🙏', '👏']
                for pattern in reaction_patterns:
                    if pattern in str(msg):
                        reactions += 1
                        
                # Count general emojis if they appear alone (likely reactions)
                if emoji_count > 0 and len(str(msg).strip()) <= 5:
                    reactions += emoji_count
            
            item.reactions = reactions
            
        except (ValueError, KeyError) as e:
            logger.error("Error processing reactions for media item: %s", str(e))
            item.reactions = 0
    
    # Get most reacted media items
    most_reacted = sorted(
        [item for item in media_items if item.reactions > 0],  # Only include items with reactions
        key=lambda x: x.reactions,
        reverse=True
    )[:5]
    
    # Convert counts to regular integers
    media_by_type_dict = {k: int(v) for k, v in media_by_type.items()}
    
    # Calculate percentage distribution of media types
    total_media = sum(media_by_type_dict.values())
    media_distribution = {
        k: round((v / total_media) * 100, 2) if total_media > 0 else 0
        for k, v in media_by_type_dict.items()
    }
    
    # Add distribution percentages to the type counts
    media_by_type_dict = {
        k: {
            'count': v,
            'percentage': media_distribution[k]
        }
        for k, v in media_by_type_dict.items()
    }
    
    return MediaStats(
        total_media_shared=int(len(media_items)),
        media_by_type=media_by_type_dict,
        top_media_sharers=top_sharers,
        most_reacted_media=most_reacted
    )

def analyze_chat_stats(df: pd.DataFrame) -> tuple[Dict, Dict]:
    """Analyze chat statistics after cleaning is complete."""
    all_emojis = Counter()
    all_words = Counter()
    
    for message in df['message']:
        _, emoji_counts, word_counts = process_message_stats(message)
        all_emojis.update(emoji_counts)
        all_words.update(word_counts)
    
    return dict(all_emojis), dict(all_words)

# Cache for sentiment analysis results
sentiment_cache = {}

async def analyze_sentiment_batch(messages_batch: List[str]) -> float:
    """Analyze sentiment for a batch of messages, excluding media-related messages."""
    # Filter out media messages
    filtered_messages = [
        msg for msg in messages_batch
        if not (msg.startswith('[Media:') or MEDIA_PATTERN.match(msg))
    ]
    
    if not filtered_messages:
        return 0.0  # Neutral sentiment for batches with only media messages
    
    # Create a cache key from the filtered messages
    cache_key = hash(tuple(filtered_messages))
    if cache_key in sentiment_cache:
        return sentiment_cache[cache_key]

    # Use semantic batching - group similar messages together
    prompt = f"""Rate the overall sentiment of these messages from -1 (negative) to 1 (positive). Return only a number.
    Messages: {' '.join(filtered_messages)}"""
    
    try:
        response = client.chat.completions.create(
            model=SENTIMENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,  # Increased to handle longer responses
            temperature=0,
            response_model=SentimentScore
        )
        score = max(min(response.score, 1.0), -1.0)
        sentiment_cache[cache_key] = score
        return score
    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.warning("Error in sentiment analysis: %s", str(e))
        return 0.0

async def analyze_sentiment_parallel(daily_messages: Dict[datetime, List[str]], batch_size: int = 25) -> List[SentimentData]: # pylint: disable=unused-argument
    """Analyze sentiment for multiple days in parallel using optimized batching."""
    sentiment_data = []
    semaphore = asyncio.Semaphore(5)  # Balance between speed and rate limits
    
    # Group consecutive days into batches for more accurate sentiment trends
    date_groups = []
    current_group = []
    dates = sorted(daily_messages.keys())
    
    for i, date in enumerate(dates):
        current_group.append(date)
        # Create a new group every 3 days or at the end
        if len(current_group) == 3 or i == len(dates) - 1:
            date_groups.append(current_group)
            current_group = []
    
    async def process_date_group(dates):
        async with semaphore:
            # Collect representative messages from each day
            group_messages = []
            batch_results = []
            
            for date in dates:
                day_messages = daily_messages[date]
                # Get representative messages spread throughout the day
                if len(day_messages) > 5:
                    # Take messages from start, middle, and end of day
                    indices = [0, len(day_messages)//4, len(day_messages)//2,
                             (3*len(day_messages))//4, len(day_messages)-1]
                    group_messages.extend([day_messages[i] for i in indices])
                else:
                    group_messages.extend(day_messages)
                
                # If group is getting too large, process current batch
                if len(group_messages) >= 15:
                    sentiment = await analyze_sentiment_batch(group_messages)
                    for d in dates:
                        if d <= date:  # Only process dates up to current point
                            batch_results.append((d, sentiment, daily_messages[d]))
                    group_messages = []  # Reset for next batch
            
            # Process any remaining messages
            if group_messages:
                sentiment = await analyze_sentiment_batch(group_messages)
                remaining_dates = [d for d in dates if not any(d == r[0] for r in batch_results)]
                batch_results.extend((date, sentiment, daily_messages[date]) for date in remaining_dates)
            
            return batch_results
    
    # Process date groups concurrently
    tasks = [process_date_group(group) for group in date_groups]
    results = await asyncio.gather(*tasks)
    
    # Flatten results and create SentimentData objects
    for group_results in results:
        for date, sentiment, messages in group_results:
            sentiment_data.append(SentimentData(
                date=str(date),
                sentiment=sentiment,
                messages=messages[:3]  # Keep top 3 messages for context
            ))
    
    # Flatten results and create SentimentData objects with deduplication
    seen_dates = set()
    for batch_results in results:
        for date, sentiment, messages in batch_results:
            if date not in seen_dates:
                seen_dates.add(date)
                sentiment_data.append(SentimentData(
                    date=str(date),
                    sentiment=sentiment,
                    messages=messages[:2]  # Further limit messages stored
                ))
    
    # Sort by date before returning
    return sorted(sentiment_data, key=lambda x: x.date)

@app.post("/api/analyze")
async def analyze_chat(file: UploadFile = File(...)):
    """Analyze uploaded WhatsApp chat log."""
    task_start_time = time.time()
    logger.info("Starting analysis of file: %s", file.filename)
    
    try:
        # Read file content
        content = await file.read()
        
        # Calculate MD5 hash of file content
        file_hash = calculate_md5(content)
        logger.info("File hash: %s", file_hash)
        
        # Check cache first
        cached_result = get_cached_result(file_hash)
        if cached_result:
            logger.info("Returning cached analysis for %s", file.filename)
            return JSONResponse(content={
                "md5": file_hash,
                **cached_result.dict()
            })
            
        # If not cached, proceed with analysis
        chat_text = content.decode('utf-8')
        logger.debug("File decoded successfully, size: %d characters", len(chat_text))
        
        # First parse and clean all messages and extract media items
        df, media_items = parse_whatsapp_chat(chat_text)
        
        if len(df) == 0:
            logger.error("No messages could be parsed from the chat file")
            raise HTTPException(status_code=400, detail="No messages could be parsed from the chat file. Please ensure this is a valid WhatsApp chat export.")
        
        # Then perform analysis on cleaned data
        emoji_counts, word_counts = analyze_chat_stats(df)
        
        # Basic statistics
        logger.debug("Calculating user activity statistics")
        most_active = df['sender'].value_counts().head(5).to_dict()
        
        # Analyze media statistics
        logger.debug("Analyzing media statistics")
        media_stats = analyze_media_stats(df, media_items)
        
        # Get chat insights using Claude via AWS Bedrock
        logger.debug("Preparing prompt for Claude analysis")
        # Intelligent message sampling - get messages from different time periods
        sample_size = min(100, len(df))
        samples = []
        
        # Get messages from different time periods for better coverage
        for period in pd.date_range(df['timestamp'].min(), df['timestamp'].max(), periods=5):
            period_messages = df[df['timestamp'].dt.date == period.date()]['message'].tolist()
            if period_messages:
                samples.extend(period_messages[:20])  # Up to 20 messages per period
        
        # If we don't have enough samples, add random messages
        if len(samples) < sample_size:
            remaining = df[~df['message'].isin(samples)].sample(n=min(sample_size - len(samples), len(df)))
            samples.extend(remaining['message'].tolist())
        
        prompt = f"""Analyze this WhatsApp chat and provide insights in the following format:
        1. Key topics discussed (max 5)
        2. Three most memorable moments
        3. A festive holiday greeting based on the chat context
        4. Create a comedic rhyming poem (at least 8 lines) that tells a story about the group's memorable moments and inside jokes. Make it festive and entertaining!

        Chat sample: {' '.join(samples)}"""
        
        # Get AI insights using instructor with structured output
        response = get_chat_insights(prompt)
        
        # Activity by date
        logger.debug("Calculating activity by date")
        daily_messages = df.groupby(df['timestamp'].dt.date).agg({
            'message': list
        }).to_dict()['message']
        
        activity = {str(k): len(v) for k, v in daily_messages.items()}
        
        # Analyze sentiment for each day in parallel
        logger.debug("Analyzing sentiment in parallel")
        sentiment_data = await analyze_sentiment_parallel(daily_messages)
        
        # Sort sentiment data for happiest/saddest days
        sentiment_data.sort(key=lambda x: x.sentiment)
        saddest_days = sentiment_data[:3]  # 3 most negative days
        happiest_days = sentiment_data[-3:][::-1]  # 3 most positive days
        
        # Identify viral messages by analyzing engagement patterns
        logger.debug("Identifying viral messages")
        messages_by_time = df.sort_values('timestamp')
        logger.debug("Processing %d messages for viral threads", len(messages_by_time))
        
        # Window for considering messages part of the same thread (4 hours)
        THREAD_WINDOW = pd.Timedelta(hours=4)
        
        class MessageThread:
            def __init__(self, message: str, timestamp: pd.Timestamp):
                self.original_message = message
                self.start_time = timestamp
                self.messages = []
                self.reactions = len(EMOJI_PATTERN.findall(message))
            
            def is_active(self, current_time: pd.Timestamp) -> bool:
                return (current_time - self.start_time) <= THREAD_WINDOW
            
            def is_related(self, message: str) -> bool:
                """Check if a message is likely a reply to the thread."""
                orig_lower = self.original_message.lower()
                msg_lower = message.lower()
                
                # Direct reply indicators
                if (message.startswith('@') or
                    'replied to' in msg_lower or
                    orig_lower in msg_lower):
                    return True
                
                # Semantic similarity
                orig_words = set(orig_lower.split())
                msg_words = set(msg_lower.split())
                common_words = orig_words & msg_words
                if len(common_words) >= 2 and not common_words.issubset(COMMON_WORDS):
                    return True
                
                # Question-answer pattern
                if '?' in self.original_message and len(message.split()) <= 10:
                    return True
                
                return False
            
            def add_message(self, message: str) -> None:
                self.messages.append(message)
                self.reactions += len(EMOJI_PATTERN.findall(message))
            
            def is_significant(self) -> bool:
                return len(self.messages) >= 2
            
            def to_viral_message(self) -> ViralMessage:
                return ViralMessage(
                    message=self.original_message,
                    replies=len(self.messages),
                    reactions=self.reactions,
                    thread=self.messages
                )

        def process_message_threads(messages_df: pd.DataFrame) -> List[ViralMessage]:
            viral_messages = []
            current_thread = None
            
            for _, row in messages_df.iterrows():
                message = row['message']
                timestamp = row['timestamp']
                
                # Skip system messages and very short messages
                if (any(pattern.match(message) for pattern in SYSTEM_MESSAGE_PATTERNS) or
                    len(message.split()) < 3):
                    continue
                
                # Check if message belongs to current thread
                if (current_thread and
                    current_thread.is_active(timestamp) and
                    current_thread.is_related(message)):
                    current_thread.add_message(message)
                else:
                    # Save significant threads
                    if current_thread and current_thread.is_significant():
                        viral_messages.append(current_thread.to_viral_message())
                    # Start new thread
                    current_thread = MessageThread(message, timestamp)
            
            # Handle the final thread
            if current_thread and current_thread.is_significant():
                viral_messages.append(current_thread.to_viral_message())
            
            # Sort by total engagement and take top 3
            return sorted(
                viral_messages,
                key=lambda x: x.replies + x.reactions,
                reverse=True
            )[:3]
        
        viral_messages = process_message_threads(messages_by_time)

        # Analyze shared links
        logger.debug("Analyzing shared links")
        shared_links = []
        url_pattern = re.compile(r'https?://\S+')
        
        # Track link engagement
        link_stats = {}  # url -> {replies: int, reactions: int, context: str}
        
        # First pass: find all links and their immediate context
        for idx, row in messages_by_time.iterrows(): # pylint: disable=unused-variable
            message = row['message']
            urls = url_pattern.findall(message)
            
            if urls:
                # Count reactions in the message containing the link
                reactions = len(EMOJI_PATTERN.findall(message))
                
                for url in urls:
                    if url not in link_stats:
                        link_stats[url] = {
                            'replies': 0,
                            'reactions': reactions,
                            'context': message
                        }
                    else:
                        link_stats[url]['reactions'] += reactions

        # Second pass: count replies to messages with links
        for url, stats in link_stats.items():
            # Find messages that reference this link
            for idx, row in messages_by_time.iterrows():
                message = row['message'].lower()
                if url.lower() in message:
                    # Count replies and reactions in the thread
                    thread_start = row['timestamp']
                    thread_messages = messages_by_time[
                        (messages_by_time['timestamp'] > thread_start) &
                        (messages_by_time['timestamp'] <= thread_start + THREAD_WINDOW)
                    ]
                    
                    stats['replies'] += len(thread_messages)
                    stats['reactions'] += sum(len(EMOJI_PATTERN.findall(m)) for m in thread_messages['message'])

        # Convert to SharedLink objects and sort by engagement
        for url, stats in link_stats.items():
            shared_links.append(SharedLink(
                url=url,
                replies=stats['replies'],
                reactions=stats['reactions'],
                context=stats['context']
            ))

        shared_links.sort(key=lambda x: x.replies + x.reactions, reverse=True)
        shared_links = shared_links[:10]  # Keep top 10 most engaging links
        
        # Convert numpy values to native Python types
        most_active_converted = {k: int(v) for k, v in most_active.items()}
        emoji_counts_converted = {k: int(v) for k, v in emoji_counts.items()}
        word_counts_converted = {k: int(v) for k, v in word_counts.items()}
        activity_converted = {k: int(v) for k, v in activity.items()}
        
        # Create summary with properly structured data
        summary = ChatSummary(
            most_active_users=[UserActivity(name=k, count=v) for k, v in most_active_converted.items()],
            popular_topics=response.popular_topics,
            memorable_moments=response.memorable_moments,
            emoji_stats=emoji_counts_converted,
            activity_by_date=activity_converted,
            word_cloud_data=[WordCloudItem(text=k, value=v) for k, v in sorted(word_counts_converted.items(), key=lambda x: x[1], reverse=True)[:50]],
            holiday_greeting=response.holiday_greeting,
            sentiment_over_time=sorted(sentiment_data, key=lambda x: x.date),
            happiest_days=happiest_days,
            saddest_days=saddest_days,
            viral_messages=viral_messages,
            shared_links=shared_links,
            chat_poem=response.chat_poem,
            media_stats=media_stats
        )
        
        total_time = time.time() - task_start_time
        logger.info("Analysis completed in %.2fs", total_time)
        
        # Save result to cache
        save_to_cache(file_hash, summary)
        
        # Return both the md5 and the analysis results
        return JSONResponse(content={
            "md5": file_hash,
            **summary.model_dump()
        })
            
    except (ValueError, OSError, HTTPException) as e:
        logger.error("Error during analysis: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
