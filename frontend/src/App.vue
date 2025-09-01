<template>
  <div class="page-wrapper d-flex inter-300" :class="theme">
    <div class="sidebar-wrapper">
      <Sidebar 
        :projects="projects"
        :active-chat-id="activeChatId"
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
        :chat="activeChat" 
        :theme="theme" 
        @toggle-theme="toggleTheme"
        @chat-updated="loadProjects"
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
    createChat, renameChat, deleteChat 
} from '@/api';

// State
const projects = ref([]);
const activeChatId = ref(null);
const theme = ref('dark');

// Computed property
const activeChat = computed(() => {
    if (!activeChatId.value) return null;
    for (const project of projects.value) {
        const chat = project.chats?.find(c => c.id === activeChatId.value);
        if (chat) return chat;
    }
    return null;
});

// Methods
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
};

const loadProjects = async () => {
    try {
        const response = await getProjects();
        projects.value = response.data;
    } catch (error) {
        console.error("Ошибка загрузки проектов:", error);
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
    } catch (error) { console.error("Ошибка создания проекта:", error); }
};

const handleRenameProject = async ({ id, name }) => {
    try {
        await renameProject(id, name);
        const project = projects.value.find(p => p.id === id);
        if (project) project.name = name;
    } catch (error) { console.error("Ошибка переименования проекта:", error); }
};

const handleDeleteProject = async (projectId) => {
    try {
        await deleteProject(projectId);
        if (activeChat.value?.project_id === projectId) {
            activeChatId.value = null;
        }
        await loadProjects();
    } catch (error) { console.error("Ошибка удаления проекта:", error); }
};

// --- Chat CRUD ---
const handleCreateChat = async ({ projectId, name }) => {
    try {
        const response = await createChat(projectId, name);
        await loadProjects(); // Reload all to get updated chat list
        selectChat(response.data.id);
    } catch (error) { console.error("Ошибка создания чата:", error); }
};

const handleRenameChat = async ({ id, name }) => {
    try {
        await renameChat(id, name);
        const project = projects.value.find(p => p.id === activeChat.value.project_id);
        if (project) {
            const chat = project.chats.find(c => c.id === id);
            if (chat) chat.name = name;
        }
    } catch (error) { console.error("Ошибка переименования чата:", error); }
};

const handleDeleteChat = async (chatId) => {
    try {
        await deleteChat(chatId);
        if (activeChatId.value === chatId) {
            activeChatId.value = null;
        }
        await loadProjects(); // Reload all to get updated chat list
    } catch (error) { console.error("Ошибка удаления чата:", error); }
};

onMounted(loadProjects);
</script>

<style lang="scss">

.inter {
  font-family: "Inter", sans-serif;
  font-optical-sizing: auto;
  font-style: normal;
  
  &-100 { font-weight: 100; }
  &-200 { font-weight: 200; }
  &-300 { font-weight: 300; }
  &-400 { font-weight: 400; }
  &-500 { font-weight: 500; }
  &-600 { font-weight: 600; }
  &-700 { font-weight: 700; }
  &-800 { font-weight: 800; }
  &-900 { font-weight: 900; }
  
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
