# WhatsApp Holiday Chat Analyzer 🎄✨

A festive web application that analyzes WhatsApp chat exports to create beautiful visualizations and AI-powered insights about your group conversations. Perfect for celebrating your group's year in messages!

This was also an experiement of writing an entire project where:  

1. ChatGPT o1-Pro was the Product Manager  
2. Roo-Cline powered by Claude 3.5 Sonnet was the Developer and QA  
3. A human ([@zoharbabin](https://github.com/zoharbabin/)) as the investor and manager  

## Features 🌟

- **Interactive Timeline**: Visualize chat activity over time
- **Word Cloud**: See the most frequently used words in your conversations
- **Top Contributors**: Identify the most active participants
- **Emoji Analysis**: Track the most popular emojis
- **AI-Powered Insights**: Get memorable moments and context-aware holiday greetings using Claude AI
- **Festive UI**: Enjoy snow effects and holiday-themed animations
- **Real-time Analysis**: Process and visualize chat data instantly
- **Responsive Design**: Works beautifully on both desktop and mobile

## Tech Stack 🛠

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **AI/ML**: Claude AI via AWS Bedrock
- **Visualization**: Chart.js, D3.js
- **Container**: Docker support
- **Dependencies**: See requirements.txt for full list

## Prerequisites 📋

- Python 3.9+
- AWS Account with Bedrock access
- AWS credentials (access key and secret key)
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

4. Create a .env file with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
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
docker run -p 8000:8000 -e AWS_ACCESS_KEY_ID=your_access_key -e AWS_SECRET_ACCESS_KEY=your_secret_key whatsapp-analyzer
```

## Usage 📱

1. Export your WhatsApp chat:
   - Open WhatsApp group
   - Go to Group Info
   - Scroll down to "Export Chat"
   - Choose "Without Media"

2. Upload the exported .txt file to the application

3. View your personalized chat analysis with:
   - Activity timeline
   - Word cloud
   - Top contributors
   - Emoji statistics
   - AI-generated memorable moments
   - Custom holiday greeting

## Project Structure 📁

```
holiday-ai-hackerspace/
├── main.py              # FastAPI application and backend logic
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── .env               # Environment variables (create this)
├── .gitignore        # Git ignore rules
├── static/           # Frontend assets
│   ├── index.html    # Main HTML file
│   └── app.js        # Frontend JavaScript
└── cache/           # Cache directory for API responses
```

## Development 🔧

### Backend (main.py)
- FastAPI application with CORS support
- Structured logging with color formatting
- Error handling and input validation
- Caching for API responses
- WhatsApp chat parsing with multiple timestamp formats
- Integration with AWS Bedrock for AI analysis

### Frontend (static/)
- Responsive design with Tailwind CSS
- Interactive visualizations with Chart.js and D3.js
- Real-time data processing
- Festive animations and effects
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

1. [ ] Support for more chat export formats (Facebook Messanger, Discord, etc.)
2. [ ] Export reports as PDF
3. [ ] More AI-powered insights and additional visualization types

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 💝

- Built with Roo-Cline, ChatGPT and @zoharbabin
- Visualization libraries: Chart.js and D3.js
- Tailwind CSS for styling

---

Made with ❤️ for the holidays