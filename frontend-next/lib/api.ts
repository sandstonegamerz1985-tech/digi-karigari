const API = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed. Check that the Digi-Karigari API is running.');
  return data as T;
}
export type Product = {id:string; title:string; story:string; description?:string; materials:string[]; price:number; display_price?:number; stock:number; category:string; tags:string[]; image_url:string; location:string; artisan_name:string; cluster_info:string; is_verified:boolean; artisan_wallet_address?:string|null; token_id?:string|null};
export const api = {
  products: async (search = '', location = '', buyerType = 'retail') => (await request<Product[]>(`/api/products?search=${encodeURIComponent(search)}&location=${encodeURIComponent(location)}&buyer_type=${buyerType}`)).map(p => ({...p, image_url: p.image_url.startsWith('/') ? `${API}${p.image_url}` : p.image_url})),
  createOrder: (body: {product_id:string;quantity:number;buyer_name:string;buyer_address:string;payment_method:'demo_upi'|'demo_card'|'wallet'}) => request<any>('/api/orders', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}),
  track: (reference:string) => request<any>(`/api/orders/track?reference=${encodeURIComponent(reference)}`),
  publish: (form:FormData) => request<any>('/api/products', {method:'POST', body:form}),
  verify: (body:any) => request<any>('/api/artisan/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}),
  orders: (artisanId='artisan-demo') => request<any[]>(`/api/artisan/orders?artisan_id=${encodeURIComponent(artisanId)}`),
  ship: (body:any) => request<any>('/api/orders/ship', {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}),
  support: () => request<any>('/api/support')
};
