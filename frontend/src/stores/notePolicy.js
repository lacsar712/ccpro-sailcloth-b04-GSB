import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

// 面板登记浸渍与浸渍台账保存共用同一份后端上下限，
// 前端只做即时提示，最终结论一律以后端 /api/dips/ 的接受/拒绝为准。
export const useNotePolicyStore = defineStore('notePolicy', () => {
  const minChars = ref(null)
  const maxChars = ref(null)
  const loaded = ref(false)
  let inflight = null

  async function fetchPolicy(force = false) {
    if (loaded.value && !force) return { minChars: minChars.value, maxChars: maxChars.value }
    if (inflight) return inflight
    inflight = api
      .get('/note-policy/')
      .then(({ data }) => {
        minChars.value = data.minChars
        maxChars.value = data.maxChars
        loaded.value = true
        return { minChars: minChars.value, maxChars: maxChars.value }
      })
      .finally(() => {
        inflight = null
      })
    return inflight
  }

  function reset() {
    minChars.value = null
    maxChars.value = null
    loaded.value = false
    inflight = null
  }

  return { minChars, maxChars, loaded, fetchPolicy, reset }
})
