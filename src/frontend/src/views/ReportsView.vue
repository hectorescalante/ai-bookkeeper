<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Reports</h1>
      <Button
        label="Export Excel"
        icon="pi pi-file-excel"
        :loading="isExporting"
        :disabled="isLoading"
        @click="handleExport"
      />
    </div>

    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label class="text-xs text-gray-600">Date from</label>
          <InputText
            v-model="filters.date_from"
            type="date"
            class="w-full"
          />
        </div>
        <div>
          <label class="text-xs text-gray-600">Date to</label>
          <InputText
            v-model="filters.date_to"
            type="date"
            class="w-full"
          />
        </div>
        <div>
          <label class="text-xs text-gray-600">Status</label>
          <select
            v-model="filters.status"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">All</option>
            <option value="PENDING">PENDING</option>
            <option value="COMPLETE">COMPLETE</option>
          </select>
        </div>
        <div class="flex items-end gap-2">
          <Button
            label="Apply"
            icon="pi pi-search"
            :loading="isLoading"
            @click="loadReport"
          />
          <Button
            label="Clear"
            severity="secondary"
            text
            @click="clearFilters"
          />
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="bg-white rounded-lg shadow p-8 text-center text-gray-500">
      <i class="pi pi-spin pi-spinner text-2xl mb-3"></i>
      <p>Loading report...</p>
    </div>

    <div
      v-else-if="report.items.length === 0"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <i class="pi pi-chart-bar text-4xl mb-4"></i>
      <p>No report rows for the selected filters.</p>
    </div>

    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-4 border-b grid grid-cols-1 md:grid-cols-5 gap-3 text-sm">
        <div>
          <p class="text-gray-500">Bookings</p>
          <p class="font-semibold text-gray-800">{{ report.totals.booking_count }}</p>
        </div>
        <div>
          <p class="text-gray-500">Revenue</p>
          <p class="font-semibold text-gray-800">
            {{ formatMoney(report.totals.total_revenue) }}
          </p>
        </div>
        <div>
          <p class="text-gray-500">Costs</p>
          <p class="font-semibold text-gray-800">
            {{ formatMoney(report.totals.total_costs) }}
          </p>
        </div>
        <div>
          <p class="text-gray-500">Margin</p>
          <p class="font-semibold text-gray-800">
            {{ formatMoney(report.totals.total_margin) }}
          </p>
        </div>
        <div>
          <p class="text-gray-500">Commission</p>
          <p class="font-semibold text-gray-800">
            {{ formatMoney(report.totals.total_commission) }}
          </p>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-600">
            <tr>
              <th class="px-4 py-3">Booking</th>
              <th class="px-4 py-3">Client</th>
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3">Created</th>
              <th class="px-4 py-3">Revenue</th>
              <th class="px-4 py-3">Costs</th>
              <th class="px-4 py-3">Margin</th>
              <th class="px-4 py-3">Commission</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in report.items"
              :key="`${item.booking_id}-${item.created_at}`"
              class="border-t hover:bg-gray-50"
            >
              <td class="px-4 py-3 font-medium text-gray-800">{{ item.booking_id }}</td>
              <td class="px-4 py-3 text-gray-700">{{ item.client_name ?? "—" }}</td>
              <td class="px-4 py-3 text-gray-700">{{ item.status }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatDate(item.created_at) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(item.total_revenue) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(item.total_costs) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(item.margin) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ formatMoney(item.commission) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import { useToast } from "primevue/usetoast";
import {
  type BookingStatus,
  type CommissionReportRequest,
  exportCommissionReport,
  generateCommissionReport,
  type CommissionReportResponse,
  type FileDownloadResponse,
} from "../services/api";

const toast = useToast();

const isLoading = ref(false);
const isExporting = ref(false);
const filters = ref<{
  date_from: string;
  date_to: string;
  status: "" | BookingStatus;
}>({
  date_from: "",
  date_to: "",
  status: "",
});
const report = ref<CommissionReportResponse>({
  items: [],
  totals: {
    booking_count: 0,
    total_revenue: "0.00",
    total_costs: "0.00",
    total_margin: "0.00",
    total_commission: "0.00",
  },
});

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

const formatMoney = (value: string | number): string => {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "€0.00";
  }
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "EUR",
  }).format(numeric);
};

const formatDate = (value: string): string =>
  new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });

const normalizeFilters = (): CommissionReportRequest => ({
  date_from: filters.value.date_from || null,
  date_to: filters.value.date_to || null,
  status: filters.value.status === "" ? null : filters.value.status,
});

const downloadFile = (file: FileDownloadResponse): void => {
  const url = URL.createObjectURL(file.blob);
  const link = window.document.createElement("a");
  link.href = url;
  link.download = file.file_name;
  window.document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const loadReport = async (): Promise<void> => {
  isLoading.value = true;
  try {
    report.value = await generateCommissionReport(normalizeFilters());
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Could not load report",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoading.value = false;
  }
};

const handleExport = async (): Promise<void> => {
  isExporting.value = true;
  try {
    const file = await exportCommissionReport(normalizeFilters());
    downloadFile(file);
    toast.add({
      severity: "success",
      summary: "Export ready",
      detail: `Downloaded ${file.file_name}`,
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Export failed",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isExporting.value = false;
  }
};

const clearFilters = (): void => {
  filters.value = {
    date_from: "",
    date_to: "",
    status: "",
  };
  void loadReport();
};

onMounted(async () => {
  await loadReport();
});
</script>
