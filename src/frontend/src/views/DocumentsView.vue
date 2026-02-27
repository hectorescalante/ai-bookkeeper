<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Documents</h1>
      <div class="flex items-center gap-2">
        <Button
          label="Fetch Emails"
          icon="pi pi-envelope"
          :loading="isFetchingEmails"
          :disabled="isFetchingEmails || isProcessingCurrentDocument"
          @click="handleFetchEmails"
        />
        <Button
          :label="batchActionLabel"
          icon="pi pi-play"
          :disabled="selectedDocumentIds.length === 0 || isProcessingCurrentDocument"
          :loading="isProcessingCurrentDocument && queueMode === 'batch'"
          @click="startBatchProcessing"
        />
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <div class="flex flex-wrap gap-2">
        <Button
          v-for="tab in tabs"
          :key="tab.value"
          :label="tab.label"
          :severity="activeTab === tab.value ? undefined : 'secondary'"
          :text="activeTab !== tab.value"
          @click="setActiveTab(tab.value)"
        />
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-6 gap-3">
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
          <label class="text-xs text-gray-600">Document type</label>
          <select
            v-model="filters.document_type"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">All</option>
            <option value="CLIENT_INVOICE">CLIENT_INVOICE</option>
            <option value="PROVIDER_INVOICE">PROVIDER_INVOICE</option>
            <option value="OTHER">OTHER</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-600">Party</label>
          <InputText
            v-model="filters.party"
            class="w-full"
            placeholder="Client or provider"
          />
        </div>
        <div>
          <label class="text-xs text-gray-600">Booking</label>
          <InputText
            v-model="filters.booking"
            class="w-full"
            placeholder="BL reference"
          />
        </div>
        <div class="flex items-end gap-2">
          <Button
            label="Apply"
            icon="pi pi-search"
            :loading="isLoadingDocuments"
            @click="loadDocuments"
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

    <div
      v-if="isLoadingDocuments"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <i class="pi pi-spin pi-spinner text-2xl mb-3"></i>
      <p>Loading documents...</p>
    </div>

    <div
      v-else-if="documents.length === 0"
      class="bg-white rounded-lg shadow p-8 text-center text-gray-500"
    >
      <i class="pi pi-inbox text-4xl mb-4"></i>
      <p>{{ emptyStateMessage }}</p>
    </div>

    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-4 border-b flex items-center justify-between">
        <div class="text-sm text-gray-600">
          {{ documents.length }} document(s) in {{ activeTabLabel }}
        </div>
        <label class="text-sm text-gray-700 flex items-center gap-2">
          <input
            type="checkbox"
            :checked="allProcessableSelected"
            :disabled="processableDocumentIds.length === 0"
            @change="toggleSelectAllProcessable"
          />
          Select all actionable
        </label>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-600">
            <tr>
              <th class="px-4 py-3 w-10"></th>
              <th class="px-4 py-3">Filename</th>
              <th
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3"
              >
                Email
              </th>
              <th
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3"
              >
                PDFs
              </th>
              <th
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3"
              >
                Created
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Type
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Invoice
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Party
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Booking
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Total
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Processed
              </th>
              <th
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3"
              >
                Review history
              </th>
              <th
                v-if="activeTab === 'ERROR'"
                class="px-4 py-3"
              >
                Error
              </th>
              <th
                v-if="activeTab === 'ERROR'"
                class="px-4 py-3"
              >
                Created
              </th>
              <th class="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="document in documents"
              :key="document.id"
              class="border-t hover:bg-gray-50"
            >
              <td class="px-4 py-3 align-top">
                <input
                  type="checkbox"
                  :checked="selectedDocumentIds.includes(document.id)"
                  :disabled="
                    !isActionableForTab(document, activeTab) ||
                    isProcessingCurrentDocument
                  "
                  @change="toggleDocumentSelection(document.id)"
                />
              </td>
              <td class="px-4 py-3">
                <div class="font-medium text-gray-800">{{ document.filename }}</div>
                <div
                  v-if="document.file_url"
                  class="mt-1"
                >
                  <a
                    class="text-xs text-blue-600 hover:underline"
                    :href="getDocumentFileUrl(document.file_url)"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View PDF
                  </a>
                </div>
              </td>
              <td
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3 text-gray-700"
              >
                <div class="text-xs text-gray-600">{{ document.email_sender ?? "—" }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ document.email_subject ?? "—" }}</div>
              </td>
              <td
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3 text-gray-700"
              >
                {{ document.pdf_count_in_email ?? "—" }}
              </td>
              <td
                v-if="activeTab === 'PENDING'"
                class="px-4 py-3 text-gray-700"
              >
                {{ formatDate(document.created_at) }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{ document.document_type ?? "—" }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{ document.invoice_number ?? "—" }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{ document.party_name ?? "—" }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{
                  document.booking_references.length > 0
                    ? document.booking_references.join(", ")
                    : "—"
                }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{ formatMoney(document.total_amount) }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                {{ document.processed_at ? formatDate(document.processed_at) : "—" }}
              </td>
              <td
                v-if="activeTab === 'PROCESSED'"
                class="px-4 py-3 text-gray-700"
              >
                <div
                  v-if="document.manually_edited_fields.length > 0"
                  class="text-xs text-amber-700"
                >
                  {{ document.manually_edited_fields.join(", ") }}
                </div>
                <span v-else>—</span>
              </td>
              <td
                v-if="activeTab === 'ERROR'"
                class="px-4 py-3 text-gray-700"
              >
                <div class="text-xs text-red-700">{{ document.error_message ?? "Unknown error" }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  Retryable: {{ document.error_retryable ? "yes" : "no" }}
                </div>
              </td>
              <td
                v-if="activeTab === 'ERROR'"
                class="px-4 py-3 text-gray-700"
              >
                {{ formatDate(document.created_at) }}
              </td>
              <td class="px-4 py-3">
                <Button
                  v-if="activeTab === 'PENDING'"
                  size="small"
                  label="Process"
                  icon="pi pi-play"
                  :disabled="isProcessingCurrentDocument"
                  :loading="
                    isProcessingCurrentDocument &&
                    currentQueueDocumentId === document.id
                  "
                  @click="startSingleProcessing(document.id)"
                />
                <Button
                  v-else-if="activeTab === 'PROCESSED'"
                  size="small"
                  label="Reprocess"
                  icon="pi pi-refresh"
                  severity="secondary"
                  :disabled="isProcessingCurrentDocument"
                  :loading="
                    isProcessingCurrentDocument &&
                    currentQueueDocumentId === document.id
                  "
                  @click="startSingleProcessing(document.id)"
                />
                <div
                  v-else-if="activeTab === 'ERROR'"
                  class="flex gap-2"
                >
                  <Button
                    size="small"
                    label="Retry"
                    icon="pi pi-refresh"
                    severity="danger"
                    :disabled="isProcessingCurrentDocument"
                    :loading="
                      isProcessingCurrentDocument &&
                      currentQueueDocumentId === document.id
                    "
                    @click="startSingleProcessing(document.id)"
                  />
                  <Button
                    size="small"
                    label="Edit manually"
                    severity="secondary"
                    :disabled="isProcessingCurrentDocument"
                    @click="startManualReview(document.id)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Dialog
      v-model:visible="showReviewDialog"
      modal
      :closable="false"
      :style="{ width: 'min(1100px, 96vw)' }"
      header="Review Extracted Invoice"
    >
      <div v-if="reviewForm" class="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        <div
          v-if="queueMode === 'batch'"
          class="text-xs text-gray-600 bg-gray-50 rounded px-3 py-2"
        >
          Processing {{ queueIndex + 1 }} of {{ processingQueue.length }}
        </div>

        <div v-if="reviewForm.warnings.length > 0" class="rounded bg-yellow-50 p-3">
          <p class="font-semibold text-yellow-800 mb-1">Warnings</p>
          <ul class="list-disc ml-5 text-sm text-yellow-800">
            <li v-for="warning in reviewForm.warnings" :key="warning">
              {{ warning }}
            </li>
          </ul>
        </div>

        <div v-if="reviewForm.errors.length > 0" class="rounded bg-red-50 p-3">
          <p class="font-semibold text-red-800 mb-1">Validation errors</p>
          <ul class="list-disc ml-5 text-sm text-red-800">
            <li v-for="error in reviewForm.errors" :key="error">
              {{ error }}
            </li>
          </ul>
        </div>

        <div
          v-if="reviewUncertaintyRows(reviewForm).length > 0"
          class="rounded bg-amber-50 p-3"
        >
          <p class="font-semibold text-amber-800 mb-1">
            Uncertain fields (AI marked as not found or ambiguous)
          </p>
          <ul class="list-disc ml-5 text-sm text-amber-800">
            <li
              v-for="item in reviewUncertaintyRows(reviewForm)"
              :key="`${item.field}-${item.status}`"
            >
              {{ item.label }}: {{ item.status === "not_found" ? "not found" : "ambiguous" }}
            </li>
          </ul>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600">Document type</label>
            <select
              v-model="reviewForm.document_type"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
              @change="markEdited('document_type')"
            >
              <option
                v-for="option in documentTypeOptions"
                :key="option"
                :value="option"
              >
                {{ option }}
              </option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-600">Overall confidence</label>
            <InputText
              class="w-full"
              :model-value="reviewForm.overall_confidence"
              disabled
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Invoice number</label>
            <InputText
              v-model="reviewForm.invoice_number"
              class="w-full"
              @update:model-value="markEdited('invoice_number')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Invoice date</label>
            <InputText
              v-model="reviewForm.invoice_date"
              class="w-full"
              placeholder="YYYY-MM-DD"
              @update:model-value="markEdited('invoice_date')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Issuer name</label>
            <InputText
              v-model="reviewForm.issuer_name"
              class="w-full"
              @update:model-value="markEdited('issuer_name')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Issuer NIF</label>
            <InputText
              v-model="reviewForm.issuer_nif"
              class="w-full"
              @update:model-value="markEdited('issuer_nif')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Recipient name</label>
            <InputText
              v-model="reviewForm.recipient_name"
              class="w-full"
              @update:model-value="markEdited('recipient_name')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Recipient NIF</label>
            <InputText
              v-model="reviewForm.recipient_nif"
              class="w-full"
              @update:model-value="markEdited('recipient_nif')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-600">Provider type</label>
            <select
              v-model="reviewForm.provider_type"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
              @change="markEdited('provider_type')"
            >
              <option value="">—</option>
              <option
                v-for="option in providerTypeOptions"
                :key="option"
                :value="option"
              >
                {{ option }}
              </option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-600">Currency</label>
            <InputText
              class="w-full"
              :model-value="`${reviewForm.currency_detected} (${reviewForm.currency_valid ? 'valid' : 'invalid'})`"
              disabled
            />
          </div>
        </div>

        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Shipping details</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-600">POL code</label>
              <InputText
                v-model="reviewForm.shipping_pol_code"
                class="w-full"
                @update:model-value="markEdited('shipping_details.pol.code')"
              />
            </div>
            <div>
              <label class="text-xs text-gray-600">POL name</label>
              <InputText
                v-model="reviewForm.shipping_pol_name"
                class="w-full"
                @update:model-value="markEdited('shipping_details.pol.name')"
              />
            </div>
            <div>
              <label class="text-xs text-gray-600">POD code</label>
              <InputText
                v-model="reviewForm.shipping_pod_code"
                class="w-full"
                @update:model-value="markEdited('shipping_details.pod.code')"
              />
            </div>
            <div>
              <label class="text-xs text-gray-600">POD name</label>
              <InputText
                v-model="reviewForm.shipping_pod_name"
                class="w-full"
                @update:model-value="markEdited('shipping_details.pod.name')"
              />
            </div>
            <div>
              <label class="text-xs text-gray-600">Vessel</label>
              <InputText
                v-model="reviewForm.shipping_vessel"
                class="w-full"
                @update:model-value="markEdited('shipping_details.vessel')"
              />
            </div>
            <div>
              <label class="text-xs text-gray-600">Containers (comma separated)</label>
              <InputText
                v-model="reviewForm.shipping_containers"
                class="w-full"
                @update:model-value="markEdited('shipping_details.containers')"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Charges</h3>
          <div class="overflow-x-auto border rounded">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 text-left text-gray-600">
                <tr>
                  <th class="px-3 py-2">BL ref</th>
                  <th class="px-3 py-2">Description</th>
                  <th class="px-3 py-2">Category</th>
                  <th class="px-3 py-2">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(charge, index) in reviewForm.charges"
                  :key="`${index}-${charge.description}`"
                  class="border-t"
                >
                  <td class="px-3 py-2">
                    <InputText
                      v-model="charge.bl_reference"
                      class="w-full"
                      @update:model-value="markEdited(`charges[${index}].bl_reference`)"
                    />
                  </td>
                  <td class="px-3 py-2">
                    <InputText
                      v-model="charge.description"
                      class="w-full"
                      @update:model-value="markEdited(`charges[${index}].description`)"
                    />
                  </td>
                  <td class="px-3 py-2">
                    <select
                      v-model="charge.category"
                      class="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
                      @change="markEdited(`charges[${index}].category`)"
                    >
                      <option
                        v-for="option in chargeCategoryOptions"
                        :key="option"
                        :value="option"
                      >
                        {{ option }}
                      </option>
                    </select>
                  </td>
                  <td class="px-3 py-2">
                    <InputText
                      v-model="charge.amount"
                      class="w-full"
                      @update:model-value="markEdited(`charges[${index}].amount`)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold text-gray-800">Raw JSON</h3>
            <Button
              :label="showRawJson ? 'Hide advanced' : 'Show advanced'"
              size="small"
              severity="secondary"
              text
              @click="showRawJson = !showRawJson"
            />
          </div>
          <Textarea
            v-if="showRawJson"
            :model-value="reviewForm.raw_json"
            rows="8"
            class="w-full font-mono text-xs"
            readonly
          />
          <div
            v-else
            class="rounded border border-dashed border-gray-300 px-3 py-3 text-xs text-gray-600"
          >
            Advanced JSON is hidden. Click “Show advanced” to inspect raw model
            output.
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between w-full">
          <div class="flex gap-2">
            <Button
              label="Cancel Batch"
              severity="secondary"
              text
              :disabled="!isProcessingCurrentDocument"
              @click="cancelBatch"
            />
            <Button
              v-if="queueMode === 'batch'"
              label="Skip"
              severity="secondary"
              :disabled="isSavingCurrentReview"
              @click="skipCurrentReview"
            />
          </div>
          <div class="flex gap-2">
            <Button
              label="Save"
              icon="pi pi-check"
              :loading="isSavingCurrentReview"
              @click="confirmCurrentReview"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import {
  API_BASE_URL,
  CHARGE_CATEGORY_OPTIONS,
  PROVIDER_TYPE_OPTIONS,
  confirmDocument,
  fetchEmails,
  listDocuments,
  processDocument,
  reprocessDocument,
  retryDocument,
  type ChargeCategory,
  type ConfirmDocumentRequest,
  type DocumentListItem,
  type DocumentType,
  type InvoiceChargeInput,
  type ProcessDocumentResponse,
  type ProviderType,
} from "../services/api";

interface ReviewForm {
  document_id: string;
  document_type: string;
  ai_model: string;
  raw_json: string;
  overall_confidence: string;
  manually_edited_fields: string[];
  invoice_number: string | null;
  invoice_date: string | null;
  issuer_name: string | null;
  issuer_nif: string | null;
  recipient_name: string | null;
  recipient_nif: string | null;
  provider_type: ProviderType | "";
  currency_valid: boolean;
  currency_detected: string;
  bl_references: Array<string | Record<string, unknown>>;
  charges: InvoiceChargeInput[];
  totals: Record<string, unknown>;
  shipping_pol_code: string;
  shipping_pol_name: string;
  shipping_pod_code: string;
  shipping_pod_name: string;
  shipping_vessel: string;
  shipping_containers: string;
  field_statuses: Record<string, FieldStatus>;
  warnings: string[];
  errors: string[];
}
type FieldStatus = "ok" | "not_found" | "ambiguous";
interface UncertaintyRow {
  field: string;
  label: string;
  status: Exclude<FieldStatus, "ok">;
}

type QueueMode = "single" | "batch" | null;
type DocumentTab = "PENDING" | "PROCESSED" | "ERROR";

interface DocumentFilters {
  date_from: string;
  date_to: string;
  document_type: "" | DocumentType;
  party: string;
  booking: string;
}

const toast = useToast();

const documents = ref<DocumentListItem[]>([]);
const isLoadingDocuments = ref(false);
const isFetchingEmails = ref(false);
const selectedDocumentIds = ref<string[]>([]);
const activeTab = ref<DocumentTab>("PENDING");
const filters = ref<DocumentFilters>({
  date_from: "",
  date_to: "",
  document_type: "",
  party: "",
  booking: "",
});
const tabs: Array<{ value: DocumentTab; label: string }> = [
  { value: "PENDING", label: "Pending" },
  { value: "PROCESSED", label: "Processed" },
  { value: "ERROR", label: "Errors" },
];

const showReviewDialog = ref(false);
const reviewForm = ref<ReviewForm | null>(null);
const editedFields = ref<string[]>([]);
const showRawJson = ref(false);

const processingQueue = ref<string[]>([]);
const queueIndex = ref(0);
const queueMode = ref<QueueMode>(null);
const isProcessingCurrentDocument = ref(false);
const isSavingCurrentReview = ref(false);
const batchStats = ref({
  processed: 0,
  skipped: 0,
  errors: 0,
});
const providerTypeOptions = PROVIDER_TYPE_OPTIONS;
const chargeCategoryOptions = CHARGE_CATEGORY_OPTIONS;
const documentTypeOptions: DocumentType[] = [
  "CLIENT_INVOICE",
  "PROVIDER_INVOICE",
  "OTHER",
];

const processableDocumentIds = computed(() =>
  documents.value
    .filter((document) => isActionableForTab(document, activeTab.value))
    .map((document) => document.id)
);

const allProcessableSelected = computed(() => {
  if (processableDocumentIds.value.length === 0) {
    return false;
  }
  return processableDocumentIds.value.every((id) =>
    selectedDocumentIds.value.includes(id)
  );
});

const currentQueueDocumentId = computed(
  () => processingQueue.value[queueIndex.value] ?? null
);
const activeTabLabel = computed(
  () => tabs.find((tab) => tab.value === activeTab.value)?.label ?? "Documents"
);
const emptyStateMessage = computed(() => {
  if (activeTab.value === "PENDING") {
    return "No pending documents. Click \"Fetch Emails\" to import new files.";
  }
  if (activeTab.value === "PROCESSED") {
    return "No processed documents found with the current filters.";
  }
  return "No error documents found with the current filters.";
});
const batchActionLabel = computed(() => {
  if (activeTab.value === "PENDING") {
    return "Process Selected";
  }
  if (activeTab.value === "PROCESSED") {
    return "Reprocess Selected";
  }
  return "Retry Selected";
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

const clearFilters = (): void => {
  filters.value = {
    date_from: "",
    date_to: "",
    document_type: "",
    party: "",
    booking: "",
  };
  void loadDocuments();
};
const fieldLabelMap: Record<string, string> = {
  invoice_number: "Invoice number",
  invoice_date: "Invoice date",
  issuer_name: "Issuer name",
  issuer_nif: "Issuer NIF",
  recipient_name: "Recipient name",
  recipient_nif: "Recipient NIF",
  provider_type: "Provider type",
  "totals.total": "Total amount",
  bl_references: "BL references",
  charges: "Charge lines",
  "shipping.pol.code": "POL code",
  "shipping.pod.code": "POD code",
  "shipping.vessel": "Vessel",
  "shipping.containers": "Containers",
};

const reviewUncertaintyRows = (form: ReviewForm): UncertaintyRow[] =>
  Object.entries(form.field_statuses)
    .filter(([, status]) => status === "not_found" || status === "ambiguous")
    .map(([field, status]) => ({
      field,
      label: fieldLabelMap[field] ?? field,
      status: status as UncertaintyRow["status"],
    }));

const asObjectRecord = (value: unknown): Record<string, unknown> | null => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
};

const asString = (value: unknown): string =>
  typeof value === "string" ? value : "";

const parseContainerList = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
};

const normalizeContainerInput = (value: string): string[] =>
  value
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);

const mapShippingDetailsToForm = (
  details: Record<string, unknown>
): {
  pol_code: string;
  pol_name: string;
  pod_code: string;
  pod_name: string;
  vessel: string;
  containers: string[];
} => {
  const pol = asObjectRecord(details.pol);
  const pod = asObjectRecord(details.pod);
  return {
    pol_code: asString(pol?.code),
    pol_name: asString(pol?.name),
    pod_code: asString(pod?.code),
    pod_name: asString(pod?.name),
    vessel: asString(details.vessel),
    containers: parseContainerList(details.containers),
  };
};


const formatDate = (value: string): string =>
  new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
const formatMoney = (value: string | number | null): string => {
  if (value === null || value === "") {
    return "—";
  }
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return "—";
  }
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "EUR",
  }).format(amount);
};

