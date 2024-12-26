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

# Configure logging with colors and performance metrics
class ColorFormatter(logging.Formatter):
    """Custom formatter adding colors to levelnames and performance tracking"""
    
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
        
        # Add file name and line number for errors and warnings
        if record.levelno >= logging.WARNING:
            record.location = f"{record.filename}:{record.lineno}"
        else:
            record.location = record.filename
        
        # Add elapsed time for performance logs
        if hasattr(record, 'elapsed'):
            record.msg = f"{record.msg} (took {record.elapsed:.2f}s)"
            
        return super().format(record)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Default to INFO level

# Console handler with color formatter
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = ColorFormatter('%(asctime)s [%(levelname)s] %(location)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load environment variables and configuration
env_load_start = time.time()
load_dotenv()
env_load_time = time.time() - env_load_start
logger.debug("Environment variables loaded", extra={"elapsed": env_load_time})

# Check for required environment variables
required_vars = {
    "AWS_ACCESS_KEY_ID": "AWS Access Key ID",
    "AWS_SECRET_ACCESS_KEY": "AWS Secret Access Key",
    "SENTIMENT_MODEL": "Sentiment Analysis Model",
    "CHAT_INSIGHTS_MODEL": "Chat Insights Model"
}

missing_vars = [name for var, name in required_vars.items() if not os.getenv(var)]
if missing_vars:
    logger.critical("Missing required environment variables: %s. Application cannot start.",
                   ', '.join(missing_vars))
    raise ValueError(f"Required environment variables are missing: {', '.join(missing_vars)}")

# Load model configurations
SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL")
CHAT_INSIGHTS_MODEL = os.getenv("CHAT_INSIGHTS_MODEL")
logger.info("Models configured - Sentiment: %s, Chat Insights: %s",
           SENTIMENT_MODEL.split('/')[-1], CHAT_INSIGHTS_MODEL.split('/')[-1])

# Initialize FastAPI app and core services
app = FastAPI(title="WhatsApp Chat Summary")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize instructor client with LiteLLM
client = instructor.from_litellm(completion)
logger.info("API server and LLM client initialized successfully")

# Setup static directories and cache
Path("static").mkdir(exist_ok=True)
Path("gh_static_front/analyzed_data").mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path("gh_static_front/analyzed_data")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/gh_static_front", StaticFiles(directory="gh_static_front"), name="gh_static_front")

@app.get("/")
async def root():
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
    media_type_percentages: Dict[str, float]
    top_media_sharers: List[UserActivity]
    most_reacted_media: List[MediaItem]

class MessageCategory(BaseModel):
    category: str
    subcategory: str
    messages: List[str]
    context: str
    participants: List[str]
    impact_score: float
    timestamp: str

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
    message_categories: List[MessageCategory]

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
# Exclude skin tone modifiers (U+1F3FB to U+1F3FF) from emoji detection
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF](?<![\U0001F3FB-\U0001F3FF])')
WORD_PATTERN = re.compile(r'\w+')
# Unicode control characters to remove
UNICODE_CONTROL_CHARS = re.compile(r'[\u200e\u200f\u202a-\u202f]+')

def clean_message(text: str) -> str:
    """Remove Unicode control characters and normalize whitespace."""
    return UNICODE_CONTROL_CHARS.sub('', text).strip()

# Pre-compile patterns for media messages
MEDIA_PATTERN = re.compile(r'(?:image|video|gif|sticker|audio|document)\s+omitted|\.(jpg|jpeg|png|gif|mp4|webp|pdf|doc|docx)>|\[Media:', re.IGNORECASE)

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
    insights_start = time.time()
    try:
        response = client.chat.completions.create(
            model=CHAT_INSIGHTS_MODEL,
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=2048,
            response_model=ChatSummary,
            caching=True
        )
        insights_time = time.time() - insights_start
        logger.info("Generated chat insights", extra={"elapsed": insights_time})
        return response
    except (Exception) as e:
        logger.error("Failed to generate chat insights: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate chat insights") from e

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
# Additional words to filter from word cloud
MEDIA_RELATED_WORDS = {
    'image', 'video', 'gif', 'sticker', 'audio', 'document',
    'omitted', 'attached', 'file', 'photo', 'picture'
}

def process_message_stats(message: str) -> tuple[list, dict, dict]:
    """
    Process a single message for emojis and words.
    Enhanced to normalize words and filter out media-related terms.
    """
    # Skip media-related messages entirely
    if MEDIA_PATTERN.search(str(message)):
        return [], Counter(), Counter()
        
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
            norm_word not in COMMON_WORDS and  # Filter out common words
            norm_word not in MEDIA_RELATED_WORDS and  # Filter out media-related words
            not norm_word.isdigit() and    # Remove pure numbers
            'http' not in norm_word        # Remove URLs or partial URLs
        ):
            words.append(norm_word)
    
    return emojis, Counter(emojis), Counter(words)

