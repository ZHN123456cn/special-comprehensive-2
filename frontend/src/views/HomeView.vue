<template>
  <div class="home-shell">
    <header class="topbar">
      <button class="brand" aria-label="返回首页" @click="scrollTop">
        <span class="brand-mark">P</span>
        <span class="brand-copy">
          <strong>PLAYFORGE</strong>
          <small>AI 小游戏生成所</small>
        </span>
      </button>
      <div class="user-area">
        <span class="user-dot"></span>
        <span>{{ user?.username || '创作者' }}</span>
        <button class="text-button" @click="logout">退出</button>
      </div>
    </header>

    <main>
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow"><span></span> NATURAL LANGUAGE → PLAYABLE GAME</p>
          <h1>一句话，<br /><em>开场。</em></h1>
          <p class="hero-description">
            描述玩法、角色和规则，让 MiniMax 为你写出完整游戏。
            无需代码，生成即可试玩，满意后再保存。
          </p>
          <div class="capability-row" aria-label="平台能力">
            <span>真实 AI 生成</span>
            <span>即时沙箱试玩</span>
            <span>多轮自然语言修改</span>
          </div>
        </div>

        <div class="arcade-wrap" aria-hidden="true">
          <div class="arcade-shadow"></div>
          <div class="arcade-machine">
            <div class="machine-top">
              <span>PLAY / 001</span>
              <span class="machine-light"></span>
            </div>
            <div class="machine-screen">
              <div class="screen-hud"><span>SCORE 0240</span><span>LIVES 03</span></div>
              <div class="pixel-scene">
                <i class="pixel player"></i>
                <i class="pixel coin coin-a"></i>
                <i class="pixel coin coin-b"></i>
                <i class="pixel enemy enemy-a"></i>
                <i class="pixel enemy enemy-b"></i>
                <i class="scene-line line-a"></i>
                <i class="scene-line line-b"></i>
              </div>
              <span class="screen-caption">CANVAS READY</span>
            </div>
            <div class="machine-controls">
              <span class="control-stick"></span>
              <span class="control-button button-a"></span>
              <span class="control-button button-b"></span>
            </div>
          </div>
          <span class="arcade-note note-top">PROMPT IN</span>
          <span class="arcade-note note-bottom">GAME OUT</span>
        </div>
      </section>

      <section id="create" class="creator-section">
        <div class="section-heading">
          <span class="section-number">01</span>
          <div>
            <p>DESCRIBE YOUR GAME</p>
            <h2>你想做一个什么游戏？</h2>
          </div>
        </div>

        <div class="prompt-composer" :class="{ 'is-generating': generating }">
          <label for="game-prompt">游戏需求</label>
          <textarea
            id="game-prompt"
            v-model="prompt"
            :disabled="generating"
            maxlength="2000"
            placeholder="例如：做一个太空打飞机游戏，方向键移动，空格发射，击中小行星加分，碰撞后结束，带开始和重新开始按钮。"
            @keydown.ctrl.enter="handleGenerate"
            @keydown.meta.enter="handleGenerate"
          ></textarea>
          <div class="composer-footer">
            <span>{{ prompt.length }} / 2000 · Ctrl + Enter 生成</span>
            <button
              class="generate-button"
              :disabled="generating || prompt.trim().length < 4"
              @click="handleGenerate"
            >
              <span>{{ generating ? 'AI 正在生成' : '生成我的游戏' }}</span>
              <b v-if="!generating">→</b>
              <i v-else class="loading-spinner"></i>
            </button>
          </div>
          <div v-if="generating" class="generation-status" role="status">
            <span class="status-pulse"></span>
            MiniMax 正在设计玩法并编写完整代码，已等待 {{ elapsed }} 秒。请勿重复提交。
          </div>
        </div>

        <div class="example-grid">
          <button
            v-for="(example, index) in examples"
            :key="example.name"
            class="example-card"
            :disabled="generating"
            @click="applyExample(example)"
          >
            <span class="example-index">0{{ index + 1 }}</span>
            <span class="example-content">
              <strong>{{ example.name }}</strong>
              <small>{{ example.summary }}</small>
            </span>
            <span class="example-arrow">↗</span>
          </button>
        </div>
      </section>

      <section class="library-section">
        <div class="section-heading library-heading">
          <span class="section-number">02</span>
          <div>
            <p>YOUR SAVED ARCADE</p>
            <h2>我的游戏</h2>
          </div>
          <span class="game-count">{{ games.length }} 个作品</span>
        </div>

        <div v-if="gamesLoading" class="library-state">
          <span class="loading-spinner dark"></span> 正在读取游戏列表
        </div>
        <div v-else-if="games.length === 0" class="empty-library">
          <span class="empty-code">NO SAVED GAMES / YET</span>
          <h3>你的第一台游戏机，正等待一句描述。</h3>
          <p>生成后可以反复试玩和修改，只有点击保存的作品才会出现在这里。</p>
          <button class="outline-button" @click="focusPrompt">开始创作</button>
        </div>
        <div v-else class="game-grid">
          <article
            v-for="(game, index) in games"
            :key="game.id"
            class="game-card"
            tabindex="0"
            @click="openGame(game.id)"
            @keydown.enter="openGame(game.id)"
          >
            <div class="game-card-top">
              <span>GAME {{ String(index + 1).padStart(3, '0') }}</span>
              <button class="delete-button" aria-label="删除游戏" @click.stop="removeGame(game)">删除</button>
            </div>
            <div class="game-glyph" aria-hidden="true">
              <span></span><i></i><b></b>
            </div>
            <h3>{{ game.title }}</h3>
            <p>{{ game.description }}</p>
            <div class="game-card-footer">
              <span>V{{ game.latest_version_no }} · {{ game.version_count }} 个版本</span>
              <span>{{ formatDate(game.updated_at) }}</span>
            </div>
          </article>
        </div>
      </section>
    </main>

    <footer class="footer">
      <span>PLAYFORGE / COURSE PROJECT</span>
      <span>VUE 3 · FASTAPI · MINIMAX · MYSQL</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteGame, generateGame, getGames } from '../api/games'

