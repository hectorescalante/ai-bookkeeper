<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Settings</h1>
    </div>

    <div class="space-y-6">
      <!-- Company Settings -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Company</h2>
        <p class="text-gray-500">Configure your company NIF and details.</p>
      </div>

      <!-- Agent Settings -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Agent</h2>
        <p class="text-gray-500">Configure agent profile information.</p>
      </div>

      <!-- Integrations -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Integrations</h2>
        <p class="text-gray-500">
          Configure API keys and email connections.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>
