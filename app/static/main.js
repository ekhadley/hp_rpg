// Connect to SocketIO server
const socket = io();

// DOM elements
const welcomeWrapper = document.getElementById('welcome-container');
const chatHeader = document.getElementById('chat-header');
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const messageForm = document.getElementById('message-form');
const newStoryBtn = document.getElementById('new-story-btn');
const createStoryBtn = document.getElementById('create-story-btn');
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
            let storyTitle = storyItem.getAttribute('data-story');
            console.log('Selected story:', storyTitle);
            socket.emit('select_story', { "selected_story": storyTitle });
            // Clear chat history when switching stories
            if (document.getElementById('current-story-title')) {
                document.getElementById('current-story-title').textContent = storyTitle;
            }
            if (chatHistory) {
                chatHistory.innerHTML = '';
            }
            // Hide welcome wrapper and show chat wrapper
            if (welcomeWrapper) {
                welcomeWrapper.style.display = 'none';
            }
            if (chatHeader) {
                chatHeader.style.display = 'flex';
            }
            showTypingIndicator();
        }
    });
}

// New story button
if (newStoryBtn) {
    newStoryBtn.addEventListener('click', function() {
        createStoryContainer.classList.toggle('active');
    });
}

if (createStoryBtn) {
    createStoryBtn.addEventListener('click', function() {
        //e.preventDefault();
        new_story_name = document.getElementById('new_story_name').value;
        createStoryContainer.classList.remove('active');
        socket.emit('create_story', { story_name: new_story_name });
        createStoryContainer.classList.remove('active');
        addNewStory({ story_name: new_story_name });
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

            addUserMessage(message);
            conversationHistory.push({
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });
            scrollToBottom()
        }
    });
}

socket.on('conversation_history', function(data) {
    console.log('Loading conversation history:', data.history);
    
    // Clear existing conversation history in UI
    conversationHistory = [];
    
    // Render each message in chronological order
    data.history.forEach(function(message) {
        if (message.role === 'user') {
            addUserMessage(message.content, false); // Don't disable input when loading history
        } else if (message.role === 'assistant') {
            addAssistantMessageFromHistory(message.content);
        }
        // Add to local conversation history
        conversationHistory.push({
            role: message.role,
            content: message.content,
            timestamp: message.timestamp || new Date().toISOString()
        });
    });
    
    scrollToBottom();
});

socket.on('assistant_ready', function() {
    hideTypingIndicator();
    //accumulatedContent = '';
    //currentNarratorMessageElement = null;
});

socket.on('text_start', function() {
    console.log('Narrator switched to outputting text');
    
    // Create a new narrator message element
    currentNarratorMessageElement = document.createElement('div');
    currentNarratorMessageElement.className = 'message narrator-message';
    currentNarratorMessageElement.style.display = 'none'; // Hide until we get content
    chatHistory.appendChild(currentNarratorMessageElement);
});

// Store the raw content to avoid extra spaces
let accumulatedContent = '';

// Track the last received timestamp to prevent duplicate/out-of-order chunks
socket.on('text_output', function(data) {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    // Show and update the narrator message
    if (currentNarratorMessageElement) {
        currentNarratorMessageElement.style.display = 'block';
        
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
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    console.log('Tool output:', data);
    
    // Display tool operations directly in chat
    data.tools.forEach(tool => {
        // Only show dice rolls with their results, other tools just show a brief message
        if (tool.name === 'roll_dice') {
            const diceElement = document.createElement('div');
            diceElement.className = 'dice-roll';
            console.log(tool)
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
    accumulatedContent = '';
    // Enable user input
    if (userInput) {
        userInput.disabled = false;
        userInput.focus();
    }
});

function addNewStory(story) {
    const storyItem = document.createElement('div');
    storyItem.className = 'story-item';
    storyItem.setAttribute('data-story', story.story);
    storyItem.textContent = story.story_name;
    storyList.appendChild(storyItem);
}

// Helper functions
function addUserMessage(message, disableInput = true) {
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
    
    // Disable input while waiting for response (unless loading from history)
    if (disableInput && userInput) {
        userInput.disabled = true;
    }
}

function addAssistantMessageFromHistory(content) {
    if (!chatHistory) return;
    
    // Create narrator message element
    const narratorMessageElement = document.createElement('div');
    narratorMessageElement.className = 'message narrator-message';
    
    // Process narration tags (reuse existing logic)
    let processedContent = content;
    processedContent = processedContent.replace(/<narration>(.*?)<\/narration>/gs, function(_, narrationContent) {
        let narrationText = narrationContent;
        let paragraphs = narrationText.split(/\n\s*\n|\n{2,}/g);
        let formattedNarration = paragraphs.map(paragraph => {
            let cleanParagraph = paragraph.replace(/\s+/g, ' ').trim();
            if (cleanParagraph) {
                return '<p>' + cleanParagraph + '</p>';
            }
            return '';
        }).join('');
        return '<div class="book-narration">' + formattedNarration + '</div>';
    });
    
    // Convert markdown to HTML (reuse existing logic)
    try {
        const formattedText = marked.parse(processedContent);
        narratorMessageElement.innerHTML = formattedText;
    } catch (e) {
        console.error('Error parsing markdown:', e);
        narratorMessageElement.textContent = processedContent;
    }
    
    chatHistory.appendChild(narratorMessageElement);
}

// Export conversation history to console
function exportConversation() {
    console.log('Conversation History:');
    console.log(JSON.stringify(conversationHistory, null, 2));
}

function showTypingIndicator() {
    if (chatHistory) {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatHistory.appendChild(typingIndicator);
    }
}
function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function scrollToBottom() {
    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
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
