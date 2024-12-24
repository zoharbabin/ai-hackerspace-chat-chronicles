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
    
    // Display word cloud with game mechanics
    // Words are pre-filtered in the backend
    const words = data.word_cloud_data.sort((a, b) => b.value - a.value);
    const width = document.getElementById('word-cloud').offsetWidth;
    const height = 400; // Increased height for game UI

    // Clear and setup game container
    const container = document.getElementById('word-cloud');
    container.innerHTML = `
        <div class="mb-4 flex justify-between items-center">
            <div class="text-lg font-semibold">Score: <span id="word-game-score">0</span></div>
            <button id="start-word-game" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                Start Word Game
            </button>
        </div>
        <div id="word-game-prompt" class="mb-4 text-center hidden">
            <p class="text-lg mb-2">Can you guess which word appears more times?</p>
            <div class="flex justify-center gap-4">
                <button class="word-choice bg-gray-100 hover:bg-gray-200 px-6 py-3 rounded-lg"></button>
                <button class="word-choice bg-gray-100 hover:bg-gray-200 px-6 py-3 rounded-lg"></button>
            </div>
        </div>
        <div id="word-cloud-svg"></div>
    `;

    let gameScore = 0;
    let isGameActive = false;
    
    // Calculate font sizes with better distribution
    const maxFreq = Math.max(...words.map(w => w.value));
    const minFreq = Math.min(...words.map(w => w.value));
    const fontScale = d3.scaleLog()
        .domain([minFreq, maxFreq])
        .range([20, 60]); // Increased font size range for better visibility of meaningful words

    // Create word cloud with improved layout for filtered data
    const layout = d3.layout.cloud()
        .size([width, height])
        .words(words.map(d => ({
            text: d.text,
            size: fontScale(d.value),
            value: d.value,
            guessed: false
        })))
        .padding(10) // More padding since we have fewer but more meaningful words
        .rotate(() => Math.random() > 0.8 ? 0 : 90) // Further reduce rotated words for readability
        .fontSize(d => d.size)
        .spiral('archimedean') // Switch to archimedean spiral for more natural word placement
        .on('end', draw);
    
    layout.start();
    
    function draw(words) {
        const svg = d3.select('#word-cloud-svg')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width/2},${height/2})`);

        const texts = svg.selectAll('text')
            .data(words)
            .enter()
            .append('text')
            .style('font-size', d => `${d.size}px`)
            .style('fill', d => d.guessed ? '#22c55e' : `hsl(${Math.random() * 360}, 70%, 50%)`)
            .attr('text-anchor', 'middle')
            .attr('transform', d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
            .text(d => d.text)
            .style('cursor', 'pointer')
            .style('transition', 'all 0.3s ease')
            .style('opacity', 0.8);

        // Add hover and click effects
        texts.on('mouseover', function() {
                d3.select(this)
                    .style('transform', 'scale(1.25)')
                    .style('filter', 'brightness(1.2)')
                    .style('opacity', 1);
            })
            .on('mouseout', function() {
                d3.select(this)
                    .style('transform', 'scale(1)')
                    .style('filter', 'brightness(1)')
                    .style('opacity', 0.8);
            })
            .on('click', function(event, d) {
                createConfetti(event.pageX, event.pageY);
                
                // Calculate additional insights
                const avgWordLength = words.reduce((sum, w) => sum + w.text.length, 0) / words.length;
                const maxValue = Math.max(...words.map(w => w.value));
                const percentageOfMax = ((d.value / maxValue) * 100).toFixed(1);
                
                showWordStats(d, {
                    frequency: d.value,
                    percentageOfMax,
                    length: d.text.length,
                    avgLength: avgWordLength.toFixed(1),
                    rank: words.sort((a, b) => b.value - a.value)
                              .findIndex(w => w.text === d.text) + 1
                }, event.pageX, event.pageY);
            });

        // Setup word guessing game
        document.getElementById('start-word-game').addEventListener('click', () => {
            if (!isGameActive) {
                startWordGame(words, texts);
            }
        });
    }

    function showWordStats(word, stats, x, y) {
        const popup = document.createElement('div');
        popup.className = 'fixed bg-white p-4 rounded-lg shadow-lg z-50 transition-opacity duration-300 max-w-xs';
        popup.style.left = `${x}px`;
        popup.style.top = `${y - 40}px`;
        
        popup.innerHTML = `
            <h3 class="font-bold text-lg mb-2">"${word.text}" Stats</h3>
            <ul class="space-y-1 text-sm">
                <li>🔄 Appears ${stats.frequency} times</li>
                <li>📊 ${stats.percentageOfMax}% of most frequent word</li>
                <li>📏 Length: ${stats.length} (avg: ${stats.avgLength})</li>
                <li>🏆 Rank: #${stats.rank} most frequent</li>
            </ul>
        `;
        
        document.body.appendChild(popup);
        
        requestAnimationFrame(() => {
            popup.style.opacity = '1';
        });
        
        setTimeout(() => {
            popup.style.opacity = '0';
            setTimeout(() => popup.remove(), 300);
        }, 3000);
    }

    function startWordGame(words, texts) {
        isGameActive = true;
        const gamePrompt = document.getElementById('word-game-prompt');
        const choices = gamePrompt.querySelectorAll('.word-choice');
        const startBtn = document.getElementById('start-word-game');
        
        startBtn.textContent = 'Game Active';
        startBtn.classList.remove('bg-blue-500', 'hover:bg-blue-600');
        startBtn.classList.add('bg-green-500');
        gamePrompt.classList.remove('hidden');

        function newRound() {
            // Select two random unguessed words
            const unguessedWords = words.filter(w => !w.guessed);
            if (unguessedWords.length < 2) {
                endGame();
                return;
            }

            const word1 = unguessedWords[Math.floor(Math.random() * unguessedWords.length)];
            let word2;
            do {
                word2 = unguessedWords[Math.floor(Math.random() * unguessedWords.length)];
            } while (word2 === word1);

            // Randomly assign words to buttons
            const [btnWord1, btnWord2] = Math.random() > 0.5 ? [word1, word2] : [word2, word1];
            
            choices[0].textContent = btnWord1.text;
            choices[1].textContent = btnWord2.text;

            // Add click handlers
            choices.forEach(btn => {
                btn.onclick = function() {
                    const selectedWord = words.find(w => w.text === this.textContent);
                    const otherWord = words.find(w =>
                        w.text === (this === choices[0] ? choices[1].textContent : choices[0].textContent)
                    );

                    if (selectedWord.value > otherWord.value) {
                        gameScore += 100;
                        createConfetti(window.innerWidth / 2, window.innerHeight / 2);
                    } else {
                        gameScore = Math.max(0, gameScore - 50);
                    }

                    document.getElementById('word-game-score').textContent = gameScore;

                    // Mark words as guessed
                    selectedWord.guessed = true;
                    otherWord.guessed = true;

                    // Update word colors
                    texts.filter(t => t.text === selectedWord.text || t.text === otherWord.text)
                         .style('fill', '#22c55e');

                    // Start new round
                    setTimeout(newRound, 1000);
                };
            });
        }

        function endGame() {
            isGameActive = false;
            gamePrompt.classList.add('hidden');
            startBtn.textContent = 'Start Word Game';
            startBtn.classList.remove('bg-green-500');
            startBtn.classList.add('bg-blue-500', 'hover:bg-blue-600');
            
            showPopup(`Game Over! Final Score: ${gameScore}`, window.innerWidth / 2, window.innerHeight / 2);
            
            // Reset game state
            words.forEach(w => w.guessed = false);
            texts.style('fill', d => `hsl(${Math.random() * 360}, 70%, 50%)`);
            gameScore = 0;
            document.getElementById('word-game-score').textContent = '0';
        }

        newRound();
    }
    
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

    // Rest of the display functions...
    displayTopContributors(data);
    displayEmojiStats(data);
    displayMemorableMoments(data);
    displayHappiestDays(data);
    displaySaddestDays(data);
    
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