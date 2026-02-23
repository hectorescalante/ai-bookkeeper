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
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-800">Outlook mailbox</p>
              <p class="text-xs text-gray-500">
                Required for “Fetch Emails” in Documents.
              </p>
            </div>
            <span
              class="inline-flex px-2 py-1 rounded text-xs font-semibold"
              :class="
                outlookConfigured
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              "
            >
              {{ outlookConfigured ? "Connected" : "Not connected" }}
            </span>
          </div>

          <div class="flex items-center gap-2">
            <Button
              label="Connect Outlook"
              icon="pi pi-link"
              :loading="isConnecting"
              :disabled="isConnecting || isDisconnecting"
              @click="startOutlookConnect"
            />
            <Button
              label="Disconnect"
              icon="pi pi-times"
              severity="secondary"
              outlined
              :loading="isDisconnecting"
              :disabled="!outlookConfigured || isConnecting || isDisconnecting"
              @click="handleOutlookDisconnect"
            />
            <Button
              label="Refresh status"
              icon="pi pi-refresh"
              severity="secondary"
              text
              :loading="isLoadingSettings"
              :disabled="isConnecting || isDisconnecting"
              @click="loadSettings"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "primevue/button";
import { useToast } from "primevue/usetoast";
import {
  connectOutlook,
  disconnectOutlook,
  getSettings,
} from "../services/api";

const toast = useToast();

const isLoadingSettings = ref(false);
const isConnecting = ref(false);
const isDisconnecting = ref(false);
const outlookConfigured = ref(false);

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

const isNotConfiguredError = (error: unknown): boolean =>
  typeof error === "object" &&
  error !== null &&
  "response" in error &&
  (error as { response?: { status?: number } }).response?.status === 404;

const loadSettings = async (): Promise<void> => {
  isLoadingSettings.value = true;
  try {
    const settings = await getSettings();
    outlookConfigured.value = settings.outlook_configured;
  } catch (error) {
    if (isNotConfiguredError(error)) {
      outlookConfigured.value = false;
      return;
    }
    toast.add({
      severity: "error",
      summary: "Failed to load settings",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoadingSettings.value = false;
  }
};

const startOutlookConnect = async (): Promise<void> => {
  isConnecting.value = true;
  try {
    const result = await connectOutlook();
    const popup = window.open(
      result.authorization_url,
      "_blank",
      "noopener,noreferrer"
    );
    if (popup === null) {
      toast.add({
        severity: "warn",
        summary: "Popup blocked",
        detail: "Allow popups, then click Connect Outlook again.",
        life: 4500,
      });
      return;
    }

    toast.add({
      severity: "info",
      summary: "Browser opened",
      detail:
        "Complete Outlook sign-in in browser. Status will update automatically.",
      life: 5000,
    });

    for (let attempt = 0; attempt < 10; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await loadSettings();
      if (outlookConfigured.value) {
        toast.add({
          severity: "success",
          summary: "Outlook connected",
          detail: "Mailbox integration is ready.",
          life: 3500,
        });
        break;
      }
    }
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to start Outlook connect",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isConnecting.value = false;
  }
};

const handleOutlookDisconnect = async (): Promise<void> => {
  isDisconnecting.value = true;
  try {
    const response = await disconnectOutlook();
    outlookConfigured.value = response.outlook_configured;
    toast.add({
      severity: "success",
      summary: "Outlook disconnected",
      detail: "You can reconnect anytime.",
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to disconnect Outlook",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isDisconnecting.value = false;
  }
};

onMounted(async () => {
  await loadSettings();
});
</script>
