-- 数据库初始化脚本
-- 首次使用时，用 root 或有权限的账号执行：
--   mysql -u root -p < init.sql
-- 表结构由 FastAPI 启动时自动创建，这里只需要建库。

CREATE DATABASE IF NOT EXISTS zhuanzong2
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
