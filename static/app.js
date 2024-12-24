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
    
    // Display activity timeline
    const activityCtx = document.getElementById('activity-chart').getContext('2d');
    new Chart(activityCtx, {
        type: 'line',
        data: {
            labels: Object.keys(data.activity_by_date),
            datasets: [{
                label: 'Messages',
                data: Object.values(data.activity_by_date),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Message Activity Over Time'
                }
            }
        }
    });
    
    // Display word cloud
    const words = data.word_cloud_data;
    const width = document.getElementById('word-cloud').offsetWidth;
    const height = 300;
    
    // Clear existing word cloud
    document.getElementById('word-cloud').innerHTML = '';
    
    // Create word cloud
    const layout = d3.layout.cloud()
        .size([width, height])
        .words(words.map(d => ({
            text: d.text,
            size: 10 + (d.value * 20 / Math.max(...words.map(w => w.value)))
        })))
        .padding(5)
        .rotate(() => 0)
        .fontSize(d => d.size)
        .on('end', draw);
    
    layout.start();
    
    function draw(words) {
        d3.select('#word-cloud')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width/2},${height/2})`)
            .selectAll('text')
            .data(words)
            .enter()
            .append('text')
            .style('font-size', d => `${d.size}px`)
            .style('fill', () => `hsl(${Math.random() * 360}, 70%, 50%)`)
            .attr('text-anchor', 'middle')
            .attr('transform', d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
            .text(d => d.text);
    }
    
    // Display top contributors
    const contributorsHtml = data.most_active_users
        .map((user, index) => `
            <div class="flex items-center justify-between p-2 ${index % 2 === 0 ? 'bg-gray-50' : ''}">
                <span class="font-semibold">${user.name}</span>
                <span class="text-gray-600">${user.count} messages</span>
            </div>
        `)
        .join('');
    document.getElementById('top-contributors').innerHTML = contributorsHtml;
    
    // Display emoji stats
    const emojiHtml = Object.entries(data.emoji_stats)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 8)
        .map(([emoji, count]) => `
            <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span class="text-2xl">${emoji}</span>
                <span class="font-semibold">${count}</span>
            </div>
        `)
        .join('');
    document.getElementById('emoji-stats').innerHTML = emojiHtml;
    
    // Display memorable moments
    const momentsHtml = data.memorable_moments
        .map(moment => `
            <div class="memory-card bg-gradient-to-br from-red-50 to-green-50 p-4 rounded-lg shadow hover:shadow-lg">
                <p class="text-gray-800">${moment}</p>
            </div>
        `)
        .join('');
    document.getElementById('memorable-moments').innerHTML = momentsHtml;
    
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

// Add confetti effect for special interactions
function createConfetti(x, y) {
    for (let i = 0; i < 30; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'absolute w-2 h-2 pointer-events-none';
        confetti.style.backgroundColor = `hsl(${Math.random() * 360}, 70%, 50%)`;
        confetti.style.left = `${x}px`;
        confetti.style.top = `${y}px`;
        
        const angle = Math.random() * Math.PI * 2;
        const velocity = 5 + Math.random() * 5;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        
        document.body.appendChild(confetti);
        
        let posX = x;
        let posY = y;
        let opacity = 1;
        
        function animate() {
            posX += vx;
            posY += vy + 1; // Add gravity
            opacity -= 0.02;
            
            confetti.style.transform = `translate(${posX - x}px, ${posY - y}px)`;
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