const getDocumentFileUrl = (fileUrl: string): string => {
  const apiOrigin = API_BASE_URL.replace(/\/api$/, "");
  return `${apiOrigin}${fileUrl}`;
};

const isActionableForTab = (document: DocumentListItem, tab: DocumentTab): boolean => {
  if (tab === "PENDING") {
    return document.status === "PENDING";
  }
  if (tab === "PROCESSED") {
    return document.status === "PROCESSED";
  }
  return document.status === "ERROR";
};

const setActiveTab = (tab: DocumentTab): void => {
  if (activeTab.value === tab) {
    return;
  }
  activeTab.value = tab;
  selectedDocumentIds.value = [];
  void loadDocuments();
};

const toggleDocumentSelection = (documentId: string): void => {
  if (selectedDocumentIds.value.includes(documentId)) {
    selectedDocumentIds.value = selectedDocumentIds.value.filter(
      (id) => id !== documentId
    );
    return;
  }
  selectedDocumentIds.value = [...selectedDocumentIds.value, documentId];
};

const toggleSelectAllProcessable = (): void => {
  if (allProcessableSelected.value) {
    selectedDocumentIds.value = selectedDocumentIds.value.filter(
      (id) => !processableDocumentIds.value.includes(id)
    );
    return;
  }

  const merged = new Set([
    ...selectedDocumentIds.value,
    ...processableDocumentIds.value,
  ]);
  selectedDocumentIds.value = Array.from(merged);
};

