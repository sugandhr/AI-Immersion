/**
 * SmartCare Queue AI - Conversational Hospital Assistant
 */

document.addEventListener('DOMContentLoaded', () => {
  setupAIAssistantChat();
  setupFloatingAssistantWidget();
});

function setupAIAssistantChat() {
  const form = document.getElementById('ai-chat-form');
  const input = document.getElementById('ai-chat-input');
  const messagesContainer = document.getElementById('ai-chat-messages');

  if (!form || !input || !messagesContainer) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    appendChatMessage('user', query);
    input.value = '';

    // Typing indicator
    const typingId = appendTypingIndicator();

    try {
      const user = window.Auth.getUser();
      const res = await window.api.post('/ai/assistant', {
        query: query,
        user_id: user ? user.id : null
      });

      removeTypingIndicator(typingId);

      if (res.success && res.data) {
        appendChatMessage('assistant', res.data.response, res.data.type);
      }
    } catch (err) {
      removeTypingIndicator(typingId);
      appendChatMessage('assistant', "I apologize, but I am currently experiencing technical difficulties connecting to the hospital information system. Please check with the front desk.", 'error');
    }
  });
}

function appendChatMessage(role, text, responseType = '') {
  const messagesContainer = document.getElementById('ai-chat-messages');
  if (!messagesContainer) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message chat-${role}`;

  let extraStyle = '';
  if (responseType === 'medical_guardrail') {
    extraStyle = 'background: #FEF3C7; border: 1.5px solid #F59E0B; color: #92400E;';
  } else if (responseType === 'emergency') {
    extraStyle = 'background: #FEE2E2; border: 1.5px solid #DC2626; color: #991B1B;';
  }

  // Convert markdown bold to HTML strong and newlines to <br>
  const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');

  msgDiv.innerHTML = `
    <div class="message-bubble" style="${extraStyle}">
      ${role === 'assistant' ? '<div style="font-size:0.75rem; font-weight:700; margin-bottom:0.25rem; color:var(--primary);">🤖 SmartCare AI Guide</div>' : ''}
      <div>${formattedText}</div>
    </div>
  `;

  messagesContainer.appendChild(msgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendTypingIndicator() {
  const messagesContainer = document.getElementById('ai-chat-messages');
  if (!messagesContainer) return null;

  const typingId = `typing-${Date.now()}`;
  const typingDiv = document.createElement('div');
  typingDiv.id = typingId;
  typingDiv.className = 'chat-message chat-assistant';
  typingDiv.innerHTML = `
    <div class="message-bubble" style="padding: 0.75rem 1rem;">
      <span class="spinner" style="width:16px; height:16px; border-width:2px;"></span>
      <span style="font-size: 0.82rem; color: var(--text-muted); margin-left: 0.5rem;">SmartCare AI is typing...</span>
    </div>
  `;
  messagesContainer.appendChild(typingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return typingId;
}

function removeTypingIndicator(typingId) {
  if (!typingId) return;
  const el = document.getElementById(typingId);
  if (el) el.remove();
}

function askSuggestedQuery(queryText) {
  const input = document.getElementById('ai-chat-input');
  const form = document.getElementById('ai-chat-form');
  if (input && form) {
    input.value = queryText;
    form.dispatchEvent(new Event('submit'));
  }
}
window.askSuggestedQuery = askSuggestedQuery;

// Floating Widget for Quick Access Across Pages
function setupFloatingAssistantWidget() {
  // If not on dedicated ai-assistant.html page, inject floating trigger
  if (window.location.pathname.includes('ai-assistant')) return;

  const btn = document.createElement('a');
  btn.href = 'ai-assistant.html';
  btn.className = 'floating-ai-btn';
  btn.innerHTML = '🤖 Ask SmartCare AI';
  btn.setAttribute('aria-label', 'Open AI Hospital Assistant');
  btn.style.cssText = `
    position: fixed;
    bottom: 1.75rem;
    right: 1.75rem;
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    color: #FFFFFF;
    padding: 0.75rem 1.35rem;
    border-radius: 9999px;
    font-size: 0.9rem;
    font-weight: 600;
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    z-index: 999;
    text-decoration: none;
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  `;
  btn.onmouseover = () => { btn.style.transform = 'translateY(-3px)'; };
  btn.onmouseout = () => { btn.style.transform = 'translateY(0)'; };
  document.body.appendChild(btn);
}
