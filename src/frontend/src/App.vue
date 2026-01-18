<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <aside class="w-64 bg-white shadow-md flex flex-col">
      <div class="p-4 border-b">
        <h1 class="text-xl font-bold text-gray-800">AI Bookkeeper</h1>
      </div>
      <nav class="flex-1 p-4">
        <ul class="space-y-2">
          <li>
            <router-link
              to="/"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="[
                $route.path === '/'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100',
              ]"
            >
              <i class="pi pi-file text-lg"></i>
              <span>Documents</span>
            </router-link>
          </li>
          <li>
            <router-link
              to="/bookings"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="[
                $route.path.startsWith('/bookings')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100',
              ]"
            >
              <i class="pi pi-box text-lg"></i>
              <span>Bookings</span>
            </router-link>
          </li>
          <li>
            <router-link
              to="/reports"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="[
                $route.path === '/reports'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100',
              ]"
            >
              <i class="pi pi-chart-bar text-lg"></i>
              <span>Reports</span>
            </router-link>
          </li>
          <li>
            <router-link
              to="/settings"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="[
                $route.path === '/settings'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100',
              ]"
            >
              <i class="pi pi-cog text-lg"></i>
              <span>Settings</span>
            </router-link>
          </li>
        </ul>
      </nav>
      <div class="p-4 border-t text-xs text-gray-500">v0.1.0</div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>

    <!-- Toast notifications -->
    <Toast />
  </div>
</template>

<script setup lang="ts">
import Toast from "primevue/toast";
</script>
