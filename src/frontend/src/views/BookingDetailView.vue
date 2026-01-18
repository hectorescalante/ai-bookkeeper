<template>
  <div class="p-6">
    <div class="flex items-center gap-4 mb-6">
      <Button
        icon="pi pi-arrow-left"
        text
        rounded
        @click="$router.push('/bookings')"
      />
      <h1 class="text-2xl font-bold text-gray-800">
        Booking {{ $route.params.id }}
      </h1>
    </div>

    <div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">
      <p>Booking detail view - coming soon</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from "primevue/button";
</script>
