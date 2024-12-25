// Test data for direct file loading
const testData = {
    word_cloud_data: [
        { text: "Hello", value: 100 },
        { text: "World", value: 80 },
        { text: "JavaScript", value: 120 },
        { text: "Programming", value: 90 },
        { text: "Interactive", value: 70 },
        { text: "Animation", value: 85 },
        { text: "Physics", value: 95 },
        { text: "Canvas", value: 75 },
        { text: "Game", value: 110 },
        { text: "Fun", value: 65 }
    ],
    activity_by_date: {
        "2023-01-01": 45,
        "2023-01-02": 67,
        "2023-01-03": 89,
        "2023-01-04": 76,
        "2023-01-05": 123
    },
    sentiment_over_time: [
        { date: "2023-01-01", sentiment: 0.8 },
        { date: "2023-01-02", sentiment: 0.3 },
        { date: "2023-01-03", sentiment: -0.2 },
        { date: "2023-01-04", sentiment: 0.5 },
        { date: "2023-01-05", sentiment: 0.9 }
    ],
    most_active_users: [
        { name: "User 1", count: 234 },
        { name: "User 2", count: 187 },
        { name: "User 3", count: 156 }
    ],
    emoji_stats: {
        "😊": 45,
        "❤️": 34,
        "👍": 28,
        "🎉": 23
    },
    memorable_moments: [
        "Remember that amazing project we finished!",
        "The virtual party was so much fun!",
        "Great team collaboration day"
    ],
    happiest_days: [
        {
            date: "2023-01-05",
            sentiment: 0.9,
            messages: ["What an amazing achievement!", "Great work everyone!"]
        }
    ],
    saddest_days: [
        {
            date: "2023-01-03",
            sentiment: -0.2,
            messages: ["Tough challenges ahead", "We'll get through this together"]
        }
    ],
    holiday_greeting: "Happy Holidays! 🎄✨ What an amazing year of collaboration!",
    viral_messages: [
        {
            message: "ARK just released a report on humanoid robots: \"If humanoid robots are able to operate at scale, they could generate ~$24 trillion in revenues\"",
            replies: 3,
            reactions: 2,
            thread: [
                "https://en.wikipedia.org/wiki/Cathie_Wood\nShe's an amazing CEO. I bought all her ETFs for the long in 2023 Q4.",
                "If robots replace human workers, and humans lose their income, who will have the purchasing power to buy the increased output?",
                "There is just so much room there though and niche specific needs, I doubt openAI can actually steamroll and own the entire space."
            ]
        },
        {
            message: "Has anyone used aider.chat? If yes, what is your opinion on it?",
            replies: 3,
            reactions: 1,
            thread: [
                "Yes RuV and some of us use it as code and debug ide",
                "aider.chat is fantastic. It's the glue between the coding model and the software development process. Working with aider feels very natural as a software dev and it's an incredible productivity booster.",
                "🙏"
            ]
        },
        {
            message: "Anyone have some best practices to share regarding using agents for customer service?",
            replies: 4,
            reactions: 0,
            thread: [
                "I have an approach that I'd like to run by anyone doing agents...",
                "1. Start by trying to get everything you need done by shoving everything in one prompt.\n2. Then check what the failure cases are. 3. If the failure case can easily be solved by modifying the prompt, do that 4. Otherwise start to add layers to your system, e.g. routing for different types of queries",
                "Yeah I think this is true of prompt engineering generally. Start by just asking ai to do the thing you want and see what happens!"
            ]
        }
    ]
};

// Snow effect
function createSnowflakes() {
    const snowContainer = document.getElementById('snow-container');
    const snowflake = document.createElement('div');
    snowflake.className = 'snowflake';
    snowflake.innerHTML = '❄';
    
    // Random position and animation duration
    const startPositionLeft = Math.random() * window.innerWidth;
    const animationDuration = Math.random() * 3 + 2; // 2-5 seconds
    
    snowflake.style.left = startPositionLeft + 'px';
    snowflake.style.animationDuration = animationDuration + 's';
    
    snowContainer.appendChild(snowflake);
    
    // Remove snowflake after animation
    setTimeout(() => {
        snowflake.remove();
    }, animationDuration * 1000);
}

// Create snowflakes periodically
setInterval(createSnowflakes, 200);

// Initialize with test data or handle file upload
function init() {
    // For direct file testing, show results immediately
    if (window.location.protocol === 'file:') {
        console.log('Loading test data:', testData);
        document.getElementById('results').classList.remove('hidden');
        displayResults(testData);
    } else {
        // File upload handling
        document.getElementById('chat-file').addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) return;
            
            // Display file name
            document.getElementById('file-name').textContent = file.name;
            
            // Show loading indicator
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                // Send file to backend
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Analysis failed');
                }
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to analyze chat. Please try again.');
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

