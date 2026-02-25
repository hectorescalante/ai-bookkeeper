import axios from "axios";
import type { AxiosInstance, AxiosRequestConfig } from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[API Error]", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Generic API methods
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then((res) => res.data),

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config).then((res) => res.data),

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config).then((res) => res.data),

  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<T>(url, data, config).then((res) => res.data),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then((res) => res.data),
};

// Health check
export const checkHealth = () => api.get<{ status: string }>("/health");

export interface DocumentListItem {
  id: string;
  filename: string;
  status: string;
  document_type: string | null;
  created_at: string;
  processed_at: string | null;
  email_sender: string | null;
  email_subject: string | null;
  error_message: string | null;
  error_retryable: boolean | null;
}

export interface ListDocumentsResponse {
  documents: DocumentListItem[];
  total: number;
}

export interface FetchEmailsResponse {
  scanned_messages: number;
  pdf_attachments_found: number;
  imported_documents: number;
  duplicate_documents: number;
}

export interface SettingsResponse {
  id: string;
  has_api_key: boolean;
  outlook_configured: boolean;
  default_export_path: string;
  extraction_prompt: string;
}

export interface ConfigureSettingsRequest {
  gemini_api_key?: string | null;
  default_export_path?: string | null;
  extraction_prompt?: string | null;
}

export interface CompanyResponse {
  id: string;
  name: string;
  nif: string;
  commission_rate: string | number;
  is_configured: boolean;
}

export interface ConfigureCompanyRequest {
  name: string;
  nif: string;
  commission_rate: string | number;
}

export interface OutlookConnectResponse {
  authorization_url: string;
}

export interface OutlookDisconnectResponse {
  outlook_configured: boolean;
}

export interface BookingListItem {
  id: string;
  client_name: string | null;
  created_at: string;
  status: string;
  total_revenue: string | number;
  total_costs: string | number;
  margin: string | number;
  commission: string | number;
  document_count: number;
}

export interface ListBookingsResponse {
  bookings: BookingListItem[];
  total: number;
}

export interface BookingDetailResponse {
  id: string;
  created_at: string;
  status: string;
  client_id: string | null;
  client_name: string | null;
  client_nif: string | null;
  pol_code: string | null;
  pol_name: string | null;
  pod_code: string | null;
  pod_name: string | null;
  vessel: string | null;
  containers: string[];
  total_revenue: string | number;
  total_costs: string | number;
  margin: string | number;
  margin_percentage: string | number;
  commission: string | number;
  revenue_charge_count: number;
  cost_charge_count: number;
}

export interface UpdateBookingRequest {
  vessel?: string | null;
  containers?: string[] | null;
  pol_code?: string | null;
  pol_name?: string | null;
  pod_code?: string | null;
  pod_name?: string | null;
}
export const PROVIDER_TYPE_OPTIONS = [
  "SHIPPING",
  "CARRIER",
  "INSPECTION",
  "OTHER",
] as const;

export type ProviderType = (typeof PROVIDER_TYPE_OPTIONS)[number];

export const CHARGE_CATEGORY_OPTIONS = [
  "FREIGHT",
  "HANDLING",
  "DOCUMENTATION",
  "TRANSPORT",
  "INSPECTION",
  "INSURANCE",
  "OTHER",
] as const;

export type ChargeCategory = (typeof CHARGE_CATEGORY_OPTIONS)[number];

export interface InvoiceChargeInput {
  bl_reference: string | null;
  description: string;
  category: ChargeCategory;
  amount: string;
  container?: string | null;
}

export interface ProcessDocumentResponse {
  document_id: string;
  document_type: string;
  document_type_confidence: string;
  ai_model: string;
  raw_json: string;
  invoice_number: string | null;
  invoice_date: string | null;
  issuer_name: string | null;
  issuer_nif: string | null;
  recipient_name: string | null;
  recipient_nif: string | null;
  provider_type: ProviderType | null;
  currency_valid: boolean;
  currency_detected: string;
  bl_references: Array<string | Record<string, unknown>>;
  charges: InvoiceChargeInput[];
  totals: Record<string, unknown>;
  extraction_notes: string | null;
  overall_confidence: string;
  warnings: string[];
  errors: string[];
}

export interface ConfirmDocumentRequest {
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
  provider_type: ProviderType | null;
  currency_valid: boolean;
  currency_detected: string;
  bl_references: Array<string | Record<string, unknown>>;
  charges: InvoiceChargeInput[];
  totals: Record<string, unknown>;
  shipping_details: Record<string, unknown>;
}

