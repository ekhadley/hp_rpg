// Connect to SocketIO server
const socket = io();

// DOM elements
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const messageForm = document.getElementById('message-form');
// Removed tool details variables
const newStoryBtn = document.getElementById('new-story-btn');
const createStoryContainer = document.getElementById('create-story-container');
const storyList = document.getElementById('story-list');
const createStoryForm = document.getElementById('create-story-form');
const exportButton = document.getElementById('export-button');

// Store conversation history
let conversationHistory = [];

// Variables for managing the narrator's message state
let currentNarratorMessageElement = null;
let currentStory = null;

// Story selection
if (storyList) {
    storyList.addEventListener('click', function(e) {
        let storyItem = e.target.closest('.story-item');
        if (storyItem) {
            const story = storyItem.getAttribute('data-story');
            window.location.href = `/select/${story}`;
        }
    });
}

// New story button
if (newStoryBtn) {
    newStoryBtn.addEventListener('click', function() {
        createStoryContainer.classList.toggle('active');
    });
}

// Event listeners for messaging
if (messageForm) {
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message) {
            socket.emit('user_message', { message });
            userInput.value = '';
        }
    });
}

// Removed tool toggle event listener

// Socket events
socket.on('connect', function() {
    console.log('Connected to server');
    
    // We no longer show typing indicator on connect - we'll wait for server events
});

socket.on('story_list_update', function(data) {
    updateStoryList(data.stories);
});

socket.on('story_selected', function(data) {
    currentStory = data.story;
    if (document.getElementById('current-story-title')) {
        document.getElementById('current-story-title').textContent = data.story;
    }
    // Clear chat history when switching stories
    if (chatHistory) {
        chatHistory.innerHTML = '';
    }
});

// New event to show typing indicator when processing starts
socket.on('processing_started', function() {
    if (chatHistory) {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatHistory.appendChild(typingIndicator);
        scrollToBottom();
    }
});

// Event when assistant is fully initialized and ready
socket.on('assistant_ready', function() {
    // Remove typing indicator if assistant is ready without sending any text
    // (which happens when loading an existing completed story)
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }

});

socket.on('user_message_received', function(data) {
    addUserMessage(data.message);
    
    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: data.message,
        timestamp: new Date().toISOString()
    });
});

socket.on('text_start', function() {
    console.log('Narrator switched to outputting text');

    
    // Create a new narrator message element
    currentNarratorMessageElement = document.createElement('div');
    currentNarratorMessageElement.className = 'message narrator-message';
    currentNarratorMessageElement.style.display = 'none'; // Hide until we get content
    chatHistory.appendChild(currentNarratorMessageElement);
    
    // Scroll to bottom
    scrollToBottom();
});

// Store the raw content to avoid extra spaces
let accumulatedContent = '';

// Track the last received timestamp to prevent duplicate/out-of-order chunks
let lastTimestamp = 0;

socket.on('assistant_text', function(data) {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    // Show and update the narrator message
    if (currentNarratorMessageElement) {
        currentNarratorMessageElement.style.display = 'block';
        
        // Make sure we process text chunks in the order they were sent
        if (data.timestamp && data.timestamp < lastTimestamp) {
            console.log('Discarding out-of-order text chunk');
            return;
        }
        
        if (data.timestamp) {
            lastTimestamp = data.timestamp;
        }
        
        // Accumulate the raw text
        accumulatedContent += data.text;

        // Special processing for narration tags
        // if processedContesnt has a start narration tag but no end, add a closing tag
        let processedContent = accumulatedContent;
        if (processedContent.includes('<narration>') && !processedContent.includes('</narration>')) {
            processedContent += '</narration>';
        }
        processedContent = processedContent.replace(/<narration>(.*?)<\/narration>/gs, function(_, narrationContent) {
            // Clean up the narration text first
            let narrationText = narrationContent;
            
            // Split into paragraphs by double newlines or multiple whitespace
            let paragraphs = narrationText.split(/\n\s*\n|\n{2,}/g);
            
            // Wrap each paragraph in <p> tags
            let formattedNarration = paragraphs.map(paragraph => {
                // Clean each paragraph of extra spaces that might appear between streamed chunks
                let cleanParagraph = paragraph.replace(/\s+/g, ' ').trim();
                if (cleanParagraph) {
                    return '<p>' + cleanParagraph + '</p>';
                }
                return '';
            }).join('');
            
            return '<div class="book-narration">' + formattedNarration + '</div>';
        });
        
        // Convert accumulated markdown to HTML - using the FULL accumulated content each time
        try {
            const formattedText = marked.parse(processedContent);
            currentNarratorMessageElement.innerHTML = formattedText;
        } catch (e) {
            console.error('Error parsing markdown:', e);
            currentNarratorMessageElement.textContent = processedContent;
        }
        
        // Scroll to bottom
        scrollToBottom();
    }
});

