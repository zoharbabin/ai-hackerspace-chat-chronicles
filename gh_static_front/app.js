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

// Initialize with available groups or load specific chat
async function init() {
    // Check for chatid in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('chatid');

    if (chatId) {
        // Hide group selection and load specific chat
        document.getElementById('group-selection').classList.add('hidden');
        await loadChatData(chatId);
    } else {
        // Show group selection dropdown
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

            await loadChatData(selectedFile);
        });
    }
}

// Load chat data from file
async function loadChatData(fileId) {
    // Show loading indicator
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');

    try {
        // Load the JSON data for the selected chat
        const response = await fetch(`analyzed_data/${fileId}.json`);
        if (!response.ok) {
            throw new Error('Failed to load chat data');
        }
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to load chat data. Please try again.');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
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
    displayMessageCategories(data);
    displayMediaStats(data);
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

function displayMediaStats(data) {
    if (!data.media_stats) {
        console.log('No media stats found');
        return;
    }

    // Display media distribution
    const distributionHtml = Object.entries(data.media_stats.media_by_type)
        .map(([type, count]) => {
            const percentage = data.media_stats.media_type_percentages[type];
            return `
                <div class="flex items-center justify-between p-2 bg-indigo-50 rounded hover:bg-indigo-100
                    transition-all duration-200 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                    <span class="font-medium capitalize">${type}</span>
                    <div class="text-sm">
                        <span class="font-semibold">${count}</span>
                        <span class="text-gray-600">(${percentage}%)</span>
                    </div>
                </div>
            `;
        })
        .join('');
    document.getElementById('media-distribution').innerHTML = distributionHtml;

    // Display top media sharers
    const sharersHtml = data.media_stats.top_media_sharers
        .map((user, index) => `
            <div class="flex items-center justify-between p-2 ${index % 2 === 0 ? 'bg-purple-50' : 'bg-purple-100'}
                rounded hover:bg-purple-200 transition-all duration-200 cursor-pointer"
                onclick="createConfetti(event.clientX, event.clientY)">
                <span class="font-medium">${user.name}</span>
                <span class="text-purple-700">${user.count} shared</span>
            </div>
        `)
        .join('');
    document.getElementById('top-media-sharers').innerHTML = sharersHtml;

    // Display most reacted media
    const reactedMediaHtml = data.media_stats.most_reacted_media
        .map(item => `
            <div class="p-3 bg-pink-50 rounded-lg hover:bg-pink-100 transition-all duration-200
                transform hover:scale-105 cursor-pointer" onclick="createConfetti(event.clientX, event.clientY)">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="font-medium capitalize">${item.type}</span>
                        <span class="text-gray-600 text-sm"> by ${item.sender}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-pink-600">❤️ ${item.reactions}</span>
                    </div>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                    ${item.timestamp}
                </div>
            </div>
        `)
        .join('');
    document.getElementById('most-reacted-media').innerHTML = reactedMediaHtml;
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

function displayMessageCategories(data) {
    if (!data.message_categories || data.message_categories.length === 0) {
        console.log('No message categories found');
        return;
    }

    const categoryColors = {
        'celebration': 'from-yellow-50 to-yellow-100',
        'business': 'from-blue-50 to-blue-100',
        'team': 'from-green-50 to-green-100',
        'strategic': 'from-purple-50 to-purple-100',
        'knowledge': 'from-red-50 to-red-100'
    };

    const getGradient = (category) => {
        const baseCategory = Object.keys(categoryColors).find(key =>
            category.toLowerCase().includes(key.toLowerCase())
        );
        return categoryColors[baseCategory] || 'from-gray-50 to-gray-100';
    };

    const categoriesHtml = data.message_categories
        .map(category => `
            <div class="mb-6">
                <div class="bg-gradient-to-r ${getGradient(category.category)} p-6 rounded-lg shadow-md
                    hover:shadow-lg transition-all duration-300 cursor-pointer"
                    onclick="createConfetti(event.clientX, event.clientY)">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">${category.category}</h3>
                            <p class="text-sm text-gray-600">${category.subcategory}</p>
                        </div>
                        <span class="text-sm font-semibold bg-white px-3 py-1 rounded-full shadow">
                            Impact: ${(category.impact_score * 100).toFixed(0)}%
                        </span>
                    </div>
                    
                    <div class="space-y-2">
                        ${category.messages.map(msg => `
                            <div class="bg-white bg-opacity-60 p-3 rounded">
                                <p class="text-gray-800">${msg}</p>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="mt-4 flex flex-wrap gap-2">
                        ${category.participants.map(participant => `
                            <span class="text-sm bg-white bg-opacity-70 px-2 py-1 rounded">
                                ${participant}
                            </span>
                        `).join('')}
                    </div>
                    
                    <div class="mt-4 text-sm text-gray-600 italic">
                        ${category.context}
                    </div>
                    
                    <div class="mt-2 text-xs text-gray-500">
                        ${category.timestamp}
                    </div>
                </div>
            </div>
        `)
        .join('');

    document.getElementById('message-categories').innerHTML = categoriesHtml;
}