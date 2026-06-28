import { z } from "zod";

export const productSchema = z.object({
  sku: z.string().min(1).max(64),
  name: z.string().min(1).max(120),
  category: z.string().max(80).optional(),
  description: z.string().max(2000).optional()
});

export const locationSchema = z.object({
  code: z.string().min(1).max(32),
  name: z.string().min(1).max(120),
  timezone: z.string().min(1).max(64),
  address: z.string().max(1000).optional()
});

export const batchSchema = z.object({
  product_id: z.string().uuid(),
  location_id: z.string().uuid(),
  batch_number: z.string().min(1).max(64),
  quantity_received: z.coerce.number().int().nonnegative(),
  quantity_available: z.coerce.number().int().nonnegative(),
  received_date: z.string().min(1),
  expiry_date: z.string().min(1),
  notes: z.string().max(2000).optional()
}).refine((data) => data.quantity_available <= data.quantity_received, {
  message: "Available quantity cannot exceed received quantity.",
  path: ["quantity_available"]
});

export type ProductFormValues = z.infer<typeof productSchema>;
export type LocationFormValues = z.infer<typeof locationSchema>;
export type BatchFormValues = z.infer<typeof batchSchema>;
