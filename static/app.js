// Initialize file upload handling
function init() {
    document.getElementById('chat-file').addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        // Display file name
        document.getElementById('file-name').textContent = file.name;
        
        // Show loading indicator
        document.getElementById('loading').classList.remove('hidden');
        
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
            
            // Immediately redirect to results page with the chat ID
            window.location.href = `/gh_static_front/index.html?chatid=${data.md5}`;
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to analyze chat. Please try again.');
            document.getElementById('loading').classList.add('hidden');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);