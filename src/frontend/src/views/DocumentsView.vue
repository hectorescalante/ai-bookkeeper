<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Documents</h1>
      <Button label="Fetch Emails" icon="pi pi-envelope" />
    </div>

    <div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">
      <i class="pi pi-inbox text-4xl mb-4"></i>
      <p>No documents yet. Click "Fetch Emails" to get started.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from "primevue/button";
</script>