const loadDocuments = async (): Promise<void> => {
  isLoadingDocuments.value = true;
  try {
    const response = await listDocuments({
      status: activeTab.value,
      document_type: filters.value.document_type || undefined,
      date_from: filters.value.date_from || undefined,
      date_to: filters.value.date_to || undefined,
      party: filters.value.party.trim() || undefined,
      booking: filters.value.booking.trim() || undefined,
      limit: 500,
    });
    documents.value = response.documents;
    selectedDocumentIds.value = selectedDocumentIds.value.filter((id) =>
      response.documents.some((document) => document.id === id)
    );
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to load documents",
      detail: extractErrorMessage(error),
      life: 4000,
    });
  } finally {
    isLoadingDocuments.value = false;
  }
};

const handleFetchEmails = async (): Promise<void> => {
  isFetchingEmails.value = true;
  try {
    const result = await fetchEmails();
    toast.add({
      severity: "success",
      summary: "Email fetch completed",
      detail: `Imported ${result.imported_documents}, duplicates ${result.duplicate_documents}, scanned ${result.scanned_messages} email(s).`,
      life: 4500,
    });
    await loadDocuments();
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Failed to fetch emails",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isFetchingEmails.value = false;
  }
};

const mapProcessResponseToReviewForm = (
  response: ProcessDocumentResponse
): ReviewForm => {
  const shippingDetails = mapShippingDetailsToForm(response.shipping_details);

  return {
    document_id: response.document_id,
    document_type: response.document_type,
    ai_model: response.ai_model,
    raw_json: response.raw_json,
    overall_confidence: response.overall_confidence,
    manually_edited_fields: [],
    invoice_number: response.invoice_number,
    invoice_date: response.invoice_date,
    issuer_name: response.issuer_name,
    issuer_nif: response.issuer_nif,
    recipient_name: response.recipient_name,
    recipient_nif: response.recipient_nif,
    provider_type: response.provider_type ?? "",
    currency_valid: response.currency_valid,
    currency_detected: response.currency_detected,
    bl_references: response.bl_references,
    charges: response.charges.map((charge) => ({
      bl_reference: charge.bl_reference,
      description: charge.description,
      category: charge.category as ChargeCategory,
      amount: String(charge.amount),
      container: charge.container ?? null,
    })),
    totals: { ...response.totals },
    shipping_pol_code: shippingDetails.pol_code,
    shipping_pol_name: shippingDetails.pol_name,
    shipping_pod_code: shippingDetails.pod_code,
    shipping_pod_name: shippingDetails.pod_name,
    shipping_vessel: shippingDetails.vessel,
    shipping_containers: shippingDetails.containers.join(", "),
    field_statuses: { ...response.field_statuses },
    warnings: [...response.warnings],
    errors: [...response.errors],
  };
};

