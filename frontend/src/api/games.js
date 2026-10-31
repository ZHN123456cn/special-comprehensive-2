import request from './request'

const AI_TIMEOUT = 0 // 0 = 不限制等待时长，直到生成完成

/** 生成未保存的游戏草稿 */
export function generateGame(data) {
  return request.post('/games/generate', data, { timeout: AI_TIMEOUT })
}

/** 修改当前草稿，不写入数据库 */
export function reviseGame(data) {
  return request.post('/games/revise', data, { timeout: AI_TIMEOUT })
}

/** 首次保存游戏与第 1 版 */
export function saveGame(data) {
  return request.post('/games', data)
}

/** 获取当前用户的游戏列表 */
export function getGames() {
  return request.get('/games')
}

/** 获取游戏最新版本与版本元数据 */
export function getGame(id) {
  return request.get(`/games/${id}`)
}

/** 将当前草稿保存为新版本 */
export function saveVersion(gameId, data) {
  return request.post(`/games/${gameId}/versions`, data)
}

/** 读取历史版本用于恢复预览 */
export function getGameVersion(gameId, versionId) {
  return request.get(`/games/${gameId}/versions/${versionId}`)
}

/** 删除游戏及其全部版本 */
export function deleteGame(id) {
  return request.delete(`/games/${id}`)
}
