<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Bookings</h1>
      <Button
        label="Refresh"
        icon="pi pi-refresh"
        :loading="isLoading"
        @click="loadBookings"
      />
    </div>

    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-3">
        <div class="xl:col-span-2">
          <label class="block text-xs text-gray-600 mb-1">Client</label>
          <input
            v-model="filters.client"
            type="text"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            placeholder="Filter by client name"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Status</label>
          <select
            v-model="filters.status"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All</option>
            <option value="PENDING">PENDING</option>
            <option value="COMPLETE">COMPLETE</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Date from</label>
          <input
            v-model="filters.date_from"
            type="date"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Date to</label>
          <input
            v-model="filters.date_to"
            type="date"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Sort by</label>
          <select
            v-model="filters.sort_by"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="created_at">created_at</option>
            <option value="margin">margin</option>
            <option value="commission">commission</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Order</label>
          <select
            v-model="filters.descending"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option :value="true">Descending</option>
            <option :value="false">Ascending</option>
          </select>
        </div>
      </div>
      <div class="flex items-center justify-end gap-2 mt-3">
        <Button
          label="Reset"
          text
          severity="secondary"
          :disabled="isLoading"
          @click="resetFilters"
        />
        <Button
          label="Apply filters"
          icon="pi pi-filter"
          :loading="isLoading"
          @click="loadBookings"
        />
      </div>
    </div>

    <div
      v-if="isLoading"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <i class="pi pi-spin pi-spinner text-2xl mb-3"></i>
      <p>Loading bookings...</p>
    </div>

    <div
      v-else-if="bookings.length === 0"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <i class="pi pi-box text-4xl mb-4"></i>
      <p>No bookings yet. Process some invoices to create bookings.</p>
    </div>

    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-4 border-b text-sm text-gray-600">
        {{ bookings.length }} booking(s)
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-600">
            <tr>
              <th class="px-4 py-3">Booking</th>
              <th class="px-4 py-3">Client</th>
              <th class="px-4 py-3">POL</th>
              <th class="px-4 py-3">POD</th>
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3">Revenue</th>
              <th class="px-4 py-3">Costs</th>
              <th class="px-4 py-3">Margin</th>
              <th class="px-4 py-3">Commission</th>
              <th class="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="booking in bookings"
              :key="booking.id"
              class="border-t hover:bg-gray-50 cursor-pointer"
              @click="$router.push(`/bookings/${booking.id}`)"
            >
              <td class="px-4 py-3 font-medium text-gray-800">{{ booking.id }}</td>
              <td class="px-4 py-3 text-gray-700">
                {{ booking.client_name ?? "—" }}
              </td>
              <td class="px-4 py-3 text-gray-700">{{ booking.pol_code ?? "—" }}</td>
              <td class="px-4 py-3 text-gray-700">{{ booking.pod_code ?? "—" }}</td>
              <td class="px-4 py-3">
                <span
                  class="inline-flex px-2 py-1 rounded text-xs font-semibold"
                  :class="statusClass(booking.status)"
                >
                  {{ booking.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(booking.total_revenue) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(booking.total_costs) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(booking.margin) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(booking.commission) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatDate(booking.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import Button from "primevue/button";
import { useToast } from "primevue/usetoast";
import {
  listBookings,
  type BookingListItem,
  type BookingStatus,
} from "../services/api";

const toast = useToast();
const bookings = ref<BookingListItem[]>([]);
const isLoading = ref(false);
const filters = ref<{
  client: string;
  status: "" | BookingStatus;
  date_from: string;
  date_to: string;
  sort_by: "created_at" | "margin" | "commission";
  descending: boolean;
}>({
  client: "",
  status: "",
  date_from: "",
  date_to: "",
  sort_by: "created_at",
  descending: true,
});

const formatDate = (value: string): string =>
  new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const formatMoney = (value: number | string): string => {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "€0.00";
  }
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "EUR",
  }).format(numeric);
};

const statusClass = (status: string): string => {
  switch (status) {
    case "PENDING":
      return "bg-gray-100 text-gray-700";
    case "COMPLETE":
      return "bg-green-100 text-green-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
};

const resetFilters = (): void => {
  filters.value = {
    client: "",
    status: "",
    date_from: "",
    date_to: "",
    sort_by: "created_at",
    descending: true,
  };
  void loadBookings();
};

const extractErrorMessage = (error: unknown): string => {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof (error as { response?: { data?: { detail?: string } } }).response
      ?.data?.detail === "string"
  ) {
    return (error as { response: { data: { detail: string } } }).response.data
      .detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
};

const loadBookings = async (): Promise<void> => {
  isLoading.value = true;
  try {
    const response = await listBookings({
      client: filters.value.client.trim() || undefined,
      status: filters.value.status || undefined,
      date_from: filters.value.date_from || undefined,
      date_to: filters.value.date_to || undefined,
      sort_by: filters.value.sort_by,
      descending: filters.value.descending,
    });
    bookings.value = response.bookings;
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to load bookings",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoading.value = false;
  }
};

const handleBookingsRefresh = (): void => {
  void loadBookings();
};

onMounted(async () => {
  window.addEventListener("bookings:refresh", handleBookingsRefresh);
  await loadBookings();
});

onBeforeUnmount(() => {
  window.removeEventListener("bookings:refresh", handleBookingsRefresh);
});
</script>
