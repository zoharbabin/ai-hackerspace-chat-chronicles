# WhatsApp Holiday Chat Analyzer 🎄✨

A festive web application that analyzes WhatsApp chat exports to create beautiful visualizations and AI-powered insights about your group conversations. Perfect for celebrating your group's year in messages!

This was also an experiement of writing an entire project where:  

1. ChatGPT o1-Pro was the Product Manager  
2. Roo-Cline powered by Claude 3.5 Sonnet was the Developer and QA  
3. A human ([@zoharbabin](https://github.com/zoharbabin/)) as the investor and manager  

## Features 🌟

- **Interactive Timeline**: Visualize chat activity patterns over time with clickable data points
- **Floating Word Cloud**: Interactive visualization of most used words with popularity counts
- **Sentiment Analysis**: Track group mood over time with AI-powered sentiment scoring
- **Top Contributors**: Identify the most active participants with message counts
- **Emoji Analysis**: Track and visualize the most popular emojis used
- **Viral Messages**: Detect and showcase messages that sparked the most engagement
- **Shared Links**: Track and analyze the most engaging shared links with context
- **AI-Powered Insights**: 
  - Memorable moments detection
  - Context-aware holiday greetings
  - Custom chat poems based on group dynamics
  - Popular topics analysis
- **Festive UI**: Snow effects, confetti animations, and holiday-themed design
- **Real-time Analysis**: Instant processing and visualization of chat data
- **Responsive Design**: Works beautifully on both desktop and mobile
- **Smart Caching**: Efficient caching system for faster repeated analyses

## Tech Stack 🛠

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **AI/ML**: 
  - Claude AI via AWS Bedrock for insights
  - Parallel sentiment analysis processing
  - Smart message batching
- **Visualization**: 
  - Chart.js for timelines and graphs
  - Custom interactive word cloud implementation
- **Performance**: 
  - Caching system with MD5 hashing
  - Parallel processing for sentiment analysis
  - Optimized message parsing
- **Dependencies**: See requirements.txt for full list

## Prerequisites 📋

- Python 3.9+
- AWS Account with Bedrock access
- AWS credentials configured
- Node.js (optional, for development)

## Setup 🚀

### Local Development

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

### Docker Setup

1. Build the Docker image:
```bash
docker build -t whatsapp-analyzer .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e SENTIMENT_MODEL=your_model \
  -e CHAT_INSIGHTS_MODEL=your_model \
  whatsapp-analyzer
```

## Usage 📱

1. Export your WhatsApp chat:
   - Open WhatsApp group
   - Go to Group Info
   - Scroll down to "Export Chat"
   - Choose "Without Media"

2. Upload the exported .txt file to the application

3. View your personalized chat analysis with:
   - Interactive activity timeline with clickable data points
   - Floating word cloud with popularity counts
   - Sentiment analysis timeline showing group mood
   - Top contributors and their message counts
   - Most used emoji statistics
   - AI-detected memorable moments
   - Viral messages with engagement metrics
   - Popular shared links with context
   - Custom holiday greeting
   - Group chat poem

## Project Structure 📁

```
holiday-ai-hackerspace/
├── main.py                # FastAPI application and backend logic
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore rules
├── static/             # Static frontend assets
│   ├── index.html      # Main HTML file
│   ├── app.js          # Frontend JavaScript
│   └── word-cloud.js   # Word cloud implementation
├── gh_static_front/    # GitHub static frontend
│   ├── index.html      # Static HTML file
│   ├── app.js          # Frontend logic
│   ├── word-cloud.js   # Word cloud visualization
│   └── analyzed_data/  # Pre-analyzed chat data
└── cache/             # Cache directory for API responses
```

## Development 🔧

### Backend (main.py)
- FastAPI application with CORS support
- Structured logging with color formatting
- Efficient chat parsing with multiple timestamp formats
- Parallel sentiment analysis processing
- Smart message batching for AI analysis
- Caching system with MD5 hashing
- Comprehensive error handling
- Viral message detection algorithm
- Shared link analysis

### Frontend (static/ & gh_static_front/)
- Responsive design with Tailwind CSS
- Interactive visualizations:
  - Activity timeline with clickable points
  - Floating word cloud with hover effects
  - Sentiment analysis graph
  - Engagement metrics displays
- Real-time data processing
- Festive animations (snow, confetti)
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

Future improvements could include:

1. [ ] Support for more chat export formats (Facebook Messenger, Discord, etc.)
2. [ ] Export reports as PDF
3. [ ] More AI-powered insights and additional visualization types
4. [ ] Enhanced sentiment analysis with emotion detection
5. [ ] Topic clustering and trend analysis
6. [ ] Custom theme support

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 💝

- Built with Roo-Cline, ChatGPT and @zoharbabin
- Chart.js for data visualization
- Tailwind CSS for styling
- AWS Bedrock for AI capabilities

---

Made with ❤️ for the holidays