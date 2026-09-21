<template>
  <div class="rich-wrap">
    <Toolbar
      :editor="editorRef"
      :defaultConfig="toolbarConfig"
      mode="default"
      class="toolbar"
    />
    <Editor
      v-model="html"
      :defaultConfig="editorConfig"
      mode="default"
      class="editor"
      @onCreated="onCreated"
    />
  </div>
</template>

<script setup>
import '@wangeditor/editor/dist/css/style.css'
import { onBeforeUnmount, shallowRef, watch, computed } from 'vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '请输入内容...' },
})

const emit = defineEmits(['update:modelValue'])

const editorRef = shallowRef()
const toolbarConfig = {}
const editorConfig = {
  placeholder: props.placeholder,
}

const html = computed({
  get: () => props.modelValue || '',
  set: (val) => emit('update:modelValue', val),
})

function onCreated(editor) {
  editorRef.value = editor
}

watch(
  () => props.modelValue,
  (val) => {
    const editor = editorRef.value
    if (!editor) return
    const cur = editor.getHtml()
    if (val !== cur) editor.setHtml(val || '')
  },
)

onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})
</script>

<style scoped>
.rich-wrap {
  border: 1px solid #ccc;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
}
.toolbar {
  border-bottom: 1px solid #ccc;
}
.editor {
  height: 280px;
  overflow-y: hidden;
}
</style>
