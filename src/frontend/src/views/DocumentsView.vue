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
          label="Process Selected"
          icon="pi pi-play"
          :disabled="selectedDocumentIds.length === 0 || isProcessingCurrentDocument"
          :loading="isProcessingCurrentDocument && queueMode === 'batch'"
          @click="startBatchProcessing"
        />
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
      <p>No documents yet. Click "Fetch Emails" to get started.</p>
    </div>

    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-4 border-b flex items-center justify-between">
        <div class="text-sm text-gray-600">
          {{ documents.length }} document(s)
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
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3">Type</th>
              <th class="px-4 py-3">Created</th>
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
                  :disabled="!isQueueEligible(document) || isProcessingCurrentDocument"
                  @change="toggleDocumentSelection(document.id)"
                />
              </td>
              <td class="px-4 py-3">
                <div class="font-medium text-gray-800">{{ document.filename }}</div>
                <div v-if="document.email_sender" class="text-xs text-gray-500 mt-1">
                  {{ document.email_sender }}
                </div>
                <div
                  v-if="document.error_message"
                  class="text-xs text-red-600 mt-1"
                >
                  {{ document.error_message }}
                </div>
              </td>
              <td class="px-4 py-3">
                <span
                  class="inline-flex px-2 py-1 rounded text-xs font-semibold"
                  :class="statusClass(document.status)"
                >
                  {{ document.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-700">
                {{ document.document_type ?? "—" }}
              </td>
              <td class="px-4 py-3 text-gray-700">
                {{ formatDate(document.created_at) }}
              </td>
              <td class="px-4 py-3">
                <Button
                  v-if="isProcessable(document)"
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
                  v-else-if="isReprocessable(document)"
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

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-gray-600">Document type</label>
            <InputText
              class="w-full"
              :model-value="reviewForm.document_type"
              disabled
            />
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
  shipping_details: Record<string, unknown>;
  warnings: string[];
  errors: string[];
}

type QueueMode = "single" | "batch" | null;

const toast = useToast();

const documents = ref<DocumentListItem[]>([]);
const isLoadingDocuments = ref(false);
const isFetchingEmails = ref(false);
const selectedDocumentIds = ref<string[]>([]);

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

const processableDocumentIds = computed(() =>
  documents.value.filter(isQueueEligible).map((document) => document.id)
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

const statusClass = (status: string): string => {
  switch (status) {
    case "PENDING":
      return "bg-gray-100 text-gray-700";
    case "PROCESSING":
      return "bg-blue-100 text-blue-700";
    case "PROCESSED":
      return "bg-green-100 text-green-700";
    case "ERROR":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
};

const formatDate = (value: string): string =>
  new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const isProcessable = (document: DocumentListItem): boolean =>
  document.status === "PENDING" || document.status === "ERROR";

const isReprocessable = (document: DocumentListItem): boolean =>
  document.status === "PROCESSED";

const isQueueEligible = (document: DocumentListItem): boolean =>
  isProcessable(document) || isReprocessable(document);

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
    const response = await listDocuments({ limit: 500 });
    documents.value = response.documents;
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
): ReviewForm => ({
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
  shipping_details: {},
  warnings: [...response.warnings],
  errors: [...response.errors],
});

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
      summary: "No processable documents selected",
      detail:
        "Only documents in PENDING, ERROR, or PROCESSED status can be processed.",
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
    shipping_details: form.shipping_details,
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