const resetQueueState = (): void => {
  processingQueue.value = [];
  queueIndex.value = 0;
  queueMode.value = null;
  isProcessingCurrentDocument.value = false;
  isSavingCurrentReview.value = false;
  showReviewDialog.value = false;
  showRawJson.value = false;
  reviewForm.value = null;
  editedFields.value = [];
};

const showBatchSummaryToast = (): void => {
  toast.add({
    severity: "info",
    summary: "Batch completed",
    detail: `Processed ${batchStats.value.processed}, skipped ${batchStats.value.skipped}, errors ${batchStats.value.errors}`,
    life: 4500,
  });
};

const getDocumentStatus = (documentId: string): string | null =>
  documents.value.find((document) => document.id === documentId)?.status ?? null;

const loadNextQueueDocument = async (): Promise<void> => {
  const documentId = processingQueue.value[queueIndex.value];
  if (!documentId) {
    isProcessingCurrentDocument.value = false;
    if (queueMode.value === "batch") {
      showBatchSummaryToast();
    }
    await loadDocuments();
    resetQueueState();
    return;
  }

  isProcessingCurrentDocument.value = true;
  try {
    const status = getDocumentStatus(documentId);
    const result =
      status === "ERROR"
        ? await retryDocument(documentId)
        : status === "PROCESSED"
          ? await reprocessDocument(documentId)
        : await processDocument(documentId);
    reviewForm.value = mapProcessResponseToReviewForm(result);
    editedFields.value = [];
    showRawJson.value = false;
    showReviewDialog.value = true;
  } catch (error) {
    batchStats.value.errors += 1;
    toast.add({
      severity: "error",
      summary: "Could not process document",
      detail: extractErrorMessage(error),
      life: 4500,
    });
    queueIndex.value += 1;
    await loadNextQueueDocument();
  }
};

