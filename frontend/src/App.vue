<template>
  <div id="chat-container">
    <div class="chat-header">
      <h2>Гибридный Чат-Бот</h2>
      <p>Память: Short-Term + Long-Term (RAG)</p>
      <small>Session ID: {{ sessionId }}</small>
    </div>
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.sender]">
        {{ msg.text }}
      </div>
       <div v-if="isLoading" class="message assistant">
        ...
      </div>
    </div>
    <div class="chat-input">
      <input
        v-model="newMessage"
        @keyup.enter="sendMessage"
        placeholder="Введите ваше сообщение..."
        :disabled="isLoading"
      />
      <button @click="sendMessage" :disabled="isLoading">Отправить</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';

const messages = ref([]);
const newMessage = ref('');
const sessionId = ref('');
const isLoading = ref(false);
const messagesContainer = ref(null);

// Генерируем уникальный ID для сессии при загрузке компонента
onMounted(() => {
  sessionId.value = 'session_' + Math.random().toString(36).substr(2, 9);
  messages.value.push({ sender: 'assistant', text: 'Здравствуйте! Чем могу помочь?' });
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
    const response = await axios.post('http://127.0.0.1:5000/chat', {
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
/* Стили для чата, можете их улучшить */
body {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  background-color: #f0f2f5;
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

#chat-container {
  width: 500px;
  height: 80vh;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  text-align: center;
  background-color: #42b983;
  color: white;
  border-radius: 8px 8px 0 0;
}
.chat-header h2, .chat-header p { margin: 0; }
.chat-header small { opacity: 0.8; }

.chat-messages {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 75%;
  word-wrap: break-word;
}

.message.user {
  background-color: #0084ff;
  color: white;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.message.assistant {
  background-color: #e5e5ea;
  color: black;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.chat-input {
  display: flex;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.chat-input input {
  flex-grow: 1;
  border: 1px solid #ccc;
  padding: 10px;
  border-radius: 20px;
  margin-right: 10px;
}

.chat-input button {
  padding: 10px 20px;
  border: none;
  background-color: #42b983;
  color: white;
  border-radius: 20px;
  cursor: pointer;
}
.chat-input button:disabled {
  background-color: #a5d6b8;
}
</style>
