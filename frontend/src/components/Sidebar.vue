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
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse' + project.id">
                            {{ project.name }}
                        </button>
                    </h2>
                    <div :id="'collapse' + project.id" class="accordion-collapse collapse" data-bs-parent="#projectsAccordion">
                        <div class="accordion-body">
                            <ul class="list-group list-group-flush">
                                <li v-for="chat in chats[project.id]" :key="chat.id"
                                    class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                                    :class="{ active: chat.id === activeChatId }"
                                    @click="$emit('select-chat', chat.id)">
                                    <span class="text-truncate">{{ chat.name }}</span>
                                    <button class="btn btn-sm btn-outline-danger" @click.stop="handleDeleteChat(chat.id)">
                                        <i class="bi bi-trash"></i>
                                    </button>
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
import { onMounted, watch } from 'vue';
// Bootstrap JS нужен для работы аккордеона
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { createProject, createChat } from '@/api.js';

const props = defineProps({
    projects: Array,
    chats: Object,
    activeChatId: Number,
});

const emit = defineEmits(['select-chat', 'project-created', 'chat-created','rename-project', 'delete-project', 'rename-chat', 'delete-chat']);


const handleCreateProject = async () => {
    const name = prompt("Введите имя нового проекта:", "Новый проект");
    if (name && name.trim()) {
        try {
            await createProject(name.trim());
            // <--- Отправляем событие родителю ---
            emit('project-created');
        } catch (error) {
            console.error("Ошибка при создании проекта:", error);
            alert("Не удалось создать проект.");
        }
    }
};

const handleCreateChat = async (projectId) => {
    const name = prompt("Введите имя нового чата:", "Новый чат");
    if (name && name.trim()) {
        try {
            const response = await createChat(projectId, name.trim());
            // <--- Отправляем событие с данными нового чата ---
            emit('chat-created', response.data);
        } catch (error) {
            console.error("Ошибка при создании чата:", error);
            alert("Не удалось создать чат.");
        }
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
</style>
