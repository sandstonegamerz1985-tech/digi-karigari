export const formatINR = (n) => "₹" + Number(n || 0).toLocaleString("en-IN");

export const formatDate = (iso) =>
  iso ? new Date(iso + (iso.endsWith("Z") || iso.includes("+") ? "" : "Z")).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  }) : "";

export const STATUS_LABELS = {
  placed: "Order placed",
  packed: "Packed",
  processing: "Being prepared",
  partially_shipped: "Partly shipped",
  shipped: "Shipped",
  delivered: "Delivered",
};

export const MAX_IMAGE_MB = 5;
export const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

// Returns an error message for a bad image file, or "" if it looks fine.
export function checkImageFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) return `${file.name}: only JPG, PNG or WEBP images are allowed.`;
  if (file.size > MAX_IMAGE_MB * 1024 * 1024) return `${file.name}: image is larger than ${MAX_IMAGE_MB} MB.`;
  return "";
}
