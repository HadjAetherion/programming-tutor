<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'

const props = withDefaults(
    defineProps<{
      modelValue?: string
      language?: string
      theme?: string
    }>(),
    {
      modelValue: '',
      language: 'go',
      theme: 'vs-dark',
    },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorContainer = ref<HTMLElement | null>(null)

let editor: monaco.editor.IStandaloneCodeEditor | null = null

onMounted(() => {
  if (!editorContainer.value) {
    return
  }

  editor = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language,
    theme: props.theme,

    automaticLayout: true,

    minimap: {
      enabled: false,
    },

    fontSize: 14,

    tabSize: 4,

    scrollBeyondLastLine: false,

    scrollbar: {
      // 编辑器内滚动到边界后把滚轮交还外层页面，避免"卡在编辑器里滚不动"
      alwaysConsumeMouseWheel: false,
    },
  })

  editor.onDidChangeModelContent(() => {
    emit('update:modelValue', editor?.getValue() ?? '')
  })
})

watch(
    () => props.modelValue,
    (value) => {
      if (!editor) {
        return
      }

      if (value !== editor.getValue()) {
        editor.setValue(value)
      }
    },
)

watch(
    () => props.language,
    (language) => {
      if (!editor) {
        return
      }

      const model = editor.getModel()

      if (model) {
        monaco.editor.setModelLanguage(model, language)
      }
    },
)

onBeforeUnmount(() => {
  editor?.dispose()
  editor = null
})
</script>

<template>
  <div ref="editorContainer" class="code-editor"></div>
</template>

<style scoped>
.code-editor {
  width: 100%;
  height: 100%;
  min-height: 400px;
}
</style>