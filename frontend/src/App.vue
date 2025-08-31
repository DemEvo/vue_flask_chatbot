<template>
  <div class="page-wrapper" :class="theme">
    <div class="container h-100 py-4">
      
      <div class="row h-100 justify-content-center align-items-center">
        
        <div class="col-12 col-md-10 col-lg-10 col-xl-8 h-100">
          
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
                <div :class="['p-2 px-3 rounded-3', msg.sender === 'user' ? 'alert alert-primary' : 'alert-secondary']">
                  {{ msg.text }}
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
// ... (раздел script остается БЕЗ ИЗМЕНЕНИЙ)
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';

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
  messages.value.push({ sender: 'assistant', text: 'Здравствуйте! Я чат-бот с гибридной памятью. Чем могу помочь?' });
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
/* Стили теперь идеально дополняют сетку Bootstrap */

/* Светлая тема */
.light {
  --bg-color: #f0f2f5;
  --window-bg: #ffffff;
  --text-color: #212529;
  --border-color: #dee2e6;
  --header-bg: #f8f9fa;
  --input-bg: #ffffff;
}

/* Тёмная тема */
.dark {
  --bg-color: #121212;
  --window-bg: #212529;
  --text-color: #f8f9fa;
  --border-color: #495057;
  --header-bg: #343a40;
  --input-bg: #495057;
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
  max-height: 100%; /* Окно чата занимает всю высоту колонки */
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
</style>