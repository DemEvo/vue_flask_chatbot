<template>
  <div class="page-wrapper d-flex inter inter-300" :class="theme">
    <div class="sidebar-wrapper">
      <Sidebar 
        :projects="projects" 
        :chats="chats"
        :activeChatId="activeChatId"
        @select-chat="selectChat"
        @project-created="handleCreateProject"
        @rename-project="handleRenameProject"
        @delete-project="handleDeleteProject"
        @chat-created="handleCreateChat"
        @rename-chat="handleRenameChat"
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
import { 
    getProjects, createProject, renameProject, deleteProject,
    getChats, createChat, renameChat, deleteChat 
} from '@/api';

// State
const projects = ref([]);
const chats = ref({});
const activeChatId = ref(null);
const theme = ref('dark');

// Computed property
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

// --- Project CRUD ---
const handleCreateProject = async (name) => {
    try {
        await createProject(name);
        await loadProjects();
    } catch (error) {
        console.error("Ошибка создания проекта:", error);
    }
};

const handleRenameProject = async ({ id, name }) => {
    try {
        await renameProject(id, name);
        const project = projects.value.find(p => p.id === id);
        if (project) project.name = name;
    } catch (error) {
        console.error("Ошибка переименования проекта:", error);
    }
};

const handleDeleteProject = async (projectId) => {
    try {
        await deleteProject(projectId);
        await loadProjects();
        if (!Object.values(chats.value).flat().some(c => c.id === activeChatId.value)) {
            activeChatId.value = null;
        }
    } catch (error) {
        console.error("Ошибка удаления проекта:", error);
    }
};


// --- Chat CRUD ---
const handleCreateChat = async ({ projectId, name }) => {
    try {
        const response = await createChat(projectId, name);
        await loadChats(projectId);
        selectChat(response.data.id);
    } catch (error) {
        console.error("Ошибка создания чата:", error);
    }
};

const handleRenameChat = async ({ id, name }) => {
    try {
        await renameChat(id, name);
        for (const projectId in chats.value) {
            const chat = chats.value[projectId].find(c => c.id === id);
            if (chat) {
                chat.name = name;
                break;
            }
        }
    } catch (error) {
        console.error("Ошибка переименования чата:", error);
    }
};

const handleDeleteChat = async (chatId) => {
    try {
        let projectIdToDeleteFrom = null;
        for (const projectId in chats.value) {
            if (chats.value[projectId]?.some(c => c.id === chatId)) {
                projectIdToDeleteFrom = projectId;
                break;
            }
        }
        
        await deleteChat(chatId);
        
        if (activeChatId.value === chatId) {
            activeChatId.value = null;
        }
        if (projectIdToDeleteFrom) {
            await loadChats(projectIdToDeleteFrom);
        }
    } catch (error) {
        console.error("Ошибка удаления чата:", error);
    }
};

onMounted(loadProjects);
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');
.inter {
  font-family: "Inter", sans-serif;
  font-optical-sizing: auto;
  font-style: normal;
}
.inter-300 {
  font-weight: 300;
}
/* ... styles remain unchanged ... */
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
/* ... theme variables ... */
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
/* ... scrollbar styles ... */
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
