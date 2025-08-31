<template>
  <div class="page-wrapper" :class="theme">
    <div class="container h-100 py-4">
      <div class="row h-100 justify-content-center align-items-center">
        <div class="col-12 col-md-10 col-lg-10 col-xl-10 h-100">
          <div class="d-flex flex-column h-100 shadow rounded-3 chat-window">
            
            <div class="chat-header p-3 d-flex justify-content-between align-items-center">
              <div>
                <h5 class="mb-0">Гибридный Чат-Бот</h5>
                <small class="opacity-75">Session ID: {{ sessionId }}</small>
              </div>
              <button class="btn btn-outline-light" @click="toggleTheme">
                {{ theme === 'dark' ? '☀️' : '🌙' }}
              </button>
            </div>

            <div class="chat-messages p-3 flex-grow-1" ref="messagesContainer">
              <div v-for="(msg, index) in messages" :key="index" 
                  :class="['message', msg.sender === 'user' ? 'user' : 'assistant', 'mb-2']">
                <div 
                  :class="['p-2 px-3 rounded-3 markdown-content', msg.sender === 'user' ? 'alert alert-primary' : 'alert-secondary']" 
                  v-html="renderMarkdown(msg.text)">
                </div>
              </div>
              <div v-if="isLoading" class="message assistant mb-2">
                <div class="p-2 px-3 rounded-3 alert alert-secondary">
                  ...
                </div>
              </div>
            </div>

            <div class="chat-input p-3">
              <div class="input-group">
                <input
                  type="text"
                  class="form-control"
                  v-model="newMessage"
                  @keyup.enter="sendMessage"
                  placeholder="Введите ваше сообщение..."
                  :disabled="isLoading"
                />
                <button class="btn btn-primary" @click="sendMessage" :disabled="isLoading">Отправить</button>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

// 👇 ИЗМЕНЕНИЕ: Импортируем highlight.js и его стили 👇
import hljs from 'highlight.js';
// Вы можете выбрать любую тему здесь: https://highlightjs.org/static/demo/
import 'highlight.js/styles/atom-one-dark.css';

// 👇 ИЗМЕНЕНИЕ: Настраиваем marked для работы с highlight.js 👇
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  gfm: true,
  breaks: true,
});


function preprocessSpecialTags(text) {
  if (!text) return '';
  const imageRegex = /\[Image of (.*?)\]/g;
  return text.replace(imageRegex, (match, query) => {
    const encodedQuery = encodeURIComponent(query.trim());
    const imageUrl = `https://placehold.co/600x400/EEE/31343C?text=${encodedQuery}`;
    return `<img src="${imageUrl}" alt="${query}" class="img-fluid rounded my-2" />`;
  });
}

const renderMarkdown = (text) => {
  if (!text) return '';
  const processedText = preprocessSpecialTags(text);
  // Теперь marked автоматически будет использовать highlight.js
  const rawHtml = marked.parse(processedText);
  return DOMPurify.sanitize(rawHtml);
};

// ... остальной <script setup> без изменений
const messages = ref([]);
const newMessage = ref('');
const sessionId = ref('');
const isLoading = ref(false);
const messagesContainer = ref(null);
const theme = ref('dark');

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
};

onMounted(() => {
  sessionId.value = 'session_' + Math.random().toString(36).substr(2, 9);
  messages.value.push({ sender: 'assistant', text: 'Здравствуйте! Теперь я умею форматировать текст, показывать картинки и подсвечивать синтаксис кода. Проверьте!' });
});

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

const sendMessage = async () => {
  if (newMessage.value.trim() === '' || isLoading.value) return;
  const userMessage = { sender: 'user', text: newMessage.value };
  messages.value.push(userMessage);
  const messageToSend = newMessage.value;
  newMessage.value = '';
  isLoading.value = true;
  scrollToBottom();
  try {
    const response = await axios.post('/api/chat', {
      session_id: sessionId.value,
      message: messageToSend
    });
    messages.value.push({ sender: 'assistant', text: response.data.reply });
  } catch (error) {
    console.error("Ошибка при отправке сообщения:", error);
    messages.value.push({ sender: 'assistant', text: 'Произошла ошибка. Попробуйте снова.' });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};
</script>

<style>
/* ... (основные стили остаются без изменений) ... */

/* Светлая тема */
.light {
  --bg-color: #f0f2f5;
  --window-bg: #ffffff;
  --text-color: #212529;
  --border-color: #dee2e6;
  --header-bg: #f8f9fa;
  --input-bg: #ffffff;
  --code-bg: #f8f9fa; /* Фон для кода в светлой теме */
}

/* Тёмная тема */
.dark {
  --bg-color: #121212;
  --window-bg: #212529;
  --text-color: #f8f9fa;
  --border-color: #495057;
  --header-bg: #343a40;
  --input-bg: #495057;
  --code-bg: #282c34; /* Фон для кода в тёмной теме (из темы atom-one-dark) */
}

html, body {
  height: 100vh;
}

.page-wrapper {
  height: 100vh;
  background-color: var(--bg-color);
  transition: background-color 0.3s;
}

.chat-window {
  max-height: 100%;
  background-color: var(--window-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.chat-header {
  background-color: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
}

.chat-messages {
  overflow-y: auto;
}

.message {
  display: flex;
  max-width: 85%;
}
.message.user {
  justify-content: flex-end;
  margin-left: auto;
}
.message.assistant {
  justify-content: flex-start;
  margin-right: auto;
}
.alert {
  border: none !important;
  margin-bottom: 0 !important;
}
.alert-secondary {
   background-color: var(--header-bg);
   color: var(--text-color);
}

.chat-input {
  background-color: var(--header-bg);
  border-top: 1px solid var(--border-color);
}
.chat-input .form-control {
  background-color: var(--input-bg);
  color: var(--text-color);
  border-color: var(--border-color);
}
.chat-input .form-control:focus {
  background-color: var(--input-bg);
  color: var(--text-color);
  box-shadow: none;
  border-color: #0d6efd;
}

.markdown-content p:last-child {
  margin-bottom: 0;
}

.markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4 {
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
}

.markdown-content ul, .markdown-content ol {
  padding-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
}

/* 👇 ИЗМЕНЕНИЕ: Стили для блоков кода 👇 */
.markdown-content pre {
  padding: 10px; /* Убираем padding, так как он будет у внутреннего <code> */
  margin: 0.5rem 0;
  border-radius: 6px;
  background-color: var(--code-bg); /* Используем фон из темы */
}
.markdown-content pre code.hljs {
  padding: 1em; /* Добавляем внутренние отступы */
  border-radius: 6px;
  background-color: transparent !important; /* Делаем фон от hljs прозрачным, чтобы видеть наш */
}

/* Адаптируем тему atom-one-dark для светлой темы */
.light .hljs {
  color: #383a42;
}
.light .hljs-comment,
.light .hljs-quote {
  color: #a0a1a7;
}
.light .hljs-variable,
.light .hljs-template-variable,
.light .hljs-tag,
.light .hljs-name,
.light .hljs-selector-id,
.light .hljs-selector-class,
.light .hljs-regexp,
.light .hljs-deletion {
  color: #e45649;
}
/* и так далее для других токенов, если нужно */
</style>