export interface ConfirmDocumentResponse {
  document_id: string;
  invoice_id: string | null;
  document_type: string;
  status: string;
  booking_ids: string[];
}

export interface CommissionReportRequest {
  date_from?: string | null;
  date_to?: string | null;
  status?: string | null;
}

export interface CommissionReportItem {
  booking_id: string;
  client_name: string | null;
  created_at: string;
  status: string;
  total_revenue: string | number;
  total_costs: string | number;
  margin: string | number;
  commission: string | number;
}

export interface CommissionReportTotals {
  booking_count: number;
  total_revenue: string | number;
  total_costs: string | number;
  total_margin: string | number;
  total_commission: string | number;
}

export interface CommissionReportResponse {
  items: CommissionReportItem[];
  totals: CommissionReportTotals;
}

export interface FileDownloadResponse {
  blob: Blob;
  file_name: string;
}

export const listDocuments = (params?: {
  status?: string;
  limit?: number;
}) =>
  api.get<ListDocumentsResponse>("/documents", {
    params,
  });

export const processDocument = (documentId: string) =>
  api.post<ProcessDocumentResponse>("/invoices/process", {
    document_id: documentId,
  });

export const fetchEmails = (maxMessages = 25) =>
  api.post<FetchEmailsResponse>("/documents/fetch", {
    max_messages: maxMessages,
  });

export const getSettings = () => api.get<SettingsResponse>("/config/settings");

export const configureSettings = (payload: ConfigureSettingsRequest) =>
  api.post<SettingsResponse>("/config/settings", payload);

export const getCompany = () => api.get<CompanyResponse>("/config/company");

export const configureCompany = (payload: ConfigureCompanyRequest) =>
  api.post<CompanyResponse>("/config/company", payload);

export const connectOutlook = () =>
  api.get<OutlookConnectResponse>("/settings/outlook/connect");

export const disconnectOutlook = () =>
  api.post<OutlookDisconnectResponse>("/settings/outlook/disconnect");

export const confirmDocument = (payload: ConfirmDocumentRequest) =>
  api.post<ConfirmDocumentResponse>("/invoices/confirm", payload);

export const listBookings = (params?: {
  client_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  descending?: boolean;
}) =>
  api.get<ListBookingsResponse>("/bookings", {
    params,
  });

export const getBookingDetail = (bookingId: string) =>
  api.get<BookingDetailResponse>(`/bookings/${encodeURIComponent(bookingId)}`);

export const updateBooking = (
  bookingId: string,
  payload: UpdateBookingRequest
) =>
  api.patch<BookingDetailResponse>(
    `/bookings/${encodeURIComponent(bookingId)}`,
    payload
  );

export const markBookingComplete = (bookingId: string) =>
  api.post<BookingDetailResponse>(
    `/bookings/${encodeURIComponent(bookingId)}/complete`
  );

export const revertBookingToPending = (bookingId: string) =>
  api.post<BookingDetailResponse>(
    `/bookings/${encodeURIComponent(bookingId)}/revert`
  );

const extractFilename = (
  contentDisposition: string | undefined,
  fallback: string
): string => {
  if (!contentDisposition) {
    return fallback;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const basicMatch = contentDisposition.match(/filename="([^"]+)"/i);
  if (basicMatch?.[1]) {
    return basicMatch[1];
  }

  return fallback;
};

export const exportBooking = async (bookingId: string) => {
  const response = await apiClient.get<Blob>(
    `/bookings/${encodeURIComponent(bookingId)}/export`,
    { responseType: "blob" }
  );
  return {
    blob: response.data,
    file_name: extractFilename(
      response.headers["content-disposition"],
      `booking-${bookingId}.xlsx`
    ),
  } satisfies FileDownloadResponse;
};

export const generateCommissionReport = (payload: CommissionReportRequest) =>
  api.post<CommissionReportResponse>("/reports/commission", payload);

export const exportCommissionReport = async (
  payload: CommissionReportRequest & { file_name?: string | null }
) => {
  const response = await apiClient.post<Blob>("/reports/export", payload, {
    responseType: "blob",
  });
  return {
    blob: response.data,
    file_name: extractFilename(
      response.headers["content-disposition"],
      "commission-report.xlsx"
    ),
  } satisfies FileDownloadResponse;
};

export default api;
