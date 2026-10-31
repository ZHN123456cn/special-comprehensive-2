<template>
  <div class="workspace-shell">
    <header class="workspace-header">
      <div class="header-left">
        <button class="brand" aria-label="返回首页" @click="goHome">
          <span class="brand-mark">P</span>
          <span class="brand-copy">
            <strong>PLAYFORGE</strong>
            <small>GAME WORKSPACE</small>
          </span>
        </button>
        <span class="header-divider"></span>
        <div class="breadcrumb">
          <small>{{ isNew ? 'NEW CREATION' : `GAME / ${String(gameId).padStart(3, '0')}` }}</small>
          <strong>{{ draft.title || '未命名游戏' }}</strong>
        </div>
      </div>

      <div class="header-actions">
        <span class="save-state" :class="{ 'is-dirty': dirty }">
          <i></i>{{ saveStateLabel }}
        </span>
        <button class="home-button" @click="goHome">返回首页</button>
        <button class="save-button" :disabled="saveDisabled" @click="handleSave">
          <span v-if="saving" class="loading-spinner"></span>
          {{ saving ? '正在保存' : isNew ? '保存游戏' : '保存为新版本' }}
          <b v-if="!saving">↗</b>
        </button>
      </div>
    </header>

    <div v-if="loading" class="workspace-state">
      <span class="loading-spinner dark"></span>
      <p>正在组装你的游戏工作台</p>
    </div>

    <div v-else-if="loadError" class="workspace-state error-state">
      <span class="error-code">DRAFT NOT FOUND</span>
      <h1>工作台暂时没有内容</h1>
      <p>{{ loadError }}</p>
      <button @click="router.push('/')">返回首页重新生成</button>
    </div>

    <main v-else class="workspace-grid">
      <aside class="panel inspector-panel">
        <div class="panel-heading">
          <span>01 / GAME BRIEF</span>
          <h2>游戏信息</h2>
        </div>

        <label class="field-label" for="game-title">游戏名称</label>
        <input
          id="game-title"
          v-model="draft.title"
          class="title-input"
          maxlength="100"
          :disabled="busy"
          @input="handleMetadataEdit"
        />

        <label class="field-label" for="game-description">玩法说明</label>
        <textarea
          id="game-description"
          v-model="draft.description"
          class="description-input"
          maxlength="5000"
          rows="3"
          :disabled="busy"
          @input="handleMetadataEdit"
        ></textarea>

        <details class="original-prompt">
          <summary>查看原始需求 <span>+</span></summary>
          <p>{{ draft.original_prompt }}</p>
        </details>

        <section class="revision-section">
          <div class="revision-heading">
            <div>
              <span>02 / ITERATE</span>
              <h3>继续修改</h3>
            </div>
            <i>AI</i>
          </div>
          <p class="revision-tip">说出想调整的地方，未提到的玩法会尽量保留。</p>
          <textarea
            v-model="instruction"
            class="revision-input"
            maxlength="2000"
            :disabled="busy"
            placeholder="例如：把背景改成深蓝色，增加暂停按钮，游戏速度再快一点。"
            @keydown.ctrl.enter="handleManualRevise"
            @keydown.meta.enter="handleManualRevise"
          ></textarea>
          <div class="revision-footer">
            <span>{{ instruction.length }} / 2000</span>
            <span>Ctrl + Enter</span>
          </div>
          <button
            class="revise-button"
            :disabled="busy || instruction.trim().length < 2"
            @click="handleManualRevise"
          >
            <span v-if="revising" class="loading-spinner"></span>
            {{ revising ? revisionButtonLabel : '生成修改草稿' }}
            <b v-if="!revising">→</b>
          </button>
          <div v-if="revising" class="generation-status" role="status">
            <span class="status-pulse"></span>
            {{ revisionMode === 'auto' ? '正在自动修复运行错误' : 'MiniMax 正在重写完整游戏' }}，已等待 {{ elapsed }} 秒。
          </div>
        </section>

        <div class="model-meta">
          <div><span>生成模型</span><strong>{{ draft.model_name || '—' }}</strong></div>
          <div><span>最近生成耗时</span><strong>{{ formatDuration(draft.generation_ms) }}</strong></div>
          <p>修改只影响当前草稿，点击保存后才会形成正式版本。</p>
        </div>
      </aside>

      <section class="preview-column">
        <div class="preview-heading">
          <div class="preview-title">
            <span class="live-dot" :class="{ ready: sandboxReady }"></span>
            <div>
              <small>LIVE SANDBOX</small>
              <h2>试玩窗口</h2>
            </div>
          </div>
          <div class="preview-actions">
            <span v-if="selectedVersion" class="version-chip">V{{ selectedVersion.version_no }}</span>
            <button :disabled="busy" @click="reloadPreview">↻ 重新运行</button>
          </div>
        </div>

        <div v-if="isHistoryPreview" class="history-banner">
          <span><b>历史预览</b> 正在查看 V{{ selectedVersion.version_no }}，正式版本尚未改变。</span>
          <button :disabled="busy" @click="showLatest">回到最新版本</button>
        </div>

        <div v-if="runtimeError" class="runtime-banner" role="alert">
          <span class="warning-mark">!</span>
          <div>
            <strong>{{ revising && revisionMode === 'auto' ? '检测到运行错误，正在自动修复' : '游戏运行时出现错误' }}</strong>
            <p>{{ runtimeError }}</p>
            <small v-if="autoRepairAttempted && !revising">已执行一次自动修复；若问题仍存在，请在左侧描述并手动修改。</small>
          </div>
        </div>

        <div class="screen-frame" :class="{ 'is-busy': busy }">
          <div class="screen-chrome">
            <div><i></i><i></i><i></i></div>
            <span>PLAYFORGE / CANVAS 2D</span>
            <small>ISOLATED</small>
          </div>
          <iframe
            :key="previewKey"
            ref="previewFrame"
            class="game-frame"
            title="游戏沙箱试玩窗口"
            :srcdoc="sandboxDocument"
            sandbox="allow-scripts"
            referrerpolicy="no-referrer"
            tabindex="0"
            @load="sandboxReady = true"
          ></iframe>
          <div v-if="busy" class="preview-loading">
            <span class="loading-spinner light"></span>
            <strong>{{ saving ? '正在写入正式版本' : 'AI 正在锻造新玩法' }}</strong>
            <small>当前草稿会保留到操作成功之后</small>
          </div>
        </div>

        <div class="preview-footer">
          <span>点击游戏画面后，即可使用键盘或画面内按钮操作。</span>
          <span>NO EXTERNAL ASSETS · SANDBOXED</span>
        </div>
      </section>

      <aside class="panel versions-panel">
        <div class="panel-heading version-heading">
          <div>
            <span>03 / ARCHIVE</span>
            <h2>版本档案</h2>
          </div>
          <b>{{ isNew ? '00' : String(versions.length).padStart(2, '0') }}</b>
        </div>

        <div v-if="isNew" class="empty-versions">
          <div class="empty-version-glyph">V1</div>
          <h3>还没有正式版本</h3>
          <p>对试玩效果满意后，点击右上角“保存游戏”，即可创建第 1 版。</p>
        </div>

        <template v-else>
          <div class="latest-card">
            <span>当前正式版本</span>
            <strong>V{{ game.latest_version_no }}</strong>
            <small>{{ versions.length }} 个存档 · {{ formatDate(game.updated_at) }}</small>
          </div>

          <div class="version-list-label">
            <span>VERSION LOG</span>
            <span>点击预览</span>
          </div>
          <ol class="version-list">
            <li v-for="version in versions" :key="version.id">
              <button
                class="version-item"
                :class="{ active: selectedVersionId === version.id }"
                :disabled="busy || loadingVersionId !== null"
                @click="previewVersion(version)"
              >
                <span class="version-node">V{{ version.version_no }}</span>
                <span class="version-copy">
                  <strong>{{ version.change_prompt }}</strong>
                  <small>{{ formatDate(version.created_at) }}</small>
                  <small>{{ version.model_name }}</small>
                </span>
                <span class="version-arrow">{{ selectedVersionId === version.id ? '●' : '↗' }}</span>
                <i v-if="loadingVersionId === version.id" class="loading-spinner"></i>
              </button>
            </li>
          </ol>
          <p class="version-note">历史版本仅进入预览，不会直接覆盖当前版本；再次保存才会生成新的版本号。</p>
        </template>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getGame,
  getGameVersion,
  reviseGame,
  saveGame,
  saveVersion,
} from '../api/games'

