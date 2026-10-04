<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'
import { errMsg } from '../errors'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')

const rule = ref(null)
const form = reactive({ minChars: 1, maxChars: 200 })
const error = ref('')
const okMsg = ref('')
const busy = ref(false)

async function load() {
  error.value = ''
  try {
    const { data } = await api.get('/note-length-rule/')
    rule.value = data
    form.minChars = data.minChars
    form.maxChars = data.maxChars
  } catch (e) {
    error.value = errMsg(e.response?.data, '规则加载失败')
  }
}

async function save() {
  error.value = ''
  okMsg.value = ''
  const min = Number(form.minChars)
  const max = Number(form.maxChars)
  if (!Number.isInteger(min) || min < 1) {
    error.value = '最短字数至少为 1'
    return
  }
  if (!Number.isInteger(max) || max < min) {
    error.value = '最长字数不能小于最短字数'
    return
  }
  busy.value = true
  try {
    const { data } = await api.put('/note-length-rule/', {
      minChars: min,
      maxChars: max,
    })
    rule.value = data
    okMsg.value = `已保存：备注留空或 ${data.minChars}–${data.maxChars} 字`
  } catch (e) {
    error.value = errMsg(e.response?.data, '保存失败')
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>备注字数</h1>
    <p class="sub">
      专页设定浸渍备注的最短与最长汉字数（最短至少 1）。登记浸渍时备注留空不校验；
      非空备注字数落在区间外将整笔拒绝，不会落库。改卷态、标已固化及备注以外字段不看字数。
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <section class="panel">
      <p v-if="rule" class="hint" style="margin:0 0 14px">
        当前规则：最短 {{ rule.minChars }} 字 · 最长 {{ rule.maxChars }} 字
      </p>
      <form class="row" @submit.prevent="save">
        <label>最短字数
          <input
            v-model.number="form.minChars"
            type="number"
            min="1"
            step="1"
            required
            :disabled="!isAdmin || busy"
          />
        </label>
        <label>最长字数
          <input
            v-model.number="form.maxChars"
            type="number"
            min="1"
            step="1"
            required
            :disabled="!isAdmin || busy"
          />
        </label>
        <button v-if="isAdmin" class="btn" type="submit" :disabled="busy">保存规则</button>
      </form>
      <p v-if="!isAdmin" class="hint" style="margin:12px 0 0">
        仅管理员可修改；当前账号 {{ auth.user?.username }} 为操作工，仅可查看。
      </p>
    </section>
  </div>
</template>