const NEW_DRAFT_KEY = 'playforge:new-draft'

const router = useRouter()
const prompt = ref('')
const generating = ref(false)
const elapsed = ref(0)
const games = ref([])
const gamesLoading = ref(true)
let timer

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
})

const examples = [
  {
    name: '贪吃蛇大作战',
    summary: '方向控制 · 食物成长 · 速度递进',
    prompt: '生成一个霓虹像素风贪吃蛇游戏，方向键或 WASD 控制，吃到食物加分并变长，每吃 5 个食物速度提升，撞墙或撞到自己结束，提供开始、暂停和重新开始按钮。',
  },
  {
    name: '星际接金币',
    summary: '左右移动 · 道具掉落 · 生命机制',
    prompt: '生成一个星际主题接金币游戏，玩家控制一艘小飞船左右移动，金币和陨石随机掉落，接到金币加 10 分，碰到陨石损失一条生命，三条生命用完结束，包含开始和重新开始。',
  },
  {
    name: '深空打飞机',
    summary: '移动射击 · 爆炸粒子 · 分数记录',
    prompt: '生成一个太空打飞机游戏，方向键移动，空格发射子弹，敌机从上方出现，击中敌机加分并显示爆炸粒子，玩家与敌机碰撞后结束，带操作说明、分数和重新开始按钮。',
  },
]

function scrollTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function focusPrompt() {
  document.getElementById('create')?.scrollIntoView({ behavior: 'smooth' })
  setTimeout(() => document.getElementById('game-prompt')?.focus(), 400)
}

function applyExample(example) {
  prompt.value = example.prompt
  focusPrompt()
}

function startTimer() {
  elapsed.value = 0
  clearInterval(timer)
  timer = setInterval(() => {
    elapsed.value += 1
  }, 1000)
}

async function handleGenerate() {
  const value = prompt.value.trim()
  if (value.length < 4 || generating.value) return
  generating.value = true
  startTimer()
  try {
    const draft = await generateGame({ prompt: value })
    sessionStorage.setItem(
      NEW_DRAFT_KEY,
      JSON.stringify({ ...draft, original_prompt: value, change_prompt: '初始生成' }),
    )
    router.push({ name: 'Workspace', params: { id: 'new' } })
  } catch {
    // 错误提示由 Axios 拦截器统一处理
  } finally {
    generating.value = false
    clearInterval(timer)
  }
}

async function loadGames() {
  gamesLoading.value = true
  try {
    games.value = await getGames()
  } catch {
    // 错误提示由 Axios 拦截器统一处理
  } finally {
    gamesLoading.value = false
  }
}

function openGame(id) {
  router.push({ name: 'Workspace', params: { id } })
}

