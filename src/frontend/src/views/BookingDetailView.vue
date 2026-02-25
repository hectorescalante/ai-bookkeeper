<template>
  <div class="p-6">
    <div class="flex items-center justify-between gap-4 mb-6">
      <div class="flex items-center gap-4">
        <Button
          icon="pi pi-arrow-left"
          text
          rounded
          @click="router.push('/bookings')"
        />
        <h1 class="text-2xl font-bold text-gray-800">
          Booking {{ bookingId }}
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <Button
          label="Export"
          icon="pi pi-file-excel"
          severity="secondary"
          :loading="isExporting"
          :disabled="!booking"
          @click="handleExport"
        />
        <Button
          v-if="booking?.status === 'PENDING'"
          label="Mark Complete"
          icon="pi pi-check"
          :loading="isChangingStatus"
          :disabled="!booking"
          @click="handleMarkComplete"
        />
        <Button
          v-else-if="booking?.status === 'COMPLETE'"
          label="Revert to Pending"
          icon="pi pi-undo"
          severity="secondary"
          :loading="isChangingStatus"
          :disabled="!booking"
          @click="handleRevertToPending"
        />
      </div>
    </div>
    <div v-if="isLoading" class="bg-white rounded-lg shadow p-8 text-center text-gray-500">
      <i class="pi pi-spin pi-spinner text-2xl mb-3"></i>
      <p>Loading booking detail...</p>
    </div>

    <div
      v-else-if="!booking"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <p>Booking not found.</p>
    </div>

    <div v-else class="space-y-4">
      <div class="bg-white rounded-lg shadow p-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div>
          <p class="text-gray-500">Status</p>
          <p class="font-semibold text-gray-800">{{ booking.status }}</p>
        </div>
        <div>
          <p class="text-gray-500">Created</p>
          <p class="font-semibold text-gray-800">{{ formatDate(booking.created_at) }}</p>
        </div>
        <div>
          <p class="text-gray-500">Client</p>
          <p class="font-semibold text-gray-800">{{ booking.client_name ?? "—" }}</p>
        </div>
        <div>
          <p class="text-gray-500">Client NIF</p>
          <p class="font-semibold text-gray-800">{{ booking.client_nif ?? "—" }}</p>
        </div>
        <div>
          <p class="text-gray-500">Revenue</p>
          <p class="font-semibold text-gray-800">{{ formatMoney(booking.total_revenue) }}</p>
        </div>
        <div>
          <p class="text-gray-500">Costs</p>
          <p class="font-semibold text-gray-800">{{ formatMoney(booking.total_costs) }}</p>
        </div>
        <div>
          <p class="text-gray-500">Margin</p>
          <p class="font-semibold text-gray-800">{{ formatMoney(booking.margin) }}</p>
        </div>
        <div>
          <p class="text-gray-500">Commission</p>
          <p class="font-semibold text-gray-800">{{ formatMoney(booking.commission) }}</p>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-semibold text-gray-800 mb-3">Shipping details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600">Vessel</label>
            <InputText
              v-model="editForm.vessel"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Containers (comma separated)</label>
            <InputText
              v-model="editForm.containers_text"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">POL code</label>
            <InputText
              v-model="editForm.pol_code"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">POL name</label>
            <InputText
              v-model="editForm.pol_name"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">POD code</label>
            <InputText
              v-model="editForm.pod_code"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">POD name</label>
            <InputText
              v-model="editForm.pod_name"
              class="w-full"
            />
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <Button
            label="Save Changes"
            icon="pi pi-save"
            :loading="isSaving"
            @click="handleSave"
          />
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-4 text-sm text-gray-700">
        <p>Revenue charges: <span class="font-semibold">{{ booking.revenue_charge_count }}</span></p>
        <p>Cost charges: <span class="font-semibold">{{ booking.cost_charge_count }}</span></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import { useToast } from "primevue/usetoast";
import { useRoute, useRouter } from "vue-router";
import {
  exportBooking,
  getBookingDetail,
  markBookingComplete,
  revertBookingToPending,
  updateBooking,
  type BookingDetailResponse,
  type FileDownloadResponse,
  type UpdateBookingRequest,
} from "../services/api";

const route = useRoute();
const router = useRouter();
const toast = useToast();

const bookingId = String(route.params.id || "");

const isLoading = ref(false);
const isSaving = ref(false);
const isChangingStatus = ref(false);
const isExporting = ref(false);
const booking = ref<BookingDetailResponse | null>(null);
const editForm = ref({
  vessel: "",
  containers_text: "",
  pol_code: "",
  pol_name: "",
  pod_code: "",
  pod_name: "",
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
  new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const syncEditForm = (item: BookingDetailResponse): void => {
  editForm.value = {
    vessel: item.vessel ?? "",
    containers_text: item.containers.join(", "),
    pol_code: item.pol_code ?? "",
    pol_name: item.pol_name ?? "",
    pod_code: item.pod_code ?? "",
    pod_name: item.pod_name ?? "",
  };
};

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

const loadBooking = async (): Promise<void> => {
  if (!bookingId) {
    return;
  }
  isLoading.value = true;
  try {
    const response = await getBookingDetail(bookingId);
    booking.value = response;
    syncEditForm(response);
  } catch (error) {
    booking.value = null;
    toast.add({
      severity: "error",
      summary: "Could not load booking",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoading.value = false;
  }
};

const buildUpdatePayload = (): UpdateBookingRequest => {
  const containers = editForm.value.containers_text
    .split(",")
    .map((container) => container.trim())
    .filter((container) => container.length > 0);
  const normalizeText = (value: string): string => value.trim();

  return {
    vessel: normalizeText(editForm.value.vessel),
    containers,
    pol_code: normalizeText(editForm.value.pol_code),
    pol_name: normalizeText(editForm.value.pol_name),
    pod_code: normalizeText(editForm.value.pod_code),
    pod_name: normalizeText(editForm.value.pod_name),
  };
};

const handleSave = async (): Promise<void> => {
  if (!booking.value) {
    return;
  }
  isSaving.value = true;
  try {
    const response = await updateBooking(bookingId, buildUpdatePayload());
    booking.value = response;
    syncEditForm(response);
    window.dispatchEvent(new Event("bookings:refresh"));
    toast.add({
      severity: "success",
      summary: "Booking updated",
      detail: "Shipping details saved successfully.",
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Update failed",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isSaving.value = false;
  }
};

const handleMarkComplete = async (): Promise<void> => {
  isChangingStatus.value = true;
  try {
    const response = await markBookingComplete(bookingId);
    booking.value = response;
    syncEditForm(response);
    window.dispatchEvent(new Event("bookings:refresh"));
    toast.add({
      severity: "success",
      summary: "Booking completed",
      life: 3000,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Action failed",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isChangingStatus.value = false;
  }
};

const handleRevertToPending = async (): Promise<void> => {
  isChangingStatus.value = true;
  try {
    const response = await revertBookingToPending(bookingId);
    booking.value = response;
    syncEditForm(response);
    window.dispatchEvent(new Event("bookings:refresh"));
    toast.add({
      severity: "success",
      summary: "Booking reverted to pending",
      life: 3000,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Action failed",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isChangingStatus.value = false;
  }
};

const handleExport = async (): Promise<void> => {
  isExporting.value = true;
  try {
    const file = await exportBooking(bookingId);
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

onMounted(async () => {
  await loadBooking();
});
</script>
