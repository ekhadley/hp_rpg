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
let currentThinkingElement = null;
let currentStory = null;
let lastNarratorMessageElement = null;

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
        //if (true) {
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

socket.on('conversation_history', function(history) {
    console.log('Loading conversation history:', history);
    
    // Clear existing conversation history in UI
    conversationHistory = [];
    
    // Render each message in chronological order
    history.forEach(function(message) {
        if (message.role === 'user') {
            if (typeof message.content === "string") {
                if (message.content != "<|begin_conversation|>") {
                    addUserMessage(message.content, false);
                }
            } else {
                message.content.forEach(element => {
                    if (element.type == "text") {
                        addUserMessage(element.content, false);
                    } else if (element.type == "tool_result") {
                        tool_call = {
                            tools: [{
                                name: tool_name,
                                inputs: tool_arguments,
                                result: element.content
                            }]
                        }
                        addToolUseToHistory(tool_call);
                    }
                });
            }
        } else if (message.role === 'assistant') {
            let hasThinking = false;
            let thinkingContent = '';
            
            // First pass: check for thinking content
            message.content.forEach(element => {
                if (element.type == "thinking") {
                    hasThinking = true;
                    thinkingContent = element.thinking;
                }
            });
            
            // Create thinking dropdown if thinking content exists
            if (hasThinking) {
                addThinkingFromHistory(thinkingContent);
            }
            
            // Second pass: process other content types
            message.content.forEach(element => {
                if (element.type == "text") {
                    addAssistantMessageFromHistory(element.text);
                } else if (element.type == "tool_use") {
                    tool_name = element.name,
                    tool_arguments = element.input
                }
            });
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

socket.on('think_start', function() {
    console.log('Model started thinking');
    
    // Create thinking dropdown container
    currentThinkingElement = document.createElement('div');
    currentThinkingElement.className = 'thinking-container';

    // Create header
    const thinkingHeader = document.createElement('div');
    thinkingHeader.className = 'thinking-header';
    
    const thinkingLabel = document.createElement('div');
    thinkingLabel.className = 'thinking-label';
    thinkingLabel.innerHTML = '<i class="fas fa-brain"></i>';
    
    const thinkingToggle = document.createElement('div');
    thinkingToggle.className = 'thinking-toggle';
    thinkingToggle.innerHTML = '▼';
    
    thinkingHeader.appendChild(thinkingLabel);
    thinkingHeader.appendChild(thinkingToggle);
    
    // Create content area
    const thinkingContent = document.createElement('div');
    thinkingContent.className = 'thinking-content';
    
    // Add click handler for toggle
    thinkingHeader.addEventListener('click', function() {
        const isExpanded = thinkingContent.classList.toggle('expanded');
        thinkingToggle.classList.toggle('expanded', isExpanded);
    });
    
    currentThinkingElement.appendChild(thinkingHeader);
    currentThinkingElement.appendChild(thinkingContent);
    chatHistory.appendChild(currentThinkingElement);
});

socket.on('think_output', function(data) {
    if (currentThinkingElement) {
        const thinkingContent = currentThinkingElement.querySelector('.thinking-content');
        thinkingContent.textContent += data.text;
        scrollToBottom();
    }
});

socket.on('text_start', function() {
    console.log('Narrator switched to outputting text');
    
    // If we're not retrying (currentNarratorMessageElement is null), create a new message element
    if (!currentNarratorMessageElement) {
        currentNarratorMessageElement = document.createElement('div');
        currentNarratorMessageElement.className = 'message narrator-message';
        currentNarratorMessageElement.style.display = 'none'; // Hide until we get content
        chatHistory.appendChild(currentNarratorMessageElement);
    }
    
    // Remove any existing retry buttons from previous messages (only show on last message)
    const existingRetryButtons = chatHistory.querySelectorAll('.retry-button');
    existingRetryButtons.forEach(button => {
        const messageActions = button.closest('.message-actions');
        if (messageActions) {
            messageActions.remove();
        }
    });
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

socket.on('tool_submit', addToolUseToHistory);
function addToolUseToHistory(data) {
//socket.on('tool_submit', function(data) {
    accumulatedContent = '';
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    console.log('Tool submitted:', data);
    
    // Display tool operations directly in chat
    data.tools.forEach(tool => {
        const toolElement = document.createElement('div');
        if (tool.name === 'roll_dice') {
            toolElement.className = 'dice-roll';
            toolElement.innerHTML = `🎲 Rolled ${tool.inputs.dice}: <strong>${tool.result}</strong>`;
            chatHistory.appendChild(toolElement);
        } else {
            toolElement.className = 'tool-message';
            toolElement.innerHTML = `Used ${tool.name}...`;
        }
        chatHistory.appendChild(toolElement);
        conversationHistory.push({
            role: 'tool',
            name: tool.name,
            inputs: tool.inputs,
            result: tool.result,
            timestamp: new Date().toISOString()
        });
    });
}

socket.on('turn_end', function() {
    // Add narrator's complete response to conversation history
    if (currentNarratorMessageElement) {
        conversationHistory.push({
            role: 'assistant',
            content: accumulatedContent,
            timestamp: new Date().toISOString()
        });
        
        // Store reference to last narrator message for retry functionality
        lastNarratorMessageElement = currentNarratorMessageElement;
        
        // Add retry button to the last narrator message
        addRetryButton(lastNarratorMessageElement);
    }
    
    currentNarratorMessageElement = null;
    currentThinkingElement = null;
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

function addThinkingFromHistory(thinkingContent) {
    if (!chatHistory) return;
    
    // Create thinking dropdown container (reuse existing logic)
    const thinkingElement = document.createElement('div');
    thinkingElement.className = 'thinking-container';

    // Create header
    const thinkingHeader = document.createElement('div');
    thinkingHeader.className = 'thinking-header';
    
    const thinkingLabel = document.createElement('div');
    thinkingLabel.className = 'thinking-label';
    thinkingLabel.innerHTML = '<i class="fas fa-brain"></i>';
    
    const thinkingToggle = document.createElement('div');
    thinkingToggle.className = 'thinking-toggle';
    thinkingToggle.innerHTML = '▼';
    
    thinkingHeader.appendChild(thinkingLabel);
    thinkingHeader.appendChild(thinkingToggle);
    
    // Create content area
    const thinkingContentDiv = document.createElement('div');
    thinkingContentDiv.className = 'thinking-content';
    thinkingContentDiv.textContent = thinkingContent;
    
    // Add click handler for toggle
    thinkingHeader.addEventListener('click', function() {
        const isExpanded = thinkingContentDiv.classList.toggle('expanded');
        thinkingToggle.classList.toggle('expanded', isExpanded);
    });
    
    thinkingElement.appendChild(thinkingHeader);
    thinkingElement.appendChild(thinkingContentDiv);
    chatHistory.appendChild(thinkingElement);
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

function addRetryButton(messageElement) {
    // Don't add retry button if one already exists
    if (messageElement.querySelector('.retry-button')) {
        return;
    }
    
    // Create retry button container
    const retryContainer = document.createElement('div');
    retryContainer.className = 'message-actions';
    
    // Create retry button
    const retryButton = document.createElement('button');
    retryButton.className = 'retry-button';
    retryButton.innerHTML = '<i class="fas fa-redo"></i>';
    retryButton.title = 'Retry this response';
    
    // Add click handler
    retryButton.addEventListener('click', function() {
        handleRetryResponse(messageElement, retryButton);
    });
    
    retryContainer.appendChild(retryButton);
    messageElement.appendChild(retryContainer);
}

function handleRetryResponse(messageElement, retryButton) {
    // Disable retry button during retry
    retryButton.disabled = true;
    retryButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Disable user input
    if (userInput) {
        userInput.disabled = true;
    }
    
    // Remove the last assistant message from conversation history (will be replaced)
    if (conversationHistory.length > 0 && conversationHistory[conversationHistory.length - 1].role === 'assistant') {
        conversationHistory.pop();
    }
    
    // Remove current message content but keep the container
    const messageActions = messageElement.querySelector('.message-actions');
    messageElement.innerHTML = '';
    if (messageActions) {
        messageElement.appendChild(messageActions);
    }
    
    // Set as current narrator message element for new content
    currentNarratorMessageElement = messageElement;
    accumulatedContent = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Request retry from server
    socket.emit('retry_last_response');
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
