function createWordCloud(container, words) {
    container.innerHTML = `<canvas id="word-cloud-canvas" class="w-full rounded-lg bg-gray-50"></canvas>`;

    const canvas = document.getElementById('word-cloud-canvas');
    const ctx = canvas.getContext('2d');
    let hoveredWord = null;

    // Set canvas size with proper pixel ratio
    const pixelRatio = window.devicePixelRatio || 1;
    canvas.width = container.offsetWidth * pixelRatio;
    canvas.height = 400 * pixelRatio;
    canvas.style.width = container.offsetWidth + 'px';
    canvas.style.height = '400px';
    ctx.scale(pixelRatio, pixelRatio);

    // Physics settings for extra gentle floating
    const maxSpeed = 0.15;
    const baseAmplitude = 0.15;

    // Font weights for better variation
    const fontWeights = [300, 400, 500, 600, 700, 800];

    // Balanced winter/fall color palette
    const seasonalColors = [
        '#1e3d59', // deep blue
        '#8b4513', // saddle brown
        '#800020', // burgundy
        '#2f4f4f', // dark slate gray
        '#4a4e4d', // charcoal
        '#8b0000', // dark red
        '#4b0082', // indigo
        '#d2691e', // chocolate
        '#556b2f', // dark olive green
        '#a0522d', // sienna
        '#483d8b', // dark slate blue
        '#b8860b'  // dark goldenrod
    ];

    // Sort and prepare words
    const maxFreq = Math.max(...words.map(w => w.value));
    const gameWords = words
        .sort((a, b) => b.value - a.value)
        .slice(0, 30)
        .map(word => {
            // Scale font size based on frequency
            const frequencyRatio = word.value / maxFreq;
            const fontSize = Math.max(18, Math.min(52, 18 + frequencyRatio * 34));
            
            // Calculate font weight based on frequency
            const weightIndex = Math.min(
                fontWeights.length - 1,
                Math.floor(frequencyRatio * fontWeights.length)
            );
            const fontWeight = fontWeights[weightIndex];
            
            // Assign random seasonal color
            const color = seasonalColors[Math.floor(Math.random() * seasonalColors.length)];
            
            ctx.font = `${fontWeight} ${fontSize}px Arial`;
            const width = ctx.measureText(word.text).width;
            const height = fontSize;

            // Random gentle rotation (-5 to 5 degrees)
            const rotation = (Math.random() - 0.5) * 0.17;

            return {
                text: word.text,
                value: word.value,
                fontSize,
                fontWeight,
                width,
                height,
                x: Math.random() * (canvas.width / pixelRatio - width),
                y: Math.random() * (canvas.height / pixelRatio - height),
                rotation,
                color,
                // Individual floating parameters
                floatOffset: Math.random() * Math.PI * 2,
                floatSpeed: 0.2 + Math.random() * 0.3,
                amplitude: baseAmplitude * (0.8 + Math.random() * 0.4)
            };
        });

    // Mouse interaction
    let mousePos = { x: 0, y: 0 };

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mousePos.x = (e.clientX - rect.left) * (canvas.width / rect.width / pixelRatio);
        mousePos.y = (e.clientY - rect.top) * (canvas.height / rect.height / pixelRatio);

        // Check for hover
        hoveredWord = null;
        for (let i = gameWords.length - 1; i >= 0; i--) {
            if (isPointInWord(mousePos.x, mousePos.y, gameWords[i])) {
                hoveredWord = gameWords[i];
                canvas.style.cursor = 'pointer';
                break;
            }
        }
        if (!hoveredWord) {
            canvas.style.cursor = 'default';
        }
    });

    canvas.addEventListener('click', (e) => {
        if (hoveredWord) {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX;
            const y = e.clientY;
            createConfetti(x, y);
        }
    });

    function isPointInWord(x, y, word) {
        const dx = x - (word.x + word.width / 2);
        const dy = y - (word.y + word.height / 2);
        const rotatedX = dx * Math.cos(-word.rotation) - dy * Math.sin(-word.rotation);
        const rotatedY = dx * Math.sin(-word.rotation) + dy * Math.cos(-word.rotation);
        return Math.abs(rotatedX) < word.width / 2 && Math.abs(rotatedY) < word.height / 2;
    }

    // Animation loop
    let lastFrameTime = 0;
    const targetFPS = 60;
    const frameInterval = 1000 / targetFPS;

    function update(timestamp) {
        if (timestamp - lastFrameTime < frameInterval) {
            requestAnimationFrame(update);
            return;
        }
        lastFrameTime = timestamp;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update and render words
        gameWords.forEach(word => {
            // Gentle floating motion
            word.y += Math.sin(timestamp * 0.001 * word.floatSpeed + word.floatOffset) * word.amplitude;
            
            // Wrap around edges with smooth transition
            if (word.x + word.width < 0) word.x = canvas.width / pixelRatio;
            if (word.x > canvas.width / pixelRatio) word.x = -word.width;
            if (word.y + word.height < 0) word.y = canvas.height / pixelRatio;
            if (word.y > canvas.height / pixelRatio) word.y = -word.height;

            // Draw word with effects
            ctx.save();
            ctx.translate(word.x + word.width / 2, word.y + word.height / 2);
            ctx.rotate(word.rotation);

            // Draw hover highlight
            if (word === hoveredWord) {
                ctx.globalAlpha = 0.15;
                ctx.fillStyle = '#22c55e';
                ctx.beginPath();
                ctx.arc(0, 0, word.width / 1.5, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            // Draw word with shadow for better contrast
            ctx.font = `${word.fontWeight} ${word.fontSize}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Add subtle shadow
            ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
            ctx.shadowBlur = 2;
            ctx.shadowOffsetX = 1;
            ctx.shadowOffsetY = 1;
            
            ctx.fillStyle = word === hoveredWord ? '#22c55e' : word.color;
            ctx.fillText(word.text, 0, 0);
            
            // Reset shadow
            ctx.shadowColor = 'transparent';
            ctx.shadowBlur = 0;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 0;

            // Show enhanced popularity count on hover
            if (word === hoveredWord) {
                const popupText = `${word.value} times`;
                const popupFont = '14px Arial';
                ctx.font = popupFont;
                const popupWidth = ctx.measureText(popupText).width;
                const padding = 8;
                const height = 24;
                
                // Draw popup background with shadow
                ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
                ctx.shadowBlur = 4;
                ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
                ctx.beginPath();
                ctx.roundRect(
                    -popupWidth/2 - padding,
                    word.fontSize/2 + padding,
                    popupWidth + padding * 2,
                    height,
                    6
                );
                ctx.fill();
                ctx.shadowColor = 'transparent';
                
                // Draw popup text
                ctx.fillStyle = '#ffffff';
                ctx.fillText(
                    popupText,
                    0,
                    word.fontSize/2 + padding + height/2
                );
            }

            ctx.restore();
        });

        requestAnimationFrame(update);
    }

    // Start animation
    requestAnimationFrame(update);
}

// Simplified confetti effect
let lastConfettiTime = 0;
const CONFETTI_COOLDOWN = 300;

function createConfetti(x, y) {
    const now = Date.now();
    if (now - lastConfettiTime < CONFETTI_COOLDOWN) return;
    lastConfettiTime = now;

    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.left = '0';
    container.style.top = '0';
    container.style.pointerEvents = 'none';
    document.body.appendChild(container);
    
    for (let i = 0; i < 20; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'absolute w-1 h-1 pointer-events-none';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.left = `${x}px`;
        confetti.style.top = `${y}px`;
        
        const angle = Math.random() * Math.PI * 2;
        const velocity = 3 + Math.random() * 3;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        
        container.appendChild(confetti);
        
        let posX = x;
        let posY = y;
        let opacity = 1;
        
        function animate() {
            posX += vx;
            posY += vy + 0.5;
            opacity -= 0.02;
            
            confetti.style.transform = `translate(${posX - x}px, ${posY - y}px) rotate(${Math.random() * 360}deg)`;
            confetti.style.opacity = opacity;
            
            if (opacity > 0) {
                requestAnimationFrame(animate);
            } else {
                confetti.remove();
                if (!container.children.length) {
                    container.remove();
                }
            }
        }
        
        requestAnimationFrame(animate);
    }
}