const startSingleProcessing = async (documentId: string): Promise<void> => {
  batchStats.value = { processed: 0, skipped: 0, errors: 0 };
  processingQueue.value = [documentId];
  queueIndex.value = 0;
  queueMode.value = "single";
  await loadNextQueueDocument();
};

const createManualReviewForm = (document: DocumentListItem): ReviewForm => {
  const bookingReferences = [...document.booking_references];
  return {
    document_id: document.id,
    document_type: document.document_type ?? "PROVIDER_INVOICE",
    ai_model: "manual-entry",
    raw_json: "{}",
    overall_confidence: "LOW",
    manually_edited_fields: [],
    invoice_number: document.invoice_number,
    invoice_date: null,
    issuer_name: null,
    issuer_nif: null,
    recipient_name: null,
    recipient_nif: null,
    provider_type: "",
    currency_valid: true,
    currency_detected: "EUR",
    bl_references: bookingReferences,
    charges: [
      {
        bl_reference: bookingReferences[0] ?? null,
        description: "",
        category: "OTHER",
        amount: "",
        container: null,
      },
    ],
    totals: {},
    shipping_pol_code: "",
    shipping_pol_name: "",
    shipping_pod_code: "",
    shipping_pod_name: "",
    shipping_vessel: "",
    shipping_containers: "",
    field_statuses: {},
    warnings: ["Manual review mode: complete required fields before saving."],
    errors: [],
  };
};