def parse_whatsapp_chat(content: str) -> tuple[pd.DataFrame, List[MediaItem]]:
    """Parse and clean WhatsApp chat log, returning the cleaned DataFrame and media items."""
    parse_start = time.time()
    messages = []
    media_items = []
    lines = content.split('\n')
    current_message = ''
    
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
                sender = clean_message(sender)
                message = clean_message(message)

                # Check for media messages
                media_match = MEDIA_PATTERN.search(message)
                if media_match:
                    try:
                        media_type = None
                        if 'omitted' in message.lower():
                            for type_name in VALID_MEDIA_TYPES:
                                if type_name in message.lower():
                                    media_type = type_name
                                    break
                        
                        if not media_type:
                            for ext, type_name in MEDIA_TYPE_MAP.items():
                                if f'.{ext}' in message.lower():
                                    media_type = type_name
                                    break
                        
                        if media_type:
                            media_items.append(MediaItem(
                                type=media_type,
                                sender=sender,
                                timestamp=timestamp,
                                reactions=0
                            ))
                            message = f"[Media: {media_type.upper()}] shared by {sender}"
                    except (AttributeError, IndexError) as e:
                        logger.warning("Failed to process media at line %d: %s", line_num, str(e))

                # Skip system messages
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
                        continue
                    
                    messages.append({
                        'timestamp': parsed_timestamp,
                        'sender': sender.strip(),
                        'message': message.strip()
                    })
                    matched = True
                    break
                except (ValueError, AttributeError) as e:
                    logger.error("Failed to parse message at line %d: %s", line_num, str(e))
                    continue
        
        if not matched and line.strip() and messages:  # Continuation of previous message
            current_message += ' ' + line
    
    if not messages:
        return pd.DataFrame(columns=['timestamp', 'sender', 'message']), []
    
    df = pd.DataFrame(messages)
    parse_time = time.time() - parse_start
    logger.info("Chat parsing completed", extra={"elapsed": parse_time})
    
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

    return MediaStats(
        total_media_shared=int(len(media_items)),
        media_by_type=media_by_type_dict,
        media_type_percentages=media_distribution,
        top_media_sharers=top_sharers,
        most_reacted_media=most_reacted
    )

def analyze_chat_stats(df: pd.DataFrame) -> tuple[Dict, Dict]:
    """Analyze chat statistics after cleaning is complete."""
    all_emojis = Counter()
    all_words = Counter()
    
    for message in df['message']:
        # DataFrame should already be cleaned of media messages
        # but we'll double-check just in case
        if MEDIA_PATTERN.search(str(message)):
            continue
            
        _, emoji_counts, word_counts = process_message_stats(message)
        all_emojis.update(emoji_counts)
        all_words.update(word_counts)
    
    return dict(all_emojis), dict(all_words)

# Cache for sentiment analysis results
sentiment_cache = {}

async def analyze_sentiment_batch(messages_batch: List[str]) -> float:
    """Analyze sentiment for a batch of messages, excluding media-related messages."""
    batch_start = time.time()
    
    # Filter out media messages
    filtered_messages = [
        msg for msg in messages_batch
        if not MEDIA_PATTERN.search(str(msg))
    ]
    
    if not filtered_messages:
        return 0.0  # Neutral sentiment for batches with only media messages
    
    # Create a cache key from the filtered messages
    cache_key = hash(tuple(filtered_messages))
    if cache_key in sentiment_cache:
        return sentiment_cache[cache_key]

    try:
        prompt = f"""Rate the overall sentiment of these messages from -1 (negative) to 1 (positive). Return only a number.
        Messages: {' '.join(filtered_messages)}"""
        
        response = client.chat.completions.create(
            model=SENTIMENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0,
            response_model=SentimentScore
        )
        score = max(min(response.score, 1.0), -1.0)
        sentiment_cache[cache_key] = score
        
        batch_time = time.time() - batch_start
        if batch_time > 2.0:  # Log only if processing took more than 2 seconds
            logger.info("Sentiment batch processed", extra={"elapsed": batch_time})
            
        return score
    except (Exception) as e:
        logger.error("Sentiment analysis failed: %s", str(e), exc_info=True)
        return 0.0

