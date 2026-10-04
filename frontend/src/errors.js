// 从 DRF 错误响应中提取一条可读消息（字段错误取第一条）
export function errMsg(data, fallback = '操作失败') {
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  for (const value of Object.values(data)) {
    if (Array.isArray(value) && value.length) return String(value[0])
    if (typeof value === 'string') return value
  }
  return fallback
}
