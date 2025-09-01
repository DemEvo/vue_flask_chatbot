<template>
    <div class="modal fade" :id="`promptManagerModal-${props.uniqueId}`" tabindex="-1" aria-hidden="true" ref="modalEl">
        <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Управление ролями (Промптами)</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <button class="btn btn-sm btn-primary" @click="startCreatePrompt">
                            <i class="bi bi-plus-lg"></i> Создать новую роль
                        </button>
                    </div>
                    <div v-if="editingPrompt" class="prompt-editor mb-4">
                        <input type="text" class="form-control mb-2" placeholder="Название роли" v-model="editingPrompt.name">
                        <textarea class="form-control" rows="5" placeholder="Содержание роли..." v-model="editingPrompt.content"></textarea>
                        <div class="mt-2">
                            <button class="btn btn-success btn-sm me-2" @click="savePrompt">Сохранить</button>
                            <button class="btn btn-secondary btn-sm" @click="cancelEdit">Отмена</button>
                        </div>
                    </div>
                    <ul class="list-group">
                        <li v-for="prompt in prompts" :key="prompt.id" class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>{{ prompt.name }}</strong>
                                <p class="mb-0 text-muted small text-truncate">{{ prompt.content }}</p>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-secondary" @click="selectPrompt(prompt.id)" :class="{'active': prompt.id === activePromptId}">
                                    <i class="bi bi-check-circle"></i> Выбрать
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" @click="startEditPrompt(prompt)">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" @click="handleDeletePrompt(prompt.id)">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { getPrompts, createPrompt, updatePrompt, deletePrompt } from '@/api.js';
import { Modal } from 'bootstrap';

const props = defineProps({
    projectId: Number,
    activePromptId: Number,
    uniqueId: Number, // Получаем uniqueId для корректной работы ID
});
const emit = defineEmits(['prompt-selected', 'prompts-updated']);

const prompts = ref([]);
const editingPrompt = ref(null);
const modalEl = ref(null);
let modalInstance = null;

onMounted(() => {
    if (modalEl.value) {
        modalInstance = new Modal(modalEl.value);
    }
});

// --- ИЗМЕНЕНИЕ: Открываем методы для родительского компонента ---
const show = () => modalInstance?.show();
const hide = () => modalInstance?.hide();
defineExpose({ show, hide });
// -----------------------------------------------------------

const loadPrompts = async () => {
    if (!props.projectId) return;
    try {
        const response = await getPrompts(props.projectId);
        prompts.value = response.data;
    } catch (e) { console.error("Ошибка загрузки промптов:", e); }
};

watch(() => props.projectId, loadPrompts, { immediate: true });

const startCreatePrompt = () => {
    editingPrompt.value = { name: '', content: '', project_id: props.projectId };
};
const startEditPrompt = (prompt) => {
    editingPrompt.value = { ...prompt };
};
const cancelEdit = () => {
    editingPrompt.value = null;
};
const savePrompt = async () => {
    if (!editingPrompt.value) return;
    try {
        if (editingPrompt.value.id) {
            await updatePrompt(editingPrompt.value.id, editingPrompt.value);
        } else {
            await createPrompt(editingPrompt.value);
        }
        await loadPrompts();
        emit('prompts-updated');
        cancelEdit();
    } catch (e) { console.error("Ошибка сохранения промпта:", e); }
};

const handleDeletePrompt = async (id) => {
    if (confirm("Удалить этот промпт?")) {
        try {
            await deletePrompt(id);
            await loadPrompts();
            emit('prompts-updated');
        } catch (e) { console.error("Ошибка удаления промпта:", e); }
    }
};

const selectPrompt = (id) => {
    emit('prompt-selected', id);
    hide(); // Используем наш метод
};
</script>

<style>
.prompt-editor {
    padding: 1rem;
    background-color: var(--header-bg);
    border-radius: 8px;
}
.list-group-item .text-truncate {
    max-width: 300px;
}
</style>
