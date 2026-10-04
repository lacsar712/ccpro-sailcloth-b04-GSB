<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'
import { checkNoteLength, extractNoteError } from '../notes'
import { useNotePolicyStore } from '../stores/notePolicy'

const dips = ref([])
const rolls = ref([])
const error = ref('')
const notePolicy = useNotePolicyStore()
const form = reactive({
  rollId: null,
  startedAt: '',
  resinPct: 28,
  cureHours: '',
  notes: '',
})

const noteState = computed(() => {
  if (notePolicy.minChars == null) return { ok: true, count: 0, empty: true }
  return checkNoteLength(form.notes, notePolicy.minChars, notePolicy.maxChars)
})

function localNow() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

async function load() {
  error.value = ''
  try {
    const [d, r] = await Promise.all([
      api.get('/dips/'),
      api.get('/rolls/'),
      notePolicy.fetchPolicy(true).catch(() => null),
    ])
    dips.value = d.data.results || d.data
    rolls.value = r.data.results || r.data
    if (!form.rollId && rolls.value.length) form.rollId = rolls.value[0].id
    if (!form.startedAt) form.startedAt = localNow()
  } catch {
    error.value = '加载失败'
  }
}

async function create() {
  error.value = ''
  // 与晾晒架面板同一套上下限、同一结论。
  const noteCheck = checkNoteLength(
    form.notes,
    notePolicy.minChars ?? 1,
    notePolicy.maxChars ?? 200
  )
  if (!noteCheck.ok) {
    error.value = noteCheck.message
    return
  }
  try {
    const payload = {
      rollId: form.rollId,
      startedAt: new Date(form.startedAt).toISOString(),
      resinPct: form.resinPct,
      cureHours: form.cureHours === '' || form.cureHours === null ? null : form.cureHours,
      notes: form.notes,
    }
    await api.post('/dips/', payload)
    form.cureHours = ''
    form.notes = ''
    form.startedAt = localNow()
    await load()
  } catch (e) {
    // 后端拒绝即整笔未入库，原样展示后端结论。
    error.value =
      extractNoteError(e.response?.data) ||
      e.response?.data?.detail ||
      JSON.stringify(e.response?.data) ||
      '创建失败'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>浸渍台账</h1>
    <p class="sub">次要全量列表。日常浸渍请在晾晒架右侧面板登记；时长 ≥ 12 小时后方可将对应布卷标为已固化。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <form class="panel row" @submit.prevent="create">
      <label>布卷
        <select v-model.number="form.rollId" required>
          <option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.rollCode }} · {{ r.loftName }}</option>
        </select>
      </label>
      <label>开始时间
        <input v-model="form.startedAt" type="datetime-local" required />
      </label>
      <label>树脂 %
        <input v-model.number="form.resinPct" type="number" step="0.1" required />
      </label>
      <label>固化时长 h（可空）
        <input v-model="form.cureHours" type="number" step="0.1" />
      </label>
      <label>备注
        <input v-model="form.notes" />
        <small v-if="notePolicy.minChars != null" class="note-hint" :class="{ 'note-bad': !noteState.ok }">
          <template v-if="noteState.empty">
            留空豁免；填写则需 {{ notePolicy.minChars }}–{{ notePolicy.maxChars }} 个汉字
          </template>
          <template v-else-if="noteState.ok">
            {{ noteState.count }} 个汉字，符合区间
          </template>
          <template v-else>{{ noteState.message }}</template>
        </small>
      </label>
      <button class="btn" type="submit" :disabled="!noteState.ok">登记</button>
    </form>

    <table>
      <thead>
        <tr>
          <th>布卷</th>
          <th>帆布间</th>
          <th>开始时间</th>
          <th>树脂 %</th>
          <th>固化时长 h</th>
          <th>备注</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in dips" :key="row.id">
          <td>{{ row.rollCode }}</td>
          <td>{{ row.loftName }}</td>
          <td>{{ new Date(row.startedAt).toLocaleString() }}</td>
          <td>{{ row.resinPct }}</td>
          <td>{{ row.cureHours ?? '—' }}</td>
          <td>{{ row.notes }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
