<template>
    <div class="d-flex flex-column h-100">
        <div v-if="!chatId" class="d-flex flex-grow-1 justify-content-center align-items-center">
            <div class="text-center text-muted">
                <h3>Выберите чат</h3>
                <p>...или создайте новый в панели слева.</p>
            </div>
        </div>
        <template v-else>
            <div class="chat-header p-3 d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-0">{{ chatName }}</h5>
                </div>
                <button class="btn btn-outline-light" @click="$emit('toggle-theme')">
                    {{ theme === 'dark' ? '☀️' : '🌙' }}
                </button>
            </div>

            <div class="chat-messages p-3 flex-grow-1" ref="messagesContainer" @scroll="handleScroll">
                 <div v-if="isLoadingMore" class="text-center text-muted my-2">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                </div>
                <div v-for="msg in messages" :key="msg.id" 
                    :class="['message', msg.role === 'user' ? 'user' : 'assistant', 'mb-2']">
                    <div :class="['p-2 px-3 rounded-3 markdown-content', msg.role === 'user' ? 'alert alert-primary' : 'alert-secondary']" 
                        v-html="renderMarkdown(msg.content)">
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
                    <textarea
                        ref="textareaRef"
                        class="form-control"
                        rows="1"
                        v-model="newMessage"
                        @keydown.enter.exact.prevent="handleSendMessage"
                        @input="autoResizeTextarea"
                        :disabled="isLoading"
                        placeholder="Введите ваше сообщение... (Shift+Enter для новой строки)"
                    ></textarea>
                    <button class="btn btn-primary" @click="handleSendMessage" :disabled="isLoading">Отправить</button>
                </div>
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { getMessages, sendMessage } from '@/api';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';

// Markdown and Highlight.js setup
marked.setOptions({
  highlight: (code, lang) => {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  gfm: true,
  breaks: true,
});

const renderMarkdown = (text) => {
    if (!text) return '';
    const rawHtml = marked.parse(text);
    return DOMPurify.sanitize(rawHtml);
};

// Component props and emits
const props = defineProps({
    chatId: Number,
    chatName: String,
    theme: String,
});
const emit = defineEmits(['toggle-theme', 'message-sent']);

// Component state
const messages = ref([]);
const newMessage = ref('');
const isLoading = ref(false);
const isLoadingMore = ref(false);
const currentPage = ref(1);
const hasMoreMessages = ref(true);
const messagesContainer = ref(null);

const autoResizeTextarea = () => {
    const el = textareaRef.value;
    if (el) {
        el.style.height = 'auto';
        const maxHeight = 200; // Максимальная высота в пикселях
        const newHeight = el.scrollHeight;
        if (newHeight > maxHeight) {
            el.style.height = `${maxHeight}px`;
            el.style.overflowY = 'auto';
        } else {
            el.style.height = `${newHeight}px`;
            el.style.overflowY = 'hidden';
        }
    }
};

// Load initial messages for a chat
const loadMessages = async (id, loadMore = false) => {
    if (!id || (loadMore && !hasMoreMessages.value)) return;

    if (loadMore) {
        isLoadingMore.value = true;
    } else {
        isLoading.value = true;
        messages.value = [];
        currentPage.value = 1;
        hasMoreMessages.value = true;
    }

    try {
        const response = await getMessages(id, currentPage.value);
        const newMessages = response.data.messages.reverse(); // API returns newest first
        messages.value = loadMore ? [...newMessages, ...messages.value] : newMessages;
        hasMoreMessages.value = response.data.has_next;
        currentPage.value++;
    } catch (error) {
        console.error("Ошибка загрузки сообщений:", error);
    } finally {
        isLoading.value = false;
        isLoadingMore.value = false;
        if (!loadMore) {
            scrollToBottom();
        }
    }
};

// Watch for chat changes
watch(() => props.chatId, (newId) => {
    loadMessages(newId);
});

// Send new message
const handleSendMessage = async () => {
    if (newMessage.value.trim() === '' || isLoading.value) return;

    const content = newMessage.value;
    newMessage.value = '';
    isLoading.value = true;
    messages.value.push({ id: Date.now(), role: 'user', content });
    scrollToBottom();

    try {
        const response = await sendMessage(props.chatId, content);
        messages.value.push(response.data);
    } catch (error) {
        console.error("Ошибка отправки сообщения:", error);
        messages.value.push({ id: Date.now(), role: 'assistant', content: 'Произошла ошибка.' });
    } finally {
        isLoading.value = false;
        scrollToBottom();
        nextTick(() => {
            if (textareaRef.value) {
                textareaRef.value.style.height = 'auto';
                textareaRef.value.style.overflowY = 'hidden';
                textareaRef.value.focus();
            }
        });
    }
};

// Infinite scroll handler
const handleScroll = () => {
    if (messagesContainer.value?.scrollTop === 0 && !isLoadingMore.value && hasMoreMessages.value) {
        loadMessages(props.chatId, true);
    }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
    });
};

</script>

<style>

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
/*
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
}*/


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

.chat-input textarea.form-control  {
    min-height: 80px;
    resize: vertical;
    overflow-y: auto;
}

.chat-input textarea.form-control::after  {
  content: "⋯";
  position: absolute;
  bottom: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
  font-size: 20px;
  color: #aaa;
  pointer-events: none; /* клик проходит мимо */
  z-index: 1;
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


.markdown-content pre {
  padding: 10px; 
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
</style>
