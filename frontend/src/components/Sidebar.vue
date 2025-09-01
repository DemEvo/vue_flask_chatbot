<template>
    <div class="d-flex flex-column h-100 p-3 sidebar-container">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4 class="mb-0">Проекты</h4>
            <button class="btn btn-sm btn-primary" @click="handleCreateProject">
                <i class="bi bi-plus-lg"></i>
            </button>
        </div>

        <div class="flex-grow-1 overflow-auto">
            <div class="accordion" id="projectsAccordion">
                <div v-for="project in projects" :key="project.id" class="accordion-item">
                    <h2 class="accordion-header" :id="'heading' + project.id">
                        <button class="accordion-button collapsed d-flex justify-content-between" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse' + project.id">
                            <span class="text-truncate me-2">{{ project.name }}</span>
                            <!-- Project Actions -->
                            <div class="project-actions">
                                <i class="bi bi-pencil-square action-icon" @click.stop="handleRenameProject(project.id, project.name)"></i>
                                <i class="bi bi-trash action-icon text-danger" @click.stop="handleDeleteProject(project.id)"></i>
                            </div>
                        </button>
                    </h2>
                    <div :id="'collapse' + project.id" class="accordion-collapse collapse" data-bs-parent="#projectsAccordion">
                        <div class="accordion-body">
                            <ul class="list-group list-group-flush">
                                <li v-for="chat in project.chats" :key="chat.id"
                                    class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                                    :class="{ active: chat.id === activeChatId }"
                                    @click="$emit('select-chat', chat.id)">
                                    <span class="text-truncate">{{ chat.name }}</span>
                                    <div class="chat-actions">
                                        <i class="bi bi-pencil-square action-icon" @click.stop="handleRenameChat(chat.id, chat.name)"></i>
                                        <i class="bi bi-trash action-icon text-danger" @click.stop="handleDeleteChat(chat.id)"></i>
                                    </div>
                                </li>
                            </ul>
                            <button class="btn btn-sm btn-outline-secondary w-100 mt-2" @click="handleCreateChat(project.id)">
                                + Новый чат
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { createProject, createChat } from '@/api.js';

const props = defineProps({
    projects: Array,
    chats: Object,
    activeChatId: Number,
});

const emit = defineEmits([
    'select-chat', 
    'project-created', 'rename-project', 'delete-project',
    'chat-created', 'rename-chat', 'delete-chat'
]);

// --- CREATE ---
const handleCreateProject = async () => {
    const name = prompt("Введите имя нового проекта:", "Новый проект");
    if (name && name.trim()) {
        emit('project-created', name.trim());
    }
};

const handleCreateChat = async (projectId) => {
    const name = prompt("Введите имя нового чата:", "Новый чат");
    if (name && name.trim()) {
        emit('chat-created', { projectId, name: name.trim() });
    }
};

// --- RENAME ---
const handleRenameProject = (projectId, currentName) => {
    const newName = prompt("Введите новое имя проекта:", currentName);
    if (newName && newName.trim() && newName.trim() !== currentName) {
        emit('rename-project', { id: projectId, name: newName.trim() });
    }
};

const handleRenameChat = (chatId, currentName) => {
    const newName = prompt("Введите новое имя чата:", currentName);
    if (newName && newName.trim() && newName.trim() !== currentName) {
        emit('rename-chat', { id: chatId, name: newName.trim() });
    }
};

// --- DELETE ---
const handleDeleteProject = (projectId) => {
    if (confirm("Вы уверены, что хотите удалить этот проект и все его чаты?")) {
        emit('delete-project', projectId);
    }
};

const handleDeleteChat = (chatId) => {
    if (confirm("Вы уверены, что хотите удалить этот чат?")) {
        emit('delete-chat', chatId);
    }
};
</script>

<style scoped>
.sidebar-container {
    background-color: var(--header-bg);
    border-right: 1px solid var(--border-color);
}
.accordion-button {
    background-color: var(--window-bg);
    color: var(--text-color);
}
.accordion-button:not(.collapsed) {
    background-color: #0d6efd;
    color: white;
}
.accordion-body {
    padding: 0;
}
.list-group-item {
    background-color: var(--window-bg);
    color: var(--text-color);
    cursor: pointer;
}
.list-group-item.active {
    background-color: #0d6efd;
    border-color: #0d6efd;
}
.action-icon {
    cursor: pointer;
    margin-left: 8px;
    opacity: 0.6;
    transition: opacity 0.2s;
}
.action-icon:hover {
    opacity: 1;
}
/* Hide actions by default */
.project-actions, .chat-actions {
    visibility: hidden;
}
/* Show on hover */
.accordion-button:hover .project-actions,
.list-group-item:hover .chat-actions {
    visibility: visible;
}
</style>