const startManualReview = (documentId: string): void => {
  const document = documents.value.find((item) => item.id === documentId);
  if (!document) {
    return;
  }

  batchStats.value = { processed: 0, skipped: 0, errors: 0 };
  processingQueue.value = [documentId];
  queueIndex.value = 0;
  queueMode.value = "single";
  isProcessingCurrentDocument.value = true;
  reviewForm.value = createManualReviewForm(document);
  editedFields.value = [];
  showRawJson.value = false;
  showReviewDialog.value = true;
};

const startBatchProcessing = async (): Promise<void> => {
  if (selectedDocumentIds.value.length === 0) {
    return;
  }

  const ids = selectedDocumentIds.value.filter((id) =>
    processableDocumentIds.value.includes(id)
  );
  if (ids.length === 0) {
    toast.add({
      severity: "warn",
      summary: "No actionable documents selected",
      detail: `Select at least one ${activeTabLabel.value.toLowerCase()} document.`,
      life: 4000,
    });
    return;
  }

  batchStats.value = { processed: 0, skipped: 0, errors: 0 };
  processingQueue.value = ids;
  queueIndex.value = 0;
  queueMode.value = "batch";
  await loadNextQueueDocument();
};

const markEdited = (field: string): void => {
  if (!editedFields.value.includes(field)) {
    editedFields.value = [...editedFields.value, field];
  }
};