socket.on('tool_request', function(data) {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    console.log('Tool requested:', data);
    // We don't show tool requests in the UI
    accumulatedContent = '';
});

socket.on('tool_submit', function(data) {
    accumulatedContent = '';
    if (typingIndicator = document.querySelector('.typing-indicator')) {
        typingIndicator.remove();
    }
    console.log('Tool output:', data);
    
    // Display tool operations directly in chat
    data.tools.forEach(tool => {
        // Only show dice rolls with their results, other tools just show a brief message
        if (tool.name === 'roll_dice') {
            const diceElement = document.createElement('div');
            diceElement.className = 'dice-roll';
            diceElement.innerHTML = `🎲 Rolled ${tool.inputs.dice}: <strong>${tool.result}</strong>`;
            chatHistory.appendChild(diceElement);
            
            // Add tool use to conversation history
            conversationHistory.push({
                role: 'tool',
                name: tool.name,
                inputs: tool.inputs,
                result: tool.result,
                timestamp: new Date().toISOString()
            });
        } else {
            // For other tools, just show a simple message
            const toolElement = document.createElement('div');
            toolElement.className = 'tool-message';
            toolElement.innerHTML = `Used ${tool.name}...`;
            chatHistory.appendChild(toolElement);
            
            // Add tool use to conversation history
            conversationHistory.push({
                role: 'tool',
                name: tool.name,
                inputs: tool.inputs,
                result: tool.result,
                timestamp: new Date().toISOString()
            });
        }
    });
    
    // Scroll to bottom after adding tool messages
    scrollToBottom();
});

socket.on('turn_end', function() {
    // Add narrator's complete response to conversation history
    if (currentNarratorMessageElement) {
        conversationHistory.push({
            role: 'assistant',
            content: accumulatedContent,
            timestamp: new Date().toISOString()
        });
    }
    
    currentNarratorMessageElement = null;
    
    // Reset accumulated content for next turn
    accumulatedContent = '';
    
    // Enable user input
    if (userInput) {
        userInput.disabled = false;
        userInput.focus();
    }
});

// Helper functions
function addUserMessage(message) {
    if (!chatHistory) return;
    
    // Create container div for message alignment
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message';
    messageContainer.style.display = 'flex';
    messageContainer.style.justifyContent = 'flex-end';
    
    // Create the actual message element
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';
    messageElement.textContent = message;
    
    // Add message to container, then container to chat
    messageContainer.appendChild(messageElement);
    chatHistory.appendChild(messageContainer);
    scrollToBottom();
    
    // Disable input while waiting for response
    if (userInput) {
        userInput.disabled = true;
    }
}

function scrollToBottom() {
    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

function updateStoryList(stories) {
    if (!storyList) return;
    
    storyList.innerHTML = '';
    stories.forEach(story => {
        const active = currentStory === story ? 'active' : '';
        storyList.innerHTML += `
            <li class="story-item ${active}" data-story="${story}">
                <i class="fas fa-book"></i>
                <span>${story}</span>
            </li>
        `;
    });
}

// Export conversation history to console
function exportConversation() {
    console.log('Conversation History:');
    console.log(JSON.stringify(conversationHistory, null, 2));
    
    // Create a time-stamped filename for downloading (optional feature)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${currentStory || 'conversation'}-${timestamp}.json`;
    
    // alert(`Conversation JSON has been printed to the console (F12)`);
}

// Initial setup
window.onload = function() {
    if (userInput) {
        userInput.focus();
    }
    
    // Add event listener for export button
    if (exportButton) {
        exportButton.addEventListener('click', exportConversation);
    }
};
