<template>
  <router-view />
</template>

<style>
:root {
  font-family: 'Trebuchet MS', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #17201c;
  background: #f2f1e9;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  --ink: #17201c;
  --paper: #f2f1e9;
  --lime: #c9f277;
  --coral: #ff795c;
  --muted: #6e7771;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  min-width: 320px;
}

button,
textarea,
input {
  font: inherit;
}

button {
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
}

::selection {
  color: #17201c;
  background: #c9f277;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #b8bdb7;
  border-radius: 8px;
}
</style>