const advanceQueue = async (result: "processed" | "skipped"): Promise<void> => {
  if (result === "processed") {
    batchStats.value.processed += 1;
  } else {
    batchStats.value.skipped += 1;
  }

  showReviewDialog.value = false;
  reviewForm.value = null;
  queueIndex.value += 1;
  await loadNextQueueDocument();
};

const buildConfirmPayload = (): ConfirmDocumentRequest => {
  const form = reviewForm.value;
  if (!form) {
    throw new Error("No review form loaded");
  }

  const shipping_details: Record<string, unknown> = {};
  const polCode = form.shipping_pol_code.trim();
  if (polCode.length > 0) {
    shipping_details.pol = {
      code: polCode,
      name: form.shipping_pol_name.trim(),
    };
  }

  const podCode = form.shipping_pod_code.trim();
  if (podCode.length > 0) {
    shipping_details.pod = {
      code: podCode,
      name: form.shipping_pod_name.trim(),
    };
  }

  const vessel = form.shipping_vessel.trim();
  if (vessel.length > 0) {
    shipping_details.vessel = vessel;
  }

  const containers = normalizeContainerInput(form.shipping_containers);
  if (containers.length > 0) {
    shipping_details.containers = containers;
  }

  return {
    document_id: form.document_id,
    document_type: form.document_type,
    ai_model: form.ai_model,
    raw_json: form.raw_json,
    overall_confidence: form.overall_confidence,
    manually_edited_fields: [...editedFields.value],
    invoice_number: form.invoice_number,
    invoice_date: form.invoice_date,
    issuer_name: form.issuer_name,
    issuer_nif: form.issuer_nif,
    recipient_name: form.recipient_name,
    recipient_nif: form.recipient_nif,
    provider_type:
      form.provider_type && form.provider_type.trim().length > 0
        ? form.provider_type
        : null,
    currency_valid: form.currency_valid,
    currency_detected: form.currency_detected,
    bl_references: form.bl_references,
    charges: form.charges.map((charge) => ({
      bl_reference: charge.bl_reference,
      description: charge.description,
      category: charge.category,
      amount: String(charge.amount),
      container: charge.container ?? null,
    })),
    totals: form.totals,
    shipping_details,
  };
};

