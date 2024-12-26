# WhatsApp Holiday Chat Analyzer 🎄✨

A festive web application that analyzes WhatsApp chat exports to create beautiful visualizations and AI-powered insights about your group conversations. Perfect for celebrating your group's year in messages!

This was also an experiement of writing an entire project where:  

1. [ChatGPT](https://openai.com/index/chatgpt/) o1-Pro was the Product Manager  
2. [Roo-Cline](https://github.com/RooVetGit/Roo-Cline) powered by [Claude 3.5 Sonnet](https://www.anthropic.com/news/claude-3-5-sonnet) (on [AWS Bedkrock](https://aws.amazon.com/bedrock/)) was the Developer and QA  
3. A human ([@zoharbabin](https://github.com/zoharbabin/)) as the investor and manager  

## Features 🌟

- **Interactive Timeline**: Visualize chat activity patterns over time
- **Word Cloud**: Dynamic visualization of most used words with popularity counts
- **Sentiment Analysis**: Track group mood over time with AI-powered sentiment scoring
- **Top Contributors**: Identify the most active participants with message counts
- **Emoji Analysis**: Track and visualize the most popular emojis used
- **Media Analysis**: 
  - Track media sharing patterns
  - Identify top media sharers
  - Monitor most reacted media items
  - Media type distribution statistics
- **Message Categories**: AI-powered categorization of messages with:
  - Category and subcategory classification
  - Context and significance analysis
  - Participant dynamics
  - Impact scoring
- **Viral Messages**: Detect and showcase messages that sparked the most engagement
- **Shared Links**: Track and analyze the most engaging shared links with context
- **AI-Powered Insights**: 
  - Memorable moments detection
  - Context-aware holiday greetings
  - Custom chat poems based on group dynamics
  - Popular topics analysis
- **Smart Caching**: MD5-based caching system for faster repeated analyses
- **Privacy Protection**: Automatic phone number anonymization with fun nicknames

## Tech Stack 🛠

- **Backend**: 
  - FastAPI (Python)
  - Pydantic for data validation
  - Async processing for sentiment analysis
  - AWS Bedrock integration via LiteLLM
  - Instructor for structured AI outputs
  - Smart caching with MD5 hashing

- **Frontend**: 
  - HTML5 with responsive design
  - Vanilla JavaScript
  - Chart.js for data visualization
  - Words Cloud Component

- **AI/ML**: 
  - Claude 3.5 Sonnet via AWS Bedrock for:
    - Sentiment analysis
    - Chat insights
    - Message categorization
  - Parallel sentiment analysis with batching
  - Structured output parsing

- **Performance**: 
  - MD5-based caching system
  - Parallel processing for sentiment analysis
  - Optimized message parsing with regex
  - Smart message batching for AI analysis

## Prerequisites 📋

- Python 3.9+
- AWS Account with Bedrock access
- AWS credentials configured

## Setup 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/holiday-ai-hackerspace.git
cd holiday-ai-hackerspace
```

2. Create and activate a virtual environment:
```bash
python -m venv holyvenv
source holyvenv/bin/activate  # On Windows: holyvenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
SENTIMENT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
CHAT_INSIGHTS_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

5. Run the application:
```bash
uvicorn main:app --reload
```

The application will be available at http://localhost:8000

## Usage 📱

1. Export your WhatsApp chat:
   - Open WhatsApp group
   - Go to Group Info
   - Scroll down to "Export Chat"
   - Choose "Without Media"

2. Upload the exported .txt file to the application

3. View your personalized chat analysis with:
   - Activity timeline showing message patterns
   - Word cloud of most used terms
   - Sentiment analysis timeline showing group mood
   - Top contributors and their message counts
   - Most used emoji statistics
   - AI-detected memorable moments
   - Media sharing statistics and trends
   - Message categorization with impact scores
   - Viral messages with engagement metrics
   - Popular shared links with context
   - Custom holiday greeting
   - Group chat poem

## Project Structure 📁

```
holiday-ai-hackerspace/
├── main.py                # FastAPI application and backend logic
├── anonymizer.py         # Phone number anonymization logic
├── requirements.txt      # Python dependencies
├── .env.example         # Example environment variables
├── .gitignore          # Git ignore rules
├── static/             # Upload interface assets
│   ├── index.html      # Interface for chat file upload
│   └── app.js          # Upload handling and API integration
└── gh_static_front/    # Visualization interface assets
    ├── index.html      # Results visualization interface
    ├── app.js          # Visualization logic
    ├── word-cloud.js   # Word cloud implementation
    └── analyzed_data/  # Pre-analyzed chat data
```

## Development 🔧

### Backend (main.py)
- FastAPI application with CORS support
- Structured logging with color formatting
- Multiple timestamp format support
- Parallel sentiment analysis with batching
- MD5-based caching system
- Comprehensive error handling
- Media analysis and categorization
- Viral message detection
- Shared link analysis
- Phone number anonymization

### Frontend
- Responsive design
- Interactive visualizations:
  - Activity timeline
  - Word cloud
  - Sentiment analysis graph
  - Media statistics displays
  - Message category cards
- Error handling and loading states

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

### Guidelines
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed
- Test thoroughly before submitting

## Roadmap 🗺️

### Platform Expansion
- [ ] Add support for Telegram exports
- [ ] Add support for Facebook Messenger exports
- [ ] Add support for Discord exports
- [ ] Add support for Slack exports

### Export and Sharing
- [ ] Enable PDF export of summaries
- [ ] Create shareable summary links

### Accessibility
- [ ] Add ARIA labels
- [ ] Make visualizations screen-reader friendly

### Enhanced Insights
- [ ] Implement detailed emotion detection
- [ ] Add topic clustering
- [ ] Track engagement trends
- [ ] Create member badges and streaks

### Customization and Visualization
- [ ] Add date range filtering
- [ ] Implement activity heatmaps
- [ ] Add zoomable timelines

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 💝

- Built with Roo-Cline, ChatGPT and @zoharbabin
- Chart.js for data visualization
- AWS Bedrock for AI capabilities

---

Made with ❤️ for the holidays