const NEW_DRAFT_KEY = 'playforge:new-draft'
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const gameId = ref(route.params.id === 'new' ? null : Number(route.params.id))
const game = ref(null)
const versions = ref([])
const selectedVersionId = ref(null)
const loadingVersionId = ref(null)
const instruction = ref('')
const saving = ref(false)
const revising = ref(false)
const revisionMode = ref('manual')
const elapsed = ref(0)
const previewKey = ref(0)
const previewFrame = ref(null)
const sandboxReady = ref(false)
const runtimeError = ref('')
const autoRepairAttempted = ref(false)
let timer
let savedSignature = ''

const draft = reactive({
  title: '',
  description: '',
  html: '',
  original_prompt: '',
  change_prompt: '',
  generation_ms: 0,
  model_name: '',
})

const isNew = computed(() => gameId.value === null)
const busy = computed(() => saving.value || revising.value)
const selectedVersion = computed(
  () => versions.value.find((version) => version.id === selectedVersionId.value) || null,
)
const isHistoryPreview = computed(
  () => selectedVersion.value && selectedVersion.value.version_no !== game.value?.latest_version_no,
)
const currentSignature = computed(() => signatureOf(draft))
const dirty = computed(() => {
  if (!draft.html) return false
  return isNew.value || currentSignature.value !== savedSignature
})
const saveDisabled = computed(
  () => busy.value || !dirty.value || !draft.title.trim() || !draft.html || loadingVersionId.value !== null,
)
const saveStateLabel = computed(() => {
  if (saving.value) return '正在写入存档'
  if (isNew.value) return '未保存草稿'
  if (dirty.value) return '有待保存修改'
  return `已保存 · V${game.value?.latest_version_no || 1}`
})
const revisionButtonLabel = computed(() =>
  revisionMode.value === 'auto' ? '正在自动修复' : 'AI 正在修改',
)