function displayResults(data) {
    // Show results container
    document.getElementById('results').classList.remove('hidden');
    
    // Display activity timeline with enhanced interactivity
    const activityCtx = document.getElementById('activity-chart').getContext('2d');
    new Chart(activityCtx, {
        type: 'line',
        data: {
            labels: Object.keys(data.activity_by_date),
            datasets: [{
                label: 'Messages',
                data: Object.values(data.activity_by_date),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                pointHoverRadius: 10,
                pointHoverBackgroundColor: 'rgb(75, 192, 192)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Message Activity Over Time'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const messages = context.raw;
                            return `${messages} messages sent ${messages > 10 ? '🔥' : ''}`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const date = Object.keys(data.activity_by_date)[index];
                    const messages = Object.values(data.activity_by_date)[index];
                    createConfetti(event.x, event.y);
                    showPopup(`On ${date}, there were ${messages} messages sent!`, event.x, event.y);
                }
            }
        }
    });
    
    // Create floating word cloud
    const wordCloudContainer = document.getElementById('word-cloud');
    wordCloudContainer.innerHTML = '<div class="text-gray-600 mb-4">Click words to celebrate them with confetti! Hover to see how many times they appear.</div>';
    createWordCloud(wordCloudContainer, data.word_cloud_data);
    
    // Display sentiment over time with enhanced interactivity
    const sentimentCtx = document.getElementById('sentiment-chart').getContext('2d');
    new Chart(sentimentCtx, {
        type: 'line',
        data: {
            labels: data.sentiment_over_time.map(d => d.date),
            datasets: [{
                label: 'Group Mood',
                data: data.sentiment_over_time.map(d => d.sentiment),
                borderColor: 'rgb(147, 51, 234)',
                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                fill: true,
                tension: 0.4,
                pointHoverRadius: 10
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Group Mood Timeline'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const sentiment = context.raw;
                            let mood = 'Neutral 😐';
                            if (sentiment > 0.5) mood = 'Very Positive 🤗';
                            else if (sentiment > 0) mood = 'Positive 😊';
                            else if (sentiment < -0.5) mood = 'Very Negative 😢';
                            else if (sentiment < 0) mood = 'Negative 😕';
                            return `Mood: ${mood} (${sentiment.toFixed(2)})`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: -1,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Sentiment Score'
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const date = data.sentiment_over_time[index].date;
                    const sentiment = data.sentiment_over_time[index].sentiment;
                    let emoji = '😐';
                    if (sentiment > 0.5) emoji = '🤗';
                    else if (sentiment > 0) emoji = '😊';
                    else if (sentiment < -0.5) emoji = '😢';
                    else if (sentiment < 0) emoji = '😕';
                    createConfetti(event.x, event.y);
                    showPopup(`${date}: The group was feeling ${emoji}`, event.x, event.y);
                }
            }
        }
    });

    // Display all sections
    displayTopContributors(data);
    displayEmojiStats(data);
    displayMemorableMoments(data);
    displayHappiestDays(data);
    displaySaddestDays(data);
    displayViralMessages(data);
    
    // Display holiday greeting
    document.getElementById('holiday-greeting').textContent = data.holiday_greeting;
    
    // Add some festive animation
    setTimeout(() => {
        document.querySelectorAll('.memory-card').forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
        });
    }, 500);
}

// Helper function to show interactive popups
function showPopup(text, x, y) {
    const popup = document.createElement('div');
    popup.className = 'fixed bg-white p-3 rounded-lg shadow-lg text-sm z-50 transition-opacity duration-300';
    popup.style.left = `${x}px`;
    popup.style.top = `${y - 40}px`;
    popup.textContent = text;
    
    document.body.appendChild(popup);
    
    // Fade in
    requestAnimationFrame(() => {
        popup.style.opacity = '1';
    });
    
    // Remove after animation
    setTimeout(() => {
        popup.style.opacity = '0';
        setTimeout(() => popup.remove(), 300);
    }, 2000);
}

// Enhanced confetti effect
function createConfetti(x, y) {
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
    
    for (let i = 0; i < 30; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'absolute w-2 h-2 pointer-events-none';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.left = `${x}px`;
        confetti.style.top = `${y}px`;
        
        const angle = Math.random() * Math.PI * 2;
        const velocity = 5 + Math.random() * 5;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        const rotation = Math.random() * 360;
        
        document.body.appendChild(confetti);
        
        let posX = x;
        let posY = y;
        let opacity = 1;
        let currentRotation = rotation;
        
        function animate() {
            posX += vx;
            posY += vy + 1; // Add gravity
            opacity -= 0.02;
            currentRotation += 5;
            
            confetti.style.transform = `translate(${posX - x}px, ${posY - y}px) rotate(${currentRotation}deg)`;
            confetti.style.opacity = opacity;
            
            if (opacity > 0) {
                requestAnimationFrame(animate);
            } else {
                confetti.remove();
            }
        }
        
        requestAnimationFrame(animate);
    }
}

