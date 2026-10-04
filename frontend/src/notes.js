// 与后端 core.rules.note_han_char_count 口径保持一致：只数汉字，
// 标点、数字、空白不计。前端仅作即时提示，真正的接受/拒绝以后端为准。
export function countHanChars(text) {
  if (!text) return 0
  const matches = text.match(/\p{Script=Han}/gu)
  return matches ? matches.length : 0
}

// 空备注（含纯空白）豁免字数；返回 { ok, count, empty, message }。
export function checkNoteLength(notes, minChars, maxChars) {
  const trimmed = (notes ?? '').trim()
  if (trimmed === '') return { ok: true, count: 0, empty: true }
  const count = countHanChars(trimmed)
  if (count < minChars) {
    return { ok: false, count, empty: false, message: `备注太短：${count} 个汉字，少于下限 ${minChars} 字` }
  }
  if (count > maxChars) {
    return { ok: false, count, empty: false, message: `备注太长：${count} 个汉字，超过上限 ${maxChars} 字` }
  }
  return { ok: true, count, empty: false }
}

export function extractNoteError(data) {
  if (!data) return ''
  if (data.notes?.[0]) return data.notes[0]
  if (data.detail) return data.detail
  if (typeof data === 'string') return data
  return ''
}
