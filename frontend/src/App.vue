<template>
  <div class="page-wrapper d-flex" :class="theme">
    <div class="sidebar-wrapper">
      <Sidebar 
        :projects="projects" 
        :chats="chats"
        :activeChatId="activeChatId"
        @select-chat="selectChat"
        @project-created="handleCreateProject"
        @chat-created="handleCreateChat"
        @delete-chat="handleDeleteChat"
      />
    </div>
    <div class="chat-wrapper flex-grow-1">
      <ChatWindow 
        :chatId="activeChatId" 
        :chatName="activeChatName"
        :theme="theme" 
        @toggle-theme="toggleTheme" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import Sidebar from '@/components/Sidebar.vue';
import ChatWindow from '@/components/ChatWindow.vue';
import { getProjects, createProject, getChats, createChat, deleteChat } from '@/api';

// State
const projects = ref([]);
const chats = ref({}); // { projectId1: [chat1, chat2], projectId2: [...] }
const activeChatId = ref(null);
const theme = ref('dark');

// Computed property to get active chat name
const activeChatName = computed(() => {
    if (!activeChatId.value) return '';
    for (const projectId in chats.value) {
        const chat = chats.value[projectId]?.find(c => c.id === activeChatId.value);
        if (chat) return chat.name;
    }
    return '';
});

// Methods
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
};

const loadProjects = async () => {
    try {
        const response = await getProjects();
        projects.value = response.data;
        // Загружаем чаты для каждого проекта
        for (const p of projects.value) {
            await loadChats(p.id);
        }
    } catch (error) {
        console.error("Ошибка загрузки проектов:", error);
    }
};

const loadChats = async (projectId) => {
    try {
        const response = await getChats(projectId);
        chats.value[projectId] = response.data;
    } catch (error) {
        console.error(`Ошибка загрузки чатов для проекта ${projectId}:`, error);
    }
};

const selectChat = (chatId) => {
    activeChatId.value = chatId;
};

const handleCreateProject = async (name) => {
    try {
        await createProject(name);
        await loadProjects(); // Перезагружаем все проекты  
    } catch (error) {
        console.error("Ошибка создания проекта:", error);
    }
};

const handleCreateChat = async ({ projectId, name }) => {
    try {
        activeChatId.value = newChat.id;
        // 1. Сначала создаем чат и получаем его от сервера
        const response = await createChat(projectId, name);
        const newChat = response.data;
        
        // 2. Перезагружаем список чатов для КОНКРЕТНОГО проекта
        await loadChats(projectId); 
        
        // 3. Делаем новый чат активным
        selectChat(newChat.id); 
    } catch (error) {
        console.error("Ошибка создания чата:", error);
    }
};

const handleDeleteChat = async (chatId) => {
    try {
        // Находим projectId, чтобы обновить нужный список
        let projectIdToDeleteFrom = null;
        for (const projectId in chats.value) {
            if (chats.value[projectId]?.some(c => c.id === chatId)) {
                projectIdToDeleteFrom = projectId;
                break;
            }
        }
        
        await deleteChat(chatId);
        
        if (activeChatId.value === chatId) {
            activeChatId.value = null; // Сбрасываем активный чат
        }
        if (projectIdToDeleteFrom) {
            await loadChats(projectIdToDeleteFrom);
        }
    } catch (error) {
        console.error("Ошибка удаления чата:", error);
    }
};


onMounted(() => {
    loadProjects();
});
</script>

<style>
/* Глобальные стили приложения */
.page-wrapper {
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow: hidden;
}
.sidebar-wrapper {
  width: 300px;
  flex-shrink: 0;
}
.chat-wrapper {
  height: 100vh;
}

/* Переменные тем (из старого App.vue) */
.light {
  --bg-color: #f0f2f5;
  --window-bg: #ffffff;
  --text-color: #212529;
  --border-color: #dee2e6;
  --header-bg: #f8f9fa;
  --input-bg: #ffffff;
  --code-bg: #f8f9fa;
}
.dark {
  --bg-color: #121212;
  --window-bg: #212529;
  --text-color: #f8f9fa;
  --border-color: #495057;
  --header-bg: #343a40;
  --input-bg: #495057;
  --code-bg: #282c34;
}

/* Стили для скроллбара */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: var(--bg-color);
}
::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #555;
}

</style>

