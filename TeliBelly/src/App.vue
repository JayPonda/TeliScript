<template>
  <div id="app-container">
    <nav>
      <router-link to="/">Dashboard</router-link>
      <router-link to="/kanban">Kanban</router-link>
    </nav>
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </div>
</template>

<script setup>
</script>

<style>
:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --secondary: #64748b;
  --success: #10b981;
  --background: #f8fafc;
  --card: #ffffff;
  --text: #1e293b;
  --border: #e2e8f0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: var(--background);
  color: var(--text);
  line-height: 1.6;
}

nav {
  background-color: var(--primary);
  padding: 1rem;
  display: flex;
  gap: 1rem;
}

nav a {
  color: white;
  text-decoration: none;
  font-weight: bold;
}

nav a.router-link-exact-active {
  text-decoration: underline;
}
</style>
