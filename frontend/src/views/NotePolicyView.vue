<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const isAdmin = ref(auth.user?.role === 'admin')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = reactive({ minChars: 1, maxChars: 200 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/note-policy/')
    form.minChars = data.minChars
    form.maxChars = data.maxChars
  } catch {
    error.value = '字数策略加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  error.value = ''
  success.value = ''
  const min = Number(form.minChars)
  const max = Number(form.maxChars)
  if (!Number.isInteger(min) || min < 1) {
    error.value = '最短汉字数必须是不小于 1 的整数'
    return
  }
  if (!Number.isInteger(max) || max < 1) {
    error.value = '最长汉字数必须是不小于 1 的整数'
    return
  }
  if (min > max) {
    error.value = '最长汉字数不能小于最短汉字数'
    return
  }
  saving.value = true
  try {
    const { data } = await api.put('/note-policy/', { minChars: min, maxChars: max })
    form.minChars = data.minChars
    form.maxChars = data.maxChars
    success.value = `已保存：浸渍备注须在 ${data.minChars}–${data.maxChars} 个汉字之间（空备注豁免）`
  } catch (e) {
    const d = e.response?.data
    error.value = d?.maxChars?.[0] || d?.minChars?.[0] || d?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchMe()
      isAdmin.value = auth.user?.role === 'admin'
    } catch {
      isAdmin.value = false
    }
  }
  await load()
})
</script>

<template>
  <div>
    <h1>备注字数</h1>
    <p class="sub">
      设定浸渍备注的最短与最长汉字数（最短至少 1）。面板登记浸渍与浸渍台账保存共用这对上下限：
      备注汉字数落出区间时整笔拒绝、不写入；空备注豁免，其余字段不看字数。
    </p>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>

    <div v-if="loading" class="hint">加载中…</div>

    <form v-else-if="isAdmin" class="panel" style="max-width: 420px" @submit.prevent="save">
      <label>最短汉字数
        <input v-model.number="form.minChars" type="number" min="1" step="1" required />
      </label>
      <label>最长汉字数
        <input v-model.number="form.maxChars" type="number" min="1" step="1" required />
      </label>
      <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存上下限' }}</button>
    </form>

    <div v-else class="panel" style="max-width: 420px">
      <p class="hint" style="margin:0">
        当前浸渍备注字数区间：<strong>{{ form.minChars }}–{{ form.maxChars }}</strong> 个汉字（空备注豁免）。
        仅管理员可修改上下限。
      </p>
    </div>
  </div>
</template>