async function removeGame(game) {
  try {
    await ElMessageBox.confirm(
      `确定删除《${game.title}》及其全部版本吗？此操作不可恢复。`,
      '删除游戏',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' },
    )
    await deleteGame(game.id)
    games.value = games.value.filter((item) => item.id !== game.id)
    ElMessage.success('游戏已删除')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      // 接口错误由 Axios 拦截器统一处理
    }
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.removeItem(NEW_DRAFT_KEY)
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(loadGames)
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.home-shell {
  min-height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(rgba(23, 32, 28, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23, 32, 28, 0.045) 1px, transparent 1px),
    #f2f1e9;
  background-size: 42px 42px;
}

.topbar {
  width: min(1240px, calc(100% - 48px));
  height: 88px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(23, 32, 28, 0.2);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--ink);
  border: 0;
  background: transparent;
  text-align: left;
}

.brand-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: var(--lime);
  background: var(--ink);
  border-radius: 9px 9px 9px 2px;
  font-family: 'Lucida Console', monospace;
  font-size: 22px;
  font-weight: 900;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-copy strong {
  font-family: 'Lucida Console', monospace;
  font-size: 17px;
  letter-spacing: 1.5px;
}

.brand-copy small {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 2px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.user-dot {
  width: 8px;
  height: 8px;
  background: #5aaf78;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(90, 175, 120, 0.12);
}

.text-button {
  margin-left: 10px;
  padding: 7px 12px;
  color: var(--muted);
  border: 1px solid rgba(23, 32, 28, 0.2);
  border-radius: 6px;
  background: transparent;
}

.text-button:hover {
  color: var(--ink);
  border-color: var(--ink);
}

.hero {
  width: min(1240px, calc(100% - 48px));
  min-height: 600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  align-items: center;
  gap: 64px;
  padding: 64px 0 74px;
}

.eyebrow,
.section-heading p,
.empty-code,
.footer {
  font-family: 'Lucida Console', monospace;
  letter-spacing: 1.5px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #52615a;
  font-size: 12px;
}

.eyebrow span {
  width: 28px;
  height: 3px;
  background: var(--coral);
}

.hero h1 {
  margin: 26px 0 28px;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
  font-size: clamp(72px, 9vw, 126px);
  line-height: 0.94;
  letter-spacing: -7px;
}

.hero h1 em {
  position: relative;
  color: var(--ink);
  font-style: normal;
  z-index: 1;
}

.hero h1 em::after {
  content: '';
  position: absolute;
  z-index: -1;
  left: -8px;
  right: -18px;
  bottom: 4px;
  height: 28%;
  background: var(--lime);
  transform: rotate(-2deg);
}

.hero-description {
  max-width: 540px;
  color: #55605a;
  font-size: 17px;
  line-height: 1.9;
}

.capability-row {
  margin-top: 34px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.capability-row span {
  padding: 8px 12px;
  border: 1px solid rgba(23, 32, 28, 0.18);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.45);
  font-size: 12px;
}

.arcade-wrap {
  position: relative;
  width: min(100%, 430px);
  justify-self: center;
  padding: 24px;
  transform: rotate(2deg);
}

.arcade-shadow {
  position: absolute;
  inset: 38px 8px 6px 48px;
  background: var(--coral);
  border: 2px solid var(--ink);
  border-radius: 24px;
}

.arcade-machine {
  position: relative;
  padding: 18px;
  border: 2px solid var(--ink);
  border-radius: 24px 24px 38px 24px;
  background: #e5e1d4;
  box-shadow: 0 24px 50px rgba(23, 32, 28, 0.14);
}

.machine-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px 14px;
  font-family: 'Lucida Console', monospace;
  font-size: 12px;
  font-weight: 700;
}

.machine-light {
  width: 10px;
  height: 10px;
  background: var(--coral);
  border: 2px solid var(--ink);
  border-radius: 50%;
}

.machine-screen {
  position: relative;
  height: 320px;
  overflow: hidden;
  padding: 16px;
  color: #d7f99b;
  border: 3px solid var(--ink);
  border-radius: 14px;
  background:
    linear-gradient(rgba(201, 242, 119, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(201, 242, 119, 0.06) 1px, transparent 1px),
    #16221e;
  background-size: 22px 22px;
  box-shadow: inset 0 0 32px rgba(0, 0, 0, 0.5);
}

.screen-hud {
  display: flex;
  justify-content: space-between;
  font-family: 'Lucida Console', monospace;
  font-size: 10px;
}

.pixel-scene {
  position: relative;
  height: 230px;
}

.pixel {
  position: absolute;
  display: block;
  width: 24px;
  height: 24px;
  border: 3px solid #101815;
}

.player {
  left: 44%;
  bottom: 22px;
  width: 44px;
  height: 36px;
  background: var(--lime);
  clip-path: polygon(50% 0, 100% 100%, 50% 76%, 0 100%);
  animation: hover-ship 2s ease-in-out infinite;
}

.coin {
  width: 17px;
  height: 17px;
  background: #ffd665;
  border-radius: 50%;
  box-shadow: 0 0 14px rgba(255, 214, 101, 0.5);
}

.coin-a { left: 22%; top: 36%; }
.coin-b { right: 20%; top: 52%; }

.enemy {
  width: 27px;
  height: 20px;
  background: var(--coral);
  clip-path: polygon(0 0, 100% 0, 80% 100%, 20% 100%);
}

.enemy-a { left: 24%; top: 72px; }
.enemy-b { right: 22%; top: 112px; }

.scene-line {
  position: absolute;
  width: 3px;
  height: 28px;
  background: var(--lime);
  animation: shot 1.8s linear infinite;
}

.line-a { left: 49%; top: 90px; }
.line-b { left: 53%; top: 136px; animation-delay: 0.7s; }

.screen-caption {
  position: absolute;
  left: 16px;
  bottom: 12px;
  font-family: 'Lucida Console', monospace;
  font-size: 10px;
  letter-spacing: 2px;
}

.machine-controls {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 18px;
}

.control-stick {
  margin-right: auto;
  width: 46px;
  height: 46px;
  border: 2px solid var(--ink);
  border-radius: 50%;
  background: #7b8580;
  box-shadow: inset 0 0 0 10px #b4b7ad;
}

.control-button {
  width: 30px;
  height: 30px;
  border: 2px solid var(--ink);
  border-radius: 50%;
}

.button-a { background: var(--coral); }
.button-b { background: var(--lime); }

.arcade-note {
  position: absolute;
  padding: 7px 10px;
  color: var(--ink);
  border: 1px solid var(--ink);
  background: var(--paper);
  font-family: 'Lucida Console', monospace;
  font-size: 10px;
  letter-spacing: 1px;
}

.note-top { top: 6px; right: -12px; transform: rotate(6deg); }
.note-bottom { bottom: 4px; left: -16px; transform: rotate(-7deg); }

.creator-section,
.library-section {
  width: min(1240px, calc(100% - 48px));
  margin: 0 auto;
  padding: 68px 0;
  border-top: 1px solid rgba(23, 32, 28, 0.2);
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 28px;
}

.section-number {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  color: var(--lime);
  background: var(--ink);
  border-radius: 50%;
  font-family: 'Lucida Console', monospace;
  font-size: 14px;
}

.section-heading p {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 10px;
}

.section-heading h2 {
  font-size: clamp(24px, 3vw, 34px);
  letter-spacing: -1px;
}

.prompt-composer {
  position: relative;
  padding: 26px;
  color: #f5f5eb;
  border: 2px solid var(--ink);
  border-radius: 16px 16px 16px 4px;
  background: #18231f;
  box-shadow: 10px 10px 0 var(--lime);
}

.prompt-composer label {
  display: block;
  margin-bottom: 12px;
  color: var(--lime);
  font-family: 'Lucida Console', monospace;
  font-size: 11px;
  letter-spacing: 1px;
}

.prompt-composer textarea {
  width: 100%;
  min-height: 142px;
  resize: vertical;
  color: #f5f5eb;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 18px;
  line-height: 1.8;
}

.prompt-composer textarea::placeholder {
  color: #829088;
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding-top: 18px;
  border-top: 1px solid #39443f;
}

.composer-footer > span {
  color: #8f9b94;
  font-size: 12px;
}

.generate-button {
  min-width: 190px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 0 22px;
  color: var(--ink);
  border: 0;
  border-radius: 8px;
  background: var(--lime);
  font-weight: 800;
  transition: transform 0.2s, background 0.2s;
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: #dbff91;
}

.generate-button:disabled {
  opacity: 0.45;
}

.generate-button b {
  font-size: 22px;
}

.loading-spinner {
  width: 17px;
  height: 17px;
  display: inline-block;
  flex: 0 0 auto;
  border: 2px solid rgba(23, 32, 28, 0.3);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner.dark {
  margin-right: 8px;
}

.generation-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  padding: 12px 14px;
  color: #dbe3dd;
  border-radius: 6px;
  background: #24312b;
  font-size: 12px;
}

.status-pulse {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  background: var(--lime);
  border-radius: 50%;
  animation: pulse 1.2s ease-in-out infinite;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 28px;
}

.example-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  color: var(--ink);
  text-align: left;
  border: 1px solid rgba(23, 32, 28, 0.25);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.42);
  transition: border 0.2s, transform 0.2s, background 0.2s;
}

.example-card:hover:not(:disabled) {
  transform: translateY(-3px);
  border-color: var(--ink);
  background: #fffef7;
}

.example-index {
  color: var(--coral);
  font-family: 'Lucida Console', monospace;
  font-size: 12px;
}

.example-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
}

.example-content strong { font-size: 15px; }
.example-content small { color: var(--muted); font-size: 11px; }
.example-arrow { font-size: 20px; }

.library-heading .game-count {
  margin-left: auto;
  color: var(--muted);
  font-size: 13px;
}

.library-state {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}

.empty-library {
  padding: 54px;
  text-align: center;
  border: 1px dashed #9ca49e;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.35);
}

.empty-code { color: var(--coral); font-size: 10px; }
.empty-library h3 { margin: 16px 0 10px; font-size: 24px; }
.empty-library p { color: var(--muted); line-height: 1.7; }

.outline-button {
  margin-top: 24px;
  padding: 11px 22px;
  color: var(--ink);
  border: 1px solid var(--ink);
  border-radius: 6px;
  background: transparent;
  font-weight: 700;
}

.outline-button:hover { background: var(--lime); }

.game-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.game-card {
  position: relative;
  min-width: 0;
  padding: 20px;
  overflow: hidden;
  border: 1px solid rgba(23, 32, 28, 0.24);
  border-radius: 12px 12px 12px 3px;
  background: #fbfaf3;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 7px 7px 0 var(--ink);
  outline: none;
}

.game-card-top,
.game-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-family: 'Lucida Console', monospace;
  font-size: 10px;
}

.delete-button {
  color: #929992;
  border: 0;
  background: transparent;
  font-size: 11px;
}

.delete-button:hover { color: #d84d36; }

.game-glyph {
  position: relative;
  height: 106px;
  margin: 20px 0;
  overflow: hidden;
  border-radius: 7px;
  background:
    linear-gradient(rgba(201, 242, 119, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(201, 242, 119, 0.08) 1px, transparent 1px),
    #1b2722;
  background-size: 18px 18px;
}

.game-glyph span {
  position: absolute;
  left: calc(50% - 18px);
  bottom: 20px;
  width: 36px;
  height: 30px;
  background: var(--lime);
  clip-path: polygon(50% 0, 100% 100%, 50% 75%, 0 100%);
}

.game-glyph i,
.game-glyph b {
  position: absolute;
  top: 22px;
  width: 18px;
  height: 18px;
  background: var(--coral);
}

.game-glyph i { left: 25%; }
.game-glyph b { right: 25%; background: #ffd665; border-radius: 50%; }

.game-card h3 {
  overflow: hidden;
  font-size: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-card > p {
  height: 44px;
  margin: 10px 0 20px;
  display: -webkit-box;
  overflow: hidden;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.game-card-footer {
  padding-top: 14px;
  color: #737d76;
  border-top: 1px solid #dedfd7;
}

.footer {
  width: min(1240px, calc(100% - 48px));
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 0 38px;
  color: #6c756f;
  border-top: 1px solid rgba(23, 32, 28, 0.2);
  font-size: 9px;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 50% { opacity: 0.3; transform: scale(0.75); } }
@keyframes hover-ship { 50% { transform: translateY(-8px); } }
@keyframes shot { from { transform: translateY(70px); opacity: 0; } 30% { opacity: 1; } to { transform: translateY(-70px); opacity: 0; } }

@media (max-width: 960px) {
  .hero { grid-template-columns: 1fr 0.75fr; gap: 24px; }
  .hero h1 { font-size: clamp(66px, 10vw, 92px); }
  .machine-screen { height: 260px; }
  .pixel-scene { height: 180px; }
  .example-grid, .game-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 720px) {
  .topbar, .hero, .creator-section, .library-section, .footer { width: min(100% - 28px, 1240px); }
  .topbar { height: 76px; }
  .brand-copy small, .user-dot, .user-area > span:not(.user-dot) { display: none; }
  .hero { grid-template-columns: 1fr; padding: 54px 0; }
  .hero h1 { letter-spacing: -4px; }
  .hero-description { font-size: 15px; }
  .arcade-wrap { width: min(90%, 380px); margin-top: 24px; }
  .creator-section, .library-section { padding: 50px 0; }
  .prompt-composer { padding: 20px; box-shadow: 6px 6px 0 var(--lime); }
  .prompt-composer textarea { min-height: 170px; font-size: 16px; }
  .composer-footer { align-items: stretch; flex-direction: column; }
  .generate-button { width: 100%; }
  .example-grid, .game-grid { grid-template-columns: 1fr; }
  .section-heading { align-items: flex-start; }
  .library-heading .game-count { display: none; }
  .empty-library { padding: 36px 20px; }
  .footer { flex-direction: column; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
}
</style>
