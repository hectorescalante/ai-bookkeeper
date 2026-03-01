<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Settings</h1>
    </div>

    <div class="space-y-6">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">Company</h2>
          <span
            class="inline-flex px-2 py-1 rounded text-xs font-semibold"
            :class="
              companyConfigured
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            "
          >
            {{ companyConfigured ? "Configured" : "Not configured" }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600">Company name</label>
            <InputText
              v-model="companyForm.name"
              class="w-full"
              placeholder="Exoticca S.L."
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Company NIF</label>
            <InputText
              v-model="companyForm.nif"
              class="w-full"
              placeholder="B12345678"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Address</label>
            <InputText
              v-model="companyForm.address"
              class="w-full"
              placeholder="Street, city, postal code"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Contact info</label>
            <InputText
              v-model="companyForm.contact_info"
              class="w-full"
              placeholder="Phone / Email / Contact person"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Commission rate (0-1)</label>
            <InputText
              v-model="companyForm.commission_rate"
              type="number"
              min="0"
              max="1"
              step="0.01"
              class="w-full"
            />
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <Button
            label="Save company"
            icon="pi pi-save"
            :loading="isSavingCompany"
            :disabled="isLoadingCompany"
            @click="saveCompany"
          />
        </div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">Agent profile</h2>
          <span
            class="inline-flex px-2 py-1 rounded text-xs font-semibold"
            :class="
              agentConfigured
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            "
          >
            {{ agentConfigured ? "Configured" : "Not configured" }}
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label class="text-xs text-gray-600">Name</label>
            <InputText
              v-model="agentForm.name"
              class="w-full"
              placeholder="Commercial agent name"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Email</label>
            <InputText
              v-model="agentForm.email"
              class="w-full"
              placeholder="name@company.com"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Phone</label>
            <InputText
              v-model="agentForm.phone"
              class="w-full"
              placeholder="+34 600 000 000"
            />
          </div>
        </div>
        <div class="mt-4 flex justify-end">
          <Button
            label="Save agent"
            icon="pi pi-save"
            :loading="isSavingAgent"
            :disabled="isLoadingAgent"
            @click="saveAgent"
          />
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">AI Extraction</h2>
          <span
            class="inline-flex px-2 py-1 rounded text-xs font-semibold"
            :class="
              hasApiKey
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            "
          >
            {{ hasApiKey ? "Gemini key configured" : "Gemini key not configured" }}
          </span>
        </div>

        <div class="space-y-3">
          <div>
            <label class="text-xs text-gray-600">Gemini API key (optional update)</label>
            <InputText
              v-model="settingsForm.gemini_api_key"
              type="password"
              class="w-full"
              placeholder="Leave empty to keep current key"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Default export path</label>
            <InputText
              v-model="settingsForm.default_export_path"
              class="w-full"
              placeholder="/Users/you/Reports"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Extraction prompt</label>
            <Textarea
              v-model="settingsForm.extraction_prompt"
              rows="7"
              class="w-full font-mono text-xs"
            />
          </div>
        </div>

        <div class="mt-4 flex flex-wrap items-center justify-end gap-2">
          <Button
            label="Reload saved"
            icon="pi pi-refresh"
            severity="secondary"
            text
            :loading="isLoadingSettings"
            :disabled="isSavingSettings"
            @click="loadSettings"
          />
          <Button
            label="Clear API key"
            icon="pi pi-times"
            severity="secondary"
            outlined
            :loading="isClearingApiKey"
            :disabled="isClearingApiKey || isSavingSettings || isTestingApiKey"
            @click="clearApiKey"
          />
          <Button
            label="Test connection"
            icon="pi pi-bolt"
            severity="secondary"
            :loading="isTestingApiKey"
            :disabled="isSavingSettings || isClearingApiKey"
            @click="handleTestConnection"
          />
          <Button
            label="Save settings"
            icon="pi pi-save"
            :loading="isSavingSettings"
            :disabled="isLoadingSettings || isTestingApiKey"
            @click="saveSettings"
          />
        </div>
      </div>

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

      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Help</h2>
        <p class="text-sm text-gray-600 mb-4">
          Export a diagnostics bundle to share with support when something fails.
        </p>
        <div class="flex flex-wrap items-center gap-2">
          <Button
            label="Export diagnostics"
            icon="pi pi-download"
            :loading="isExportingDiagnostics"
            :disabled="isExportingDiagnostics"
            @click="handleExportDiagnostics"
          />
          <Button
            label="Open file location"
            icon="pi pi-folder-open"
            severity="secondary"
            outlined
            :disabled="!latestDiagnosticsBundlePath || isExportingDiagnostics"
            @click="openDiagnosticsLocation"
          />
          <Button
            label="Share by email"
            icon="pi pi-envelope"
            severity="secondary"
            text
            :disabled="!latestDiagnosticsBundlePath || isExportingDiagnostics"
            @click="shareDiagnosticsByEmail"
          />
        </div>

        <div
          v-if="latestDiagnosticsBundlePath"
          class="mt-3 rounded border border-gray-200 bg-gray-50 p-3"
        >
          <p class="text-xs text-gray-700">
            Latest bundle:
            <span class="font-medium text-gray-800">{{ latestDiagnosticsBundleName }}</span>
          </p>
          <p class="text-xs text-gray-600 break-all mt-1">
            {{ latestDiagnosticsBundlePath }}
          </p>
          <p class="text-xs text-gray-500 mt-2">
            Your email app cannot auto-attach files from here. The “Share by email” button opens
            a draft; attach this zip file manually before sending.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { openUrl, revealItemInDir } from "@tauri-apps/plugin-opener";
import { onMounted, ref } from "vue";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import {
  configureAgent,
  configureCompany,
  configureSettings,
  connectOutlook,
  disconnectOutlook,
  exportDiagnostics,
  getAgent,
  getCompany,
  getSettings,
  testGeminiConnection,
} from "../services/api";

const toast = useToast();
const isLoadingCompany = ref(false);
const isSavingCompany = ref(false);
const isLoadingAgent = ref(false);
const isSavingAgent = ref(false);
const isLoadingSettings = ref(false);
const isSavingSettings = ref(false);
const isClearingApiKey = ref(false);
const isTestingApiKey = ref(false);
const isConnecting = ref(false);
const isDisconnecting = ref(false);
const isExportingDiagnostics = ref(false);

const companyConfigured = ref(false);
const agentConfigured = ref(false);
const hasApiKey = ref(false);
const outlookConfigured = ref(false);
const latestDiagnosticsBundleName = ref("");
const latestDiagnosticsBundlePath = ref("");
const companyForm = ref({
  name: "",
  nif: "",
  address: "",
  contact_info: "",
  commission_rate: "0.50",
});
const agentForm = ref({
  name: "",
  email: "",
  phone: "",
});
const settingsForm = ref({
  gemini_api_key: "",
  default_export_path: "",
  extraction_prompt: "",
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

const isNotConfiguredError = (error: unknown): boolean =>
  typeof error === "object" &&
  error !== null &&
  "response" in error &&
  (error as { response?: { status?: number } }).response?.status === 404;

const loadCompany = async (): Promise<void> => {
  isLoadingCompany.value = true;
  try {
    const company = await getCompany();
    companyConfigured.value = company.is_configured;
    companyForm.value = {
      name: company.name,
      nif: company.nif,
      address: company.address,
      contact_info: company.contact_info,
      commission_rate: String(company.commission_rate),
    };
  } catch (error) {
    if (isNotConfiguredError(error)) {
      companyConfigured.value = false;
      companyForm.value = {
        name: "",
        nif: "",
        address: "",
        contact_info: "",
        commission_rate: "0.50",
      };
      return;
    }
    toast.add({
      severity: "error",
      summary: "Failed to load company",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoadingCompany.value = false;
  }
};

const loadAgent = async (): Promise<void> => {
  isLoadingAgent.value = true;
  try {
    const agent = await getAgent();
    agentConfigured.value = true;
    agentForm.value = {
      name: agent.name,
      email: agent.email,
      phone: agent.phone,
    };
  } catch (error) {
    if (isNotConfiguredError(error)) {
      agentConfigured.value = false;
      agentForm.value = {
        name: "",
        email: "",
        phone: "",
      };
      return;
    }
    toast.add({
      severity: "error",
      summary: "Failed to load agent profile",
      detail: extractErrorMessage(error),
      life: 4500,
    });
  } finally {
    isLoadingAgent.value = false;
  }
};

const loadSettings = async (): Promise<void> => {
  isLoadingSettings.value = true;
  try {
    const settings = await getSettings();
    hasApiKey.value = settings.has_api_key;
    outlookConfigured.value = settings.outlook_configured;
    settingsForm.value = {
      gemini_api_key: "",
      default_export_path: settings.default_export_path,
      extraction_prompt: settings.extraction_prompt,
    };
  } catch (error) {
    if (isNotConfiguredError(error)) {
      hasApiKey.value = false;
      outlookConfigured.value = false;
      settingsForm.value = {
        gemini_api_key: "",
        default_export_path: "",
        extraction_prompt: "",
      };
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

const saveCompany = async (): Promise<void> => {
  const name = companyForm.value.name.trim();
  const nif = companyForm.value.nif.trim();
  const commissionRate = Number(companyForm.value.commission_rate);

  if (!name || !nif) {
    toast.add({
      severity: "warn",
      summary: "Missing fields",
      detail: "Company name and NIF are required.",
      life: 3500,
    });
    return;
  }

  if (
    Number.isNaN(commissionRate) ||
    commissionRate < 0 ||
    commissionRate > 1
  ) {
    toast.add({
      severity: "warn",
      summary: "Invalid commission rate",
      detail: "Commission rate must be a number between 0 and 1.",
      life: 3500,
    });
    return;
  }

  isSavingCompany.value = true;
  try {
    const response = await configureCompany({
      name,
      nif,
      address: companyForm.value.address.trim(),
      contact_info: companyForm.value.contact_info.trim(),
      commission_rate: commissionRate.toFixed(2),
    });
    companyConfigured.value = response.is_configured;
    companyForm.value = {
      name: response.name,
      nif: response.nif,
      address: response.address,
      contact_info: response.contact_info,
      commission_rate: String(response.commission_rate),
    };
    window.dispatchEvent(new Event("bookings:refresh"));
    toast.add({
      severity: "success",
      summary: "Company saved",
      detail: "Company configuration updated successfully.",
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to save company",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isSavingCompany.value = false;
  }
};

const saveAgent = async (): Promise<void> => {
  const name = agentForm.value.name.trim();
  const email = agentForm.value.email.trim();
  const phone = agentForm.value.phone.trim();

  if (!name || !email || !phone) {
    toast.add({
      severity: "warn",
      summary: "Missing fields",
      detail: "Name, email, and phone are required.",
      life: 3500,
    });
    return;
  }

  isSavingAgent.value = true;
  try {
    const response = await configureAgent({ name, email, phone });
    agentConfigured.value = true;
    agentForm.value = {
      name: response.name,
      email: response.email,
      phone: response.phone,
    };
    toast.add({
      severity: "success",
      summary: "Agent profile saved",
      detail: "Agent information updated successfully.",
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to save agent profile",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isSavingAgent.value = false;
  }
};

const handleTestConnection = async (): Promise<void> => {
  isTestingApiKey.value = true;
  try {
    const key = settingsForm.value.gemini_api_key.trim();
    const result = await testGeminiConnection({
      gemini_api_key: key.length > 0 ? key : null,
    });
    toast.add({
      severity: "success",
      summary: "Gemini connection",
      detail: result.message,
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Gemini connection failed",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isTestingApiKey.value = false;
  }
};

const saveSettings = async (): Promise<void> => {
  const prompt = settingsForm.value.extraction_prompt.trim();
  if (!prompt) {
    toast.add({
      severity: "warn",
      summary: "Prompt is required",
      detail: "Extraction prompt cannot be empty.",
      life: 3500,
    });
    return;
  }

  isSavingSettings.value = true;
  try {
    const geminiApiKey = settingsForm.value.gemini_api_key.trim();
    if (geminiApiKey.length > 0) {
      await testGeminiConnection({ gemini_api_key: geminiApiKey });
    }
    const response = await configureSettings({
      gemini_api_key: geminiApiKey.length > 0 ? geminiApiKey : null,
      default_export_path: settingsForm.value.default_export_path.trim(),
      extraction_prompt: prompt,
    });
    hasApiKey.value = response.has_api_key;
    outlookConfigured.value = response.outlook_configured;
    settingsForm.value = {
      gemini_api_key: "",
      default_export_path: response.default_export_path,
      extraction_prompt: response.extraction_prompt,
    };
    toast.add({
      severity: "success",
      summary: "Settings saved",
      detail: "AI settings updated successfully.",
      life: 3500,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to save settings",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isSavingSettings.value = false;
  }
};

const clearApiKey = async (): Promise<void> => {
  isClearingApiKey.value = true;
  try {
    const response = await configureSettings({ gemini_api_key: "" });
    hasApiKey.value = response.has_api_key;
    settingsForm.value.gemini_api_key = "";
    toast.add({
      severity: "success",
      summary: "Gemini key cleared",
      life: 3000,
    });
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to clear API key",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isClearingApiKey.value = false;
  }
};

const handleExportDiagnostics = async (): Promise<void> => {
  isExportingDiagnostics.value = true;
  try {
    const result = await exportDiagnostics();
    latestDiagnosticsBundleName.value = result.bundle_name;
    latestDiagnosticsBundlePath.value = result.bundle_path;

    toast.add({
      severity: "success",
      summary: "Diagnostics exported",
      detail: `Saved at ${result.bundle_path}`,
      life: 4500,
    });

    if (result.warnings.length > 0) {
      toast.add({
        severity: "warn",
        summary: "Diagnostics warnings",
        detail: result.warnings.join(" "),
        life: 6000,
      });
    }
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to export diagnostics",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isExportingDiagnostics.value = false;
  }
};

const openDiagnosticsLocation = async (): Promise<void> => {
  if (!latestDiagnosticsBundlePath.value) {
    return;
  }
  try {
    await revealItemInDir(latestDiagnosticsBundlePath.value);
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to open location",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  }
};

const shareDiagnosticsByEmail = async (): Promise<void> => {
  if (!latestDiagnosticsBundlePath.value) {
    return;
  }

  const subject = encodeURIComponent("AI Bookkeeper diagnostics bundle");
  const body = encodeURIComponent(
    [
      "Hi,",
      "",
      "I am sharing diagnostics for support.",
      "Please attach this file before sending:",
      latestDiagnosticsBundlePath.value,
      "",
      "Thanks.",
    ].join("\n")
  );

  try {
    await openUrl(`mailto:?subject=${subject}&body=${body}`);
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to open email app",
      detail: extractErrorMessage(error),
      life: 5000,
    });
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
  await Promise.all([loadCompany(), loadAgent(), loadSettings()]);
});
</script>