// Add confetti to memorable moments on click
document.addEventListener('click', (e) => {
    if (e.target.closest('.memory-card')) {
        createConfetti(e.clientX, e.clientY);
    }
});

// Helper functions for displaying other sections
function displayTopContributors(data) {
    const contributorsHtml = data.most_active_users
        .map((user, index) => `
            <div class="flex items-center justify-between p-2 ${index % 2 === 0 ? 'bg-gray-50' : ''} 
                hover:bg-gray-100 transition-colors duration-200 cursor-pointer"
                onclick="createConfetti(event.clientX, event.clientY)">
                <span class="font-semibold">${user.name}</span>
                <span class="text-gray-600">${user.count} messages</span>
            </div>
        `)
        .join('');
    document.getElementById('top-contributors').innerHTML = contributorsHtml;
}

function displayEmojiStats(data) {
    const emojiHtml = Object.entries(data.emoji_stats)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 8)
        .map(([emoji, count]) => `
            <div class="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 
                transition-all duration-200 transform hover:scale-105 cursor-pointer"
                onclick="createConfetti(event.clientX, event.clientY)">
                <span class="text-2xl">${emoji}</span>
                <span class="font-semibold">${count}</span>
            </div>
        `)
        .join('');
    document.getElementById('emoji-stats').innerHTML = emojiHtml;
}

function displayMemorableMoments(data) {
    const momentsHtml = data.memorable_moments
        .map(moment => `
            <div class="memory-card bg-gradient-to-br from-red-50 to-green-50 p-4 rounded-lg shadow 
                hover:shadow-lg transition-all duration-300 transform hover:scale-105 cursor-pointer">
                <p class="text-gray-800">${moment}</p>
            </div>
        `)
        .join('');
    document.getElementById('memorable-moments').innerHTML = momentsHtml;
}

function displayHappiestDays(data) {
    const happiestHtml = data.happiest_days
        .map(day => `
            <div class="p-4 bg-green-50 rounded-lg hover:shadow-lg transition-all duration-300 
                transform hover:scale-105 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold text-green-700">${day.date}</span>
                    <span class="text-sm text-green-600">Score: ${day.sentiment.toFixed(2)} 🎉</span>
                </div>
                <div class="text-sm text-gray-600 space-y-1">
                    ${day.messages.map(msg => `<p>"${msg}"</p>`).join('')}
                </div>
            </div>
        `)
        .join('');
    document.getElementById('happiest-days').innerHTML = happiestHtml;
}

function displaySaddestDays(data) {
    const saddestHtml = data.saddest_days
        .map(day => `
            <div class="p-4 bg-blue-50 rounded-lg hover:shadow-lg transition-all duration-300 
                transform hover:scale-105 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold text-blue-700">${day.date}</span>
                    <span class="text-sm text-blue-600">Score: ${day.sentiment.toFixed(2)} 💙</span>
                </div>
                <div class="text-sm text-gray-600 space-y-1">
                    ${day.messages.map(msg => `<p>"${msg}"</p>`).join('')}
                </div>
            </div>
        `)
        .join('');
    document.getElementById('saddest-days').innerHTML = saddestHtml;
}

function displayViralMessages(data) {
    console.log('Displaying viral messages:', data.viral_messages);
    if (!data.viral_messages) {
        console.log('No viral messages found');
        return;
    }
    
    const viralHtml = data.viral_messages
        .map(msg => {
            console.log('Processing message:', msg);
            return `
                <div class="p-4 bg-purple-50 rounded-lg hover:shadow-lg transition-all duration-300
                    transform hover:scale-105 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-semibold text-purple-700">${msg.message}</span>
                        <div class="flex space-x-3">
                            <span class="text-sm text-purple-600">💬 ${msg.replies}</span>
                            <span class="text-sm text-purple-600">❤️ ${msg.reactions}</span>
                        </div>
                    </div>
                    <div class="text-sm text-gray-600 space-y-1 mt-3 bg-white p-3 rounded">
                        ${msg.thread.map(reply => `<p class="hover:bg-purple-50 p-1 rounded">${reply}</p>`).join('')}
                    </div>
                </div>
            `;
        })
        .join('');
    
    console.log('Generated HTML:', viralHtml);
    const container = document.getElementById('viral-messages');
    console.log('Container element:', container);
    container.innerHTML = viralHtml;
}