async def analyze_sentiment_parallel(daily_messages: Dict[datetime, List[str]], batch_size: int = 25) -> List[SentimentData]: # pylint: disable=unused-argument
    """Analyze sentiment for multiple days in parallel using optimized batching."""
    parallel_start = time.time()
    sentiment_data = []
    semaphore = asyncio.Semaphore(5)  # Balance between speed and rate limits
    
    # Group consecutive days into batches
    date_groups = []
    current_group = []
    dates = sorted(daily_messages.keys())
    
    for i, date in enumerate(dates):
        current_group.append(date)
        if len(current_group) == 3 or i == len(dates) - 1:
            date_groups.append(current_group)
            current_group = []
    
    async def process_date_group(dates):
        group_start = time.time()
        async with semaphore:
            group_messages = []
            batch_results = []
            
            for date in dates:
                # Filter out media messages first
                filtered_messages = [
                    msg for msg in daily_messages[date]
                    if not MEDIA_PATTERN.search(str(msg))
                ]
                
                if len(filtered_messages) > 5:
                    indices = [0, len(filtered_messages)//4, len(filtered_messages)//2,
                             (3*len(filtered_messages))//4, len(filtered_messages)-1]
                    group_messages.extend([filtered_messages[i] for i in indices])
                else:
                    group_messages.extend(filtered_messages)
                
                if len(group_messages) >= 15:
                    sentiment = await analyze_sentiment_batch(group_messages)
                    for d in dates:
                        if d <= date:
                            batch_results.append((d, sentiment, daily_messages[d]))
                    group_messages = []
            
            if group_messages:
                sentiment = await analyze_sentiment_batch(group_messages)
                remaining_dates = [d for d in dates if not any(d == r[0] for r in batch_results)]
                batch_results.extend((date, sentiment, daily_messages[date]) for date in remaining_dates)
            
            group_elapsed = time.time() - group_start
            if group_elapsed > 5.0:  # Log only if processing took more than 5 seconds
                logger.info("Date group processed", extra={"elapsed": group_elapsed})
            
            return batch_results
    
    # Process date groups concurrently
    tasks = [process_date_group(group) for group in date_groups]
    results = await asyncio.gather(*tasks)
    
    # Process results with deduplication
    seen_dates = set()
    for batch_results in results:
        for date, sentiment, messages in batch_results:
            if date not in seen_dates:
                seen_dates.add(date)
                sentiment_data.append(SentimentData(
                    date=str(date),
                    sentiment=sentiment,
                    messages=messages[:2]  # Limit stored messages
                ))
    
    elapsed = time.time() - parallel_start
    logger.info("Sentiment analysis completed", extra={"elapsed": elapsed})
    
    return sorted(sentiment_data, key=lambda x: x.date)

@app.post("/api/analyze")
async def analyze_chat(file: UploadFile = File(...)):
    """Analyze uploaded WhatsApp chat log."""
    analysis_start = time.time()
    logger.info("Starting analysis of file: %s", file.filename)
    
    try:
        content = await file.read()
        file_hash = calculate_md5(content)
        
        # Check cache first
        cached_result = get_cached_result(file_hash)
        if cached_result:
            logger.info("Cache hit for %s (%s)", file.filename, file_hash[:8])
            return JSONResponse(content={
                "md5": file_hash,
                **cached_result.dict()
            })
            
        # If not cached, proceed with analysis
        chat_text = content.decode('utf-8')
        
        # Parse and analyze chat content
        df, media_items = parse_whatsapp_chat(chat_text)
        
        if len(df) == 0:
            logger.error("Chat parsing failed for %s - no valid messages found", file.filename)
            raise HTTPException(
                status_code=400,
                detail="No messages could be parsed from the chat file. Please ensure this is a valid WhatsApp chat export."
            )
        
        # Analyze media statistics
        media_stats = analyze_media_stats(df, media_items)
        logger.info("Parsed %d messages and %d media items", len(df), len(media_items))
        
        # Create a clean DataFrame without media messages for text analysis
        clean_df = df[~df['message'].apply(lambda x: bool(MEDIA_PATTERN.search(str(x))))]
        
        # Then perform analysis on cleaned data (excluding media messages)
        emoji_counts, word_counts = analyze_chat_stats(clean_df)
        
        # Basic statistics from clean data
        logger.debug("Calculating user activity statistics")
        most_active = clean_df['sender'].value_counts().head(5).to_dict()
        
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
        
        prompt = f"""Analyze this WhatsApp chat and provide comprehensive insights with the following structure:

        1. Key topics discussed (max 5)
        2. Three most memorable moments
        3. A festive holiday greeting based on the chat context
        4. Create a comedic rhyming poem (at least 8 lines) that tells a story about the group's memorable moments and inside jokes. Make it festive and entertaining!
        5. Categorize messages into meaningful groups by analyzing:
           - Type of interaction (celebration, milestone, discussion, etc.)
           - Context and significance
           - Participant dynamics
           - Impact on team/organization
           - Cultural significance
           
           For each identified category, provide:
           - Category name and subcategory
           - Representative messages
           - Context and significance
           - Involved participants
           - Impact score (0.0 to 1.0)
           - Timestamp

        Don't use predetermined categories - identify natural patterns and groupings that emerge from the content.
        Consider message context, participant engagement, long-term significance, and cultural dynamics.

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
        thread_window = pd.Timedelta(hours=4)
        
        class MessageThread:
            def __init__(self, message: str, timestamp: pd.Timestamp):
                self.original_message = message
                self.start_time = timestamp
                self.messages = []
                self.reactions = len(EMOJI_PATTERN.findall(message))
            
            def is_active(self, current_time: pd.Timestamp) -> bool:
                return (current_time - self.start_time) <= thread_window
            
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
                        (messages_by_time['timestamp'] <= thread_start + thread_window)
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
        
        # Create summary with properly structured data including message categories
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
            media_stats=media_stats,
            message_categories=response.message_categories if hasattr(response, 'message_categories') else []
        )
        
        analysis_time = time.time() - analysis_start
        logger.info("Analysis completed", extra={"elapsed": analysis_time})
        
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