const confirmCurrentReview = async (): Promise<void> => {
  if (!reviewForm.value) {
    return;
  }

  isSavingCurrentReview.value = true;
  try {
    const payload = buildConfirmPayload();
    const result = await confirmDocument(payload);
    toast.add({
      severity: "success",
      summary: "Invoice saved",
      detail:
        result.booking_ids.length > 0
          ? `Updated bookings: ${result.booking_ids.join(", ")}`
          : "Document persisted successfully.",
      life: 3500,
    });
    window.dispatchEvent(new Event("bookings:refresh"));
    await advanceQueue("processed");
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Save failed",
      detail: extractErrorMessage(error),
      life: 5000,
    });
  } finally {
    isSavingCurrentReview.value = false;
  }
};

const skipCurrentReview = async (): Promise<void> => {
  await advanceQueue("skipped");
};

const cancelBatch = async (): Promise<void> => {
  const hasRemaining =
    queueIndex.value < processingQueue.value.length - 1 &&
    queueMode.value === "batch";
  if (hasRemaining) {
    toast.add({
      severity: "warn",
      summary: "Batch cancelled",
      detail: "Remaining documents were not processed.",
      life: 3500,
    });
  }
  await loadDocuments();
  resetQueueState();
};

onMounted(async () => {
  await loadDocuments();
});
</script>
