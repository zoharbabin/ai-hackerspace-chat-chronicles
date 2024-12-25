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

// Store chart references
let activityChart = null;
let sentimentChart = null;

// Initialize with available groups
async function init() {
    const groupSelect = document.getElementById('group-select');
    
    // List of available groups with their filenames
    const groups = [
        {name: 'Agentic Robotics', file: 'Agentic Robotics.json'},
        {name: 'Ai Code Chat', file: 'Ai Code Chat.json'},
        {name: 'AI Startup Chat', file: 'AI Startup Chat.json'},
        {name: 'Breaking Ai News & Links', file: 'Breaking Ai News & Links.json'},
        {name: 'Events & Conferences', file: 'Events & Conferences.json'},
        {name: 'General Ai Chat', file: 'General Ai Chat.json'},
        {name: 'Solana AI hackathon', file: 'Solana AI hackathon.json'}
    ];

    // Clear existing options
    groupSelect.innerHTML = '<option value="">Choose a group...</option>';

    // Populate dropdown
    groups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.file;
        option.textContent = group.name;
        groupSelect.appendChild(option);
    });

    // Handle group selection
    groupSelect.addEventListener('change', async () => {
        const selectedFile = groupSelect.value;
        if (!selectedFile) {
            document.getElementById('results').classList.add('hidden');
            return;
        }

        // Show loading indicator
        document.getElementById('loading').classList.remove('hidden');
        document.getElementById('results').classList.add('hidden');

        try {
            // Load the JSON data for the selected group
            const response = await fetch(`analyzed_data/${selectedFile}`);
            if (!response.ok) {
                throw new Error('Failed to load group data');
            }
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load group data. Please try again.');
        } finally {
            document.getElementById('loading').classList.add('hidden');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

function displayResults(data) {
    // Show results container
    document.getElementById('results').classList.remove('hidden');
    
    // Destroy existing charts if they exist
    if (activityChart) {
        activityChart.destroy();
    }
    if (sentimentChart) {
        sentimentChart.destroy();
    }

    // Display activity timeline with enhanced interactivity
    const activityCtx = document.getElementById('activity-chart').getContext('2d');
    activityChart = new Chart(activityCtx, {
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
    sentimentChart = new Chart(sentimentCtx, {
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
    displaySharedLinks(data);
    
    // Display holiday greeting
    document.getElementById('holiday-greeting').textContent = data.holiday_greeting;

    // Display chat poem
    if (data.chat_poem) {
        document.getElementById('chat-poem').textContent = data.chat_poem;
    }
    
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
    if (!data.viral_messages) {
        console.log('No viral messages found');
        return;
    }
    
    const viralHtml = data.viral_messages
        .map(msg => {
            return `
                <div class="p-2 bg-purple-50 rounded hover:bg-purple-100 transition-all duration-200 cursor-pointer"
                    onclick="createConfetti(event.clientX, event.clientY)">
                    <div class="flex items-start gap-2">
                        <div class="flex-grow">
                            <p class="font-medium text-purple-900 mb-1">${msg.message}</p>
                            <div class="text-xs text-purple-600 flex items-center gap-2 mb-1">
                                <span class="inline-flex items-center">💬 ${msg.replies}</span>
                                <span class="inline-flex items-center">❤️ ${msg.reactions}</span>
                            </div>
                        </div>
                    </div>
                    <div class="text-sm text-gray-600 border-l-2 border-purple-200 pl-2 mt-1">
                        ${msg.thread.map(reply => `
                            <p class="text-sm py-0.5 hover:bg-purple-50 rounded">${reply}</p>
                        `).join('')}
                    </div>
                </div>
            `;
        })
        .join('');
    
    document.getElementById('viral-messages').innerHTML = viralHtml;
}

function displaySharedLinks(data) {
    if (!data.shared_links) {
        console.log('No shared links found');
        return;
    }
    
    const linksHtml = data.shared_links
        .map(link => `
            <div class="p-4 bg-blue-50 rounded-lg hover:shadow-lg transition-all duration-300
                transform hover:scale-105 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                <div class="flex items-start gap-4">
                    <div class="flex-grow">
                        <a href="${link.url}" target="_blank" class="text-blue-600 hover:text-blue-800 font-medium break-all">
                            ${link.url}
                        </a>
                        <div class="text-sm text-gray-600 mt-2">
                            <span class="inline-flex items-center mr-4">
                                <span class="mr-1">💬</span> ${link.replies} replies
                            </span>
                            <span class="inline-flex items-center">
                                <span class="mr-1">❤️</span> ${link.reactions} reactions
                            </span>
                        </div>
                        <div class="mt-2 text-sm text-gray-700">
                            <p class="italic">"${link.context}"</p>
                        </div>
                    </div>
                </div>
            </div>
        `)
        .join('');
    
    document.getElementById('shared-links').innerHTML = linksHtml;
}