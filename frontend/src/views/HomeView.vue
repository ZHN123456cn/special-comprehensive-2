<template>
  <el-container class="home">
    <el-header class="header">
      <div class="logo">专综2 项目</div>
      <div class="user-area">
        <span class="welcome">你好，{{ user?.username || '用户' }}</span>
        <el-button type="danger" plain size="small" @click="logout">退出登录</el-button>
      </div>
    </el-header>

    <el-main class="main">
      <el-card>
        <template #header>登录成功</template>
        <p>这是登录后的首页占位页面，后续业务功能在这里继续开发。</p>
        <el-descriptions :column="1" border style="margin-top: 16px">
          <el-descriptions-item label="用户ID">{{ user?.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ user?.created_at }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.home {
  height: 100%;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome {
  color: #606266;
}

.main {
  background: #f5f7fa;
  display: flex;
  justify-content: center;
}

.main .el-card {
  width: 100%;
  max-width: 720px;
  margin-top: 40px;
}
</style>