// 安全桥接脚本只注入预览文档，不会进入保存的游戏 HTML。
const sandboxBridge = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><script>
(function () {
  function report(message) {
    try {
      parent.postMessage({ source: 'playforge-sandbox', type: 'runtime-error', message: String(message).slice(0, 800) }, '*');
    } catch (_) {}
  }
  window.addEventListener('error', function (event) {
    var location = event.lineno ? '（第 ' + event.lineno + ' 行）' : '';
    report((event.message || '未知脚本错误') + location);
  });
  window.addEventListener('unhandledrejection', function (event) {
    var reason = event.reason && event.reason.message ? event.reason.message : event.reason;
    report('未处理的 Promise 异常：' + (reason || '未知错误'));
  });
})();
<\/script>`

const sandboxDocument = computed(() => {
  if (!draft.html) return ''
  if (/<head[^>]*>/i.test(draft.html)) {
    return draft.html.replace(/<head[^>]*>/i, (tag) => tag + sandboxBridge)
  }
  return draft.html.replace(/<html[^>]*>/i, (tag) => tag + sandboxBridge)
})

function signatureOf(value) {
  return JSON.stringify({
    title: value.title,
    description: value.description,
    html: value.html,
  })
}

function applySavedGame(data) {
  game.value = data
  versions.value = [...data.versions].sort((a, b) => b.version_no - a.version_no)
  const latest = versions.value[0]
  Object.assign(draft, {
    title: data.title,
    description: data.description,
    html: data.html,
    original_prompt: data.original_prompt,
    change_prompt: '',
    generation_ms: latest?.generation_ms || 0,
    model_name: latest?.model_name || data.model_name || '',
  })
  selectedVersionId.value = latest?.id || null
  savedSignature = signatureOf(draft)
}

async function loadWorkspace() {
  loading.value = true
  loadError.value = ''
  try {
    if (isNew.value) {
      const raw = sessionStorage.getItem(NEW_DRAFT_KEY)
      if (!raw) throw new Error('未找到生成草稿，请回到首页重新描述游戏。')
      const data = JSON.parse(raw)
      if (!data.html || !data.title || !data.original_prompt) {
        throw new Error('草稿内容不完整，请回到首页重新生成。')
      }
      Object.assign(draft, {
        title: data.title,
        description: data.description || '',
        html: data.html,
        original_prompt: data.original_prompt,
        change_prompt: data.change_prompt || '初始生成',
        generation_ms: data.generation_ms || 0,
        model_name: data.model_name || '',
      })
    } else {
      if (!Number.isInteger(gameId.value) || gameId.value <= 0) {
        throw new Error('游戏地址无效，请回到首页重新选择。')
      }
      applySavedGame(await getGame(gameId.value))
    }
  } catch (error) {
    loadError.value = error.message || '游戏读取失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function handleMetadataEdit() {
  if (!draft.change_prompt || draft.change_prompt === '手动编辑游戏信息') {
    draft.change_prompt = '手动编辑游戏信息'
  }
}

function startTimer() {
  clearInterval(timer)
  elapsed.value = 0
  timer = setInterval(() => {
    elapsed.value += 1
  }, 1000)
}

function stopTimer() {
  clearInterval(timer)
  timer = undefined
}

async function runRevision(value, mode = 'manual') {
  if (busy.value || value.trim().length < 2) return
  revising.value = true
  revisionMode.value = mode
  startTimer()
  try {
    const result = await reviseGame({
      original_prompt: draft.original_prompt,
      current_html: draft.html,
      instruction: value.trim(),
    })
    Object.assign(draft, {
      title: result.title,
      description: result.description,
      html: result.html,
      generation_ms: result.generation_ms,
      model_name: result.model_name,
      change_prompt: mode === 'auto' ? `自动修复运行错误：${runtimeError.value}` : value.trim(),
    })
    if (mode === 'manual') {
      instruction.value = ''
      autoRepairAttempted.value = false
      ElMessage.success('修改草稿已生成，试玩满意后请手动保存')
    } else {
      autoRepairAttempted.value = true
      ElMessage.success('自动修复草稿已生成，请重新试玩')
    }
    runtimeError.value = ''
    sandboxReady.value = false
    previewKey.value += 1
  } catch {
    // 请求失败时不修改任何草稿内容，错误由 Axios 拦截器提示。
  } finally {
    revising.value = false
    stopTimer()
  }
}

function handleManualRevise() {
  runRevision(instruction.value, 'manual')
}

async function handleSave() {
  if (saveDisabled.value) return
  saving.value = true
  try {
    const payload = {
      title: draft.title.trim(),
      description: draft.description.trim() || '暂无玩法说明',
      html: draft.html,
      generation_ms: draft.generation_ms || 0,
      model_name: draft.model_name || 'MiniMax-M2',
    }
    const data = isNew.value
      ? await saveGame({ ...payload, original_prompt: draft.original_prompt })
      : await saveVersion(gameId.value, {
          ...payload,
          change_prompt: draft.change_prompt.trim() || '手动保存修改',
        })

    const wasNew = isNew.value
    gameId.value = data.id
    applySavedGame(data)
    sessionStorage.removeItem(NEW_DRAFT_KEY)
    instruction.value = ''
    runtimeError.value = ''
    autoRepairAttempted.value = false
    if (wasNew) await router.replace({ name: 'Workspace', params: { id: data.id } })
    ElMessage.success(wasNew ? '游戏已保存，已创建 V1' : `已保存为新版本 V${data.latest_version_no}`)
  } catch {
    // 保存失败保留当前草稿和版本选择，避免丢失用户工作。
  } finally {
    saving.value = false
  }
}

async function confirmReplaceDraft() {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm(
      '切换版本会替换当前未保存的草稿内容，确定继续吗？',
      '当前草稿尚未保存',
      { confirmButtonText: '替换并预览', cancelButtonText: '留在当前草稿', type: 'warning' },
    )
    return true
  } catch {
    return false
  }
}

function resetPreviewDiagnostics() {
  runtimeError.value = ''
  autoRepairAttempted.value = false
  sandboxReady.value = false
  previewKey.value += 1
}

async function previewVersion(version) {
  if (selectedVersionId.value === version.id || busy.value) return
  if (!(await confirmReplaceDraft())) return
  loadingVersionId.value = version.id
  try {
    const data = await getGameVersion(gameId.value, version.id)
    Object.assign(draft, {
      html: data.html,
      generation_ms: data.generation_ms,
      model_name: data.model_name,
      change_prompt: `恢复 V${data.version_no} 预览`,
    })
    selectedVersionId.value = data.id
    resetPreviewDiagnostics()
    ElMessage.info(`正在预览 V${data.version_no}，保存后会创建新版本`)
  } catch {
    // 读取失败不改变当前预览。
  } finally {
    loadingVersionId.value = null
  }
}

async function showLatest() {
  const latest = versions.value[0]
  if (!latest || selectedVersionId.value === latest.id || busy.value) return
  if (!(await confirmReplaceDraft())) return
  Object.assign(draft, {
    html: game.value.html,
    generation_ms: latest.generation_ms,
    model_name: latest.model_name,
    change_prompt: '',
  })
  selectedVersionId.value = latest.id
  resetPreviewDiagnostics()
}

function reloadPreview() {
  if (busy.value) return
  runtimeError.value = ''
  sandboxReady.value = false
  previewKey.value += 1
}

function handleSandboxMessage(event) {
  if (event.source !== previewFrame.value?.contentWindow) return
  const data = event.data
  if (data?.source !== 'playforge-sandbox' || data?.type !== 'runtime-error') return
  runtimeError.value = data.message || '未知运行错误'
  if (!autoRepairAttempted.value && !busy.value && draft.html) {
    autoRepairAttempted.value = true
    runRevision(
      `游戏在浏览器沙箱中运行时报错：${runtimeError.value}。请定位并修复错误，返回完整可运行游戏，保留原有玩法。`,
      'auto',
    )
  }
}

function handleBeforeUnload(event) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

function goHome() {
  router.push('/')
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDuration(value) {
  if (!value) return '—'
  return value >= 1000 ? `${(value / 1000).toFixed(1)} 秒` : `${value} 毫秒`
}

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm(
      '当前游戏还有未保存的草稿或修改，离开后这些内容将丢失。',
      '确定离开工作台吗？',
      { confirmButtonText: '放弃草稿并离开', cancelButtonText: '继续编辑', type: 'warning' },
    )
    if (isNew.value) sessionStorage.removeItem(NEW_DRAFT_KEY)
    return true
  } catch {
    return false
  }
})

onMounted(() => {
  window.addEventListener('message', handleSandboxMessage)
  window.addEventListener('beforeunload', handleBeforeUnload)
  loadWorkspace()
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleSandboxMessage)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  stopTimer()
})
</script>

<style scoped>
.workspace-shell {
  min-height: 100vh;
  background:
    linear-gradient(rgba(23, 32, 28, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23, 32, 28, 0.04) 1px, transparent 1px),
    var(--paper);
  background-size: 36px 36px;
}

.workspace-header {
  position: relative;
  z-index: 5;
  min-height: 78px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 12px 24px;
  border-bottom: 2px solid var(--ink);
  background: rgba(242, 241, 233, 0.96);
}

.header-left,
.header-actions,
.brand,
.preview-heading,
.preview-title,
.preview-actions {
  display: flex;
  align-items: center;
}

.header-left { min-width: 0; gap: 20px; }
.brand { gap: 10px; color: var(--ink); border: 0; background: transparent; text-align: left; }
.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: var(--lime);
  border-radius: 8px 8px 8px 2px;
  background: var(--ink);
  font-family: 'Lucida Console', monospace;
  font-size: 23px;
  font-weight: 900;
}
.brand-copy { display: flex; flex-direction: column; gap: 3px; }
.brand-copy strong { font-family: 'Lucida Console', monospace; font-size: 15px; letter-spacing: 1px; }
.brand-copy small { color: var(--muted); font-family: 'Lucida Console', monospace; font-size: 8px; letter-spacing: 1.5px; }
.header-divider { width: 1px; height: 38px; background: #c8cbc4; }
.breadcrumb { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.breadcrumb small { color: var(--coral); font-family: 'Lucida Console', monospace; font-size: 9px; letter-spacing: 1px; }
.breadcrumb strong { max-width: 300px; overflow: hidden; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.header-actions { gap: 12px; }
.save-state { display: flex; align-items: center; gap: 7px; color: var(--muted); font-size: 11px; }
.save-state i { width: 7px; height: 7px; border-radius: 50%; background: #55a773; }
.save-state.is-dirty i { background: var(--coral); box-shadow: 0 0 0 4px rgba(255, 121, 92, 0.12); }
.home-button,
.preview-actions button {
  padding: 9px 13px;
  color: var(--ink);
  border: 1px solid #b9beb8;
  border-radius: 5px;
  background: transparent;
  font-size: 12px;
}
.home-button:hover,
.preview-actions button:hover:not(:disabled) { border-color: var(--ink); background: #fffef7; }
.save-button {
  min-width: 154px;
  height: 43px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 18px;
  color: var(--lime);
  border: 2px solid var(--ink);
  border-radius: 7px 7px 7px 2px;
  background: var(--ink);
  font-size: 13px;
  font-weight: 800;
  box-shadow: 4px 4px 0 var(--coral);
  transition: transform 0.18s, box-shadow 0.18s;
}
.save-button:hover:not(:disabled) { transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--coral); }
.save-button:disabled { opacity: 0.45; box-shadow: none; }
.save-button b { font-size: 18px; }

.workspace-state {
  min-height: calc(100vh - 78px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  padding: 40px;
  text-align: center;
}
.workspace-state p { color: var(--muted); }
.error-state .error-code { color: var(--coral); font-family: 'Lucida Console', monospace; font-size: 11px; letter-spacing: 2px; }
.error-state h1 { font-size: clamp(28px, 4vw, 44px); }
.error-state button { margin-top: 10px; padding: 12px 20px; color: var(--ink); border: 1px solid var(--ink); border-radius: 6px; background: var(--lime); font-weight: 700; }

.workspace-grid {
  width: 100%;
  max-width: 1800px;
  height: calc(100vh - 78px);
  min-height: 690px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 310px minmax(420px, 1fr) 250px;
  gap: 18px;
  padding: 20px 24px 24px;
}
.panel {
  min-width: 0;
  overflow-y: auto;
  padding: 22px;
  border: 1px solid #c5c9c2;
  border-radius: 12px 12px 12px 3px;
  background: rgba(251, 250, 243, 0.9);
  animation: panel-in 0.45s both;
}
.panel-heading { margin-bottom: 24px; }
.panel-heading > span,
.panel-heading > div > span,
.revision-heading span,
.preview-title small,
.version-list-label,
.screen-chrome,
.model-meta span {
  color: var(--muted);
  font-family: 'Lucida Console', monospace;
  font-size: 9px;
  letter-spacing: 1.2px;
}
.panel-heading h2 { margin-top: 6px; font-size: 23px; letter-spacing: -0.8px; }
.field-label { display: block; margin: 17px 0 7px; color: #59635d; font-size: 11px; font-weight: 700; }
.title-input,
.description-input,
.revision-input {
  width: 100%;
  color: var(--ink);
  border: 1px solid #c8ccc5;
  border-radius: 6px;
  outline: 0;
  background: #fffef8;
  transition: border 0.18s, box-shadow 0.18s;
}
.title-input:focus,
.description-input:focus,
.revision-input:focus { border-color: var(--ink); box-shadow: 3px 3px 0 var(--lime); }
.title-input { height: 42px; padding: 0 12px; font-size: 15px; font-weight: 800; }
.description-input { min-height: 82px; padding: 10px 12px; resize: vertical; font-size: 12px; line-height: 1.7; }
.title-input:disabled,
.description-input:disabled,
.revision-input:disabled { opacity: 0.65; }
.original-prompt { margin: 16px 0 24px; border-bottom: 1px solid #dcded7; }
.original-prompt summary { display: flex; justify-content: space-between; padding: 0 0 13px; color: var(--muted); cursor: pointer; font-size: 11px; list-style: none; }
.original-prompt summary::-webkit-details-marker { display: none; }
.original-prompt[open] summary span { transform: rotate(45deg); }
.original-prompt p { padding: 0 0 15px; color: #59635d; font-size: 11px; line-height: 1.8; white-space: pre-wrap; }

.revision-section { padding-top: 2px; }
.revision-heading { display: flex; align-items: center; justify-content: space-between; }
.revision-heading h3 { margin-top: 5px; font-size: 20px; }
.revision-heading > i { width: 34px; height: 34px; display: grid; place-items: center; color: var(--lime); border-radius: 50%; background: var(--ink); font-family: 'Lucida Console', monospace; font-size: 11px; font-style: normal; }
.revision-tip { margin: 12px 0; color: var(--muted); font-size: 11px; line-height: 1.7; }
.revision-input { min-height: 128px; padding: 12px; resize: vertical; font-size: 12px; line-height: 1.75; }
.revision-input::placeholder { color: #939b95; }
.revision-footer { display: flex; justify-content: space-between; margin: 7px 0 12px; color: #8a928c; font-size: 9px; }
.revise-button {
  width: 100%;
  height: 43px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--ink);
  border: 1px solid var(--ink);
  border-radius: 6px;
  background: var(--lime);
  font-size: 12px;
  font-weight: 800;
}
.revise-button:hover:not(:disabled) { background: #dcff94; }
.revise-button:disabled { opacity: 0.45; }
.revise-button b { font-size: 18px; }
.generation-status { display: flex; align-items: flex-start; gap: 8px; margin-top: 12px; padding: 10px; color: #d7ded9; border-radius: 5px; background: var(--ink); font-size: 10px; line-height: 1.6; }
.status-pulse { width: 7px; height: 7px; flex: 0 0 auto; margin-top: 4px; border-radius: 50%; background: var(--lime); animation: pulse 1.1s infinite; }
.model-meta { margin-top: 24px; padding-top: 16px; border-top: 1px solid #dcded7; }
.model-meta > div { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.model-meta strong { max-width: 160px; overflow: hidden; font-family: 'Lucida Console', monospace; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.model-meta p { margin-top: 15px; color: #7a837d; font-size: 10px; line-height: 1.7; }

.preview-column { min-width: 0; display: flex; flex-direction: column; animation: panel-in 0.45s 0.08s both; }
.preview-heading { min-height: 52px; justify-content: space-between; gap: 16px; margin-bottom: 12px; }
.preview-title { gap: 11px; }
.preview-title h2 { margin-top: 3px; font-size: 21px; }
.live-dot { width: 11px; height: 11px; border: 2px solid var(--ink); border-radius: 50%; background: #b1b7b1; }
.live-dot.ready { background: var(--lime); box-shadow: 0 0 0 5px rgba(201, 242, 119, 0.25); }
.preview-actions { gap: 9px; }
.version-chip { padding: 6px 9px; color: var(--ink); border: 1px solid var(--ink); border-radius: 4px; background: var(--lime); font-family: 'Lucida Console', monospace; font-size: 10px; font-weight: 800; }
.preview-actions button { background: #fbfaf3; font-size: 11px; }
.history-banner,
.runtime-banner { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; padding: 10px 13px; border: 1px solid var(--ink); border-radius: 6px; font-size: 11px; }
.history-banner { justify-content: space-between; background: #fff1b9; }
.history-banner button { flex: 0 0 auto; color: var(--ink); border: 0; border-bottom: 1px solid var(--ink); background: transparent; font-size: 10px; font-weight: 800; }
.runtime-banner { align-items: flex-start; color: #702e20; border-color: #d5664f; background: #fff0e9; }
.warning-mark { width: 22px; height: 22px; display: grid; place-items: center; flex: 0 0 auto; color: white; border-radius: 50%; background: #d95b42; font-weight: 900; }
.runtime-banner strong { font-size: 11px; }
.runtime-banner p { margin-top: 3px; overflow-wrap: anywhere; font-family: 'Lucida Console', monospace; font-size: 9px; line-height: 1.5; }
.runtime-banner small { display: block; margin-top: 5px; font-size: 9px; }
.screen-frame {
  position: relative;
  min-height: 0;
  flex: 1;
  overflow: hidden;
  border: 2px solid var(--ink);
  border-radius: 14px 14px 14px 3px;
  background: #111a17;
  box-shadow: 8px 8px 0 var(--coral);
}
.screen-chrome { height: 38px; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 14px; color: #99a69e; border-bottom: 1px solid #3b4842; background: var(--ink); font-size: 8px; }
.screen-chrome > div { display: flex; gap: 5px; }
.screen-chrome i { width: 7px; height: 7px; border-radius: 50%; background: #55635c; }
.screen-chrome i:first-child { background: var(--coral); }
.screen-chrome i:nth-child(2) { background: #ffd665; }
.screen-chrome i:last-child { background: var(--lime); }
.screen-chrome small { color: var(--lime); font-size: 8px; }
.game-frame { width: 100%; height: calc(100% - 38px); min-height: 480px; display: block; border: 0; background: white; }
.preview-loading { position: absolute; inset: 38px 0 0; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 12px; color: #f4f5ec; background: rgba(17, 26, 23, 0.88); backdrop-filter: blur(5px); }
.preview-loading strong { margin-top: 8px; font-size: 18px; }
.preview-loading small { color: #a6b1aa; font-size: 11px; }
.preview-footer { display: flex; justify-content: space-between; gap: 16px; padding: 17px 2px 0; color: #77817a; font-size: 9px; }
.preview-footer span:last-child { flex: 0 0 auto; font-family: 'Lucida Console', monospace; font-size: 8px; letter-spacing: 0.6px; }

.versions-panel { animation-delay: 0.16s; }
.version-heading { display: flex; align-items: flex-start; justify-content: space-between; }
.version-heading > b { color: #d5d8d1; font-family: 'Lucida Console', monospace; font-size: 34px; line-height: 1; }
.empty-versions { padding: 26px 4px; text-align: center; }
.empty-version-glyph { width: 76px; height: 76px; display: grid; place-items: center; margin: 0 auto 20px; color: var(--lime); border: 2px solid var(--ink); border-radius: 50%; background: var(--ink); box-shadow: 5px 5px 0 var(--coral); font-family: 'Lucida Console', monospace; font-size: 21px; font-weight: 900; }
.empty-versions h3 { font-size: 16px; }
.empty-versions p,
.version-note { margin-top: 12px; color: var(--muted); font-size: 11px; line-height: 1.8; }
.latest-card { position: relative; overflow: hidden; padding: 17px; color: #f4f5ed; border-radius: 8px 8px 8px 2px; background: var(--ink); }
.latest-card::after { content: ''; position: absolute; right: -22px; bottom: -32px; width: 86px; height: 86px; border: 18px solid var(--lime); border-radius: 50%; opacity: 0.18; }
.latest-card > span { color: #a7b3ac; font-size: 10px; }
.latest-card strong { display: block; margin: 7px 0; color: var(--lime); font-family: 'Lucida Console', monospace; font-size: 34px; }
.latest-card small { color: #a7b3ac; font-size: 9px; }
.version-list-label { display: flex; justify-content: space-between; margin: 24px 0 10px; font-size: 8px; }
.version-list { list-style: none; }
.version-list li { position: relative; }
.version-list li:not(:last-child)::after { content: ''; position: absolute; left: 17px; top: 48px; bottom: -5px; width: 1px; background: #ccd0c9; }
.version-item { position: relative; width: 100%; display: flex; align-items: flex-start; gap: 10px; padding: 12px 7px; color: var(--ink); border: 1px solid transparent; border-radius: 7px; background: transparent; text-align: left; }
.version-item:hover:not(:disabled) { background: #f0f2e8; }
.version-item.active { border-color: var(--ink); background: #eff7df; }
.version-node { position: relative; z-index: 1; width: 34px; height: 26px; display: grid; place-items: center; flex: 0 0 auto; color: var(--ink); border: 1px solid #aeb5ae; border-radius: 4px; background: #fbfaf3; font-family: 'Lucida Console', monospace; font-size: 9px; font-weight: 800; }
.version-item.active .version-node { border-color: var(--ink); background: var(--lime); }
.version-copy { min-width: 0; display: flex; flex: 1; flex-direction: column; gap: 4px; }
.version-copy strong { display: -webkit-box; overflow: hidden; font-size: 11px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.version-copy small { overflow: hidden; color: #89918b; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
.version-arrow { color: #89918b; font-size: 11px; }
.version-item.active .version-arrow { color: #5a8e2e; }
.version-item > .loading-spinner { position: absolute; right: 8px; bottom: 8px; width: 12px; height: 12px; }
.version-note { padding-top: 18px; border-top: 1px solid #dcded7; font-size: 10px; }

.loading-spinner { width: 15px; height: 15px; display: inline-block; flex: 0 0 auto; border: 2px solid rgba(201, 242, 119, 0.28); border-top-color: var(--lime); border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-spinner.dark { width: 26px; height: 26px; border-color: rgba(23, 32, 28, 0.2); border-top-color: var(--ink); }
.loading-spinner.light { width: 28px; height: 28px; }
.revise-button .loading-spinner,
.version-item .loading-spinner { border-color: rgba(23, 32, 28, 0.25); border-top-color: var(--ink); }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 50% { opacity: 0.35; transform: scale(0.75); } }
@keyframes panel-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1240px) {
  .workspace-grid { height: auto; min-height: calc(100vh - 78px); grid-template-columns: 300px minmax(0, 1fr); }
  .preview-column { min-height: 680px; }
  .versions-panel { grid-column: 1 / -1; overflow: visible; }
  .version-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .version-list li::after { display: none; }
  .version-note { max-width: 600px; }
  .save-state { display: none; }
}

@media (max-width: 820px) {
  .workspace-header { align-items: flex-start; flex-wrap: wrap; padding: 12px 16px; }
  .header-left { width: 100%; }
  .header-divider, .breadcrumb { display: none; }
  .header-actions { width: 100%; justify-content: flex-end; }
  .home-button { margin-right: auto; }
  .workspace-grid { display: flex; flex-direction: column; padding: 16px; }
  .preview-column { order: -1; min-height: 600px; }
  .panel { overflow: visible; }
  .game-frame { min-height: 470px; }
  .preview-footer span:last-child { display: none; }
  .version-list { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 520px) {
  .brand-copy small { display: none; }
  .save-button { min-width: 142px; padding: 0 12px; }
  .home-button { padding: 9px; }
  .workspace-grid { padding: 12px; }
  .preview-column { min-height: 510px; }
  .preview-heading { align-items: flex-start; }
  .preview-title h2 { font-size: 18px; }
  .preview-actions button { padding: 8px; }
  .game-frame { min-height: 390px; }
  .history-banner { align-items: flex-start; flex-direction: column; }
  .screen-chrome > span { display: none; }
  .panel { padding: 18px; }
  .version-list { grid-template-columns: 1fr; }
  .preview-footer { line-height: 1.6; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
}
</style>
