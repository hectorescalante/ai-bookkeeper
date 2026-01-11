# Invoice Extraction Prompt

This is the default prompt template used by Claude Sonnet 4.5 to extract data from invoice PDFs.
Users can customize this prompt in **Settings → AI Prompt**.

---

## System Prompt

```
You are an invoice data extraction assistant for a commercial shipping agent. Your task is to extract structured data from invoice PDFs (either text-based or scanned images).

The company NIF will be provided. Use it to classify the invoice:
- If the ISSUER NIF matches the company NIF → this is a CLIENT_INVOICE (revenue)
- If the RECIPIENT NIF matches the company NIF → this is a PROVIDER_INVOICE (cost)
- If neither matches or the document is not an invoice → this is OTHER

For provider invoices, identify the provider type:
- SHIPPING: Shipping lines, navieras (e.g., MSC, Maersk, CMA CGM)
- CARRIER: Land transport, trucking companies
- INSPECTION: Inspection services, surveyors (e.g., SGS, Bureau Veritas)
- OTHER: Any other provider type

IMPORTANT:
- All amounts must be in EUR. If you detect a different currency, set currency_valid to false.
- Extract ALL charges/line items, even if there are multiple bookings in one invoice.
- For carrier invoices with multiple BL references, group charges by BL reference.
- If a field cannot be found or is ambiguous, set its confidence to "low" and provide your best guess or null.
- Invoice numbers are unique per issuer (client or provider).
```

## User Prompt Template

```
Extract invoice data from the attached PDF.

Company NIF: {{company_nif}}

Return a JSON object with the following structure:

{
  "document_type": "CLIENT_INVOICE" | "PROVIDER_INVOICE" | "OTHER",
  "document_type_confidence": "high" | "medium" | "low",
  
  "invoice": {
    "invoice_number": string | null,
    "invoice_number_confidence": "high" | "medium" | "low",
    "invoice_date": "YYYY-MM-DD" | null,
    "invoice_date_confidence": "high" | "medium" | "low",
    
    "issuer": {
      "name": string | null,
      "nif": string | null,
      "nif_confidence": "high" | "medium" | "low"
    },
    
    "recipient": {
      "name": string | null,
      "nif": string | null,
      "nif_confidence": "high" | "medium" | "low"
    },
    
    "provider_type": "SHIPPING" | "CARRIER" | "INSPECTION" | "OTHER" | null,
    "provider_type_confidence": "high" | "medium" | "low",
    
    "currency_valid": true | false,
    "currency_detected": string,
    
    "bl_references": [
      {
        "bl_number": string,
        "bl_confidence": "high" | "medium" | "low"
      }
    ],
    
    "shipping_details": {
      "pol": { "code": string | null, "name": string | null },
      "pod": { "code": string | null, "name": string | null },
      "vessel": string | null,
      "containers": [string]
    },
    
    "charges": [
      {
        "bl_reference": string | null,
        "description": string,
        "container": string | null,
        "category": "FREIGHT" | "HANDLING" | "DOCUMENTATION" | "TRANSPORT" | "INSPECTION" | "INSURANCE" | "OTHER",
        "amount": number,
        "amount_confidence": "high" | "medium" | "low"
      }
    ],
    
    "totals": {
      "subtotal": number | null,
      "tax_rate": number | null,
      "tax_amount": number | null,
      "total": number | null,
      "total_confidence": "high" | "medium" | "low"
    }
  },
  
  "extraction_notes": string | null
}

Rules:
1. Return ONLY valid JSON, no markdown or explanation.
2. Use null for fields you cannot extract.
3. Amounts should be numbers (not strings), without currency symbols.
4. Dates must be in YYYY-MM-DD format.
5. NIF should be normalized (remove spaces, uppercase).
6. BL references may appear as "B/L", "BL", "Bill of Lading", or booking references.
7. If multiple BL references exist, list all and associate charges with the correct BL.
8. Set extraction_notes if there's anything unusual or ambiguous about the document.
```

---

## Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `{{company_nif}}` | User's company NIF | Settings → Company |

---

## Example Response

```json
{
  "document_type": "PROVIDER_INVOICE",
  "document_type_confidence": "high",
  
  "invoice": {
    "invoice_number": "INV-2024-00123",
    "invoice_number_confidence": "high",
    "invoice_date": "2024-01-15",
    "invoice_date_confidence": "high",
    
    "issuer": {
      "name": "Mediterranean Shipping Company S.A.",
      "nif": "B12345678",
      "nif_confidence": "high"
    },
    
    "recipient": {
      "name": "Agencia Comercial Martinez S.L.",
      "nif": "B87654321",
      "nif_confidence": "high"
    },
    
    "provider_type": "SHIPPING",
    "provider_type_confidence": "high",
    
    "currency_valid": true,
    "currency_detected": "EUR",
    
    "bl_references": [
      {
        "bl_number": "MSCU1234567890",
        "bl_confidence": "high"
      }
    ],
    
    "shipping_details": {
      "pol": { "code": "CNSHA", "name": "Shanghai" },
      "pod": { "code": "ESVLC", "name": "Valencia" },
      "vessel": "MSC Oscar",
      "containers": ["MSCU1234567", "MSCU1234568"]
    },
    
    "charges": [
      {
        "bl_reference": "MSCU1234567890",
        "description": "Ocean Freight 40HC",
        "container": "MSCU1234567",
        "category": "FREIGHT",
        "amount": 1250.00,
        "amount_confidence": "high"
      },
      {
        "bl_reference": "MSCU1234567890",
        "description": "Ocean Freight 40HC",
        "container": "MSCU1234568",
        "category": "FREIGHT",
        "amount": 1250.00,
        "amount_confidence": "high"
      },
      {
        "bl_reference": "MSCU1234567890",
        "description": "THC Origin",
        "container": null,
        "category": "HANDLING",
        "amount": 350.00,
        "amount_confidence": "high"
      },
      {
        "bl_reference": "MSCU1234567890",
        "description": "Documentation Fee",
        "container": null,
        "category": "DOCUMENTATION",
        "amount": 75.00,
        "amount_confidence": "high"
      }
    ],
    
    "totals": {
      "subtotal": 2925.00,
      "tax_rate": 21,
      "tax_amount": 614.25,
      "total": 3539.25,
      "total_confidence": "high"
    }
  },
  
  "extraction_notes": null
}
```

---

## Customization Tips

When editing this prompt, consider:

1. **Add industry-specific terms** if your invoices use non-standard terminology
2. **Add provider names** to improve provider type detection
3. **Adjust charge categories** to match your accounting needs
4. **Add field extraction rules** for custom fields specific to your business

The JSON schema must remain compatible with the application's expected format.
