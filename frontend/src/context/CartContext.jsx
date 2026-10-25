// The cart lives in the browser (localStorage). The server re-checks prices and stock at checkout,
// so the numbers shown here are only an estimate.
import { createContext, useContext, useEffect, useState } from "react";

const CartContext = createContext(null);
const KEY = "dk_cart";

function load() {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(load);

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
    } catch {
      /* storage full or blocked: the cart simply will not persist */
    }
  }, [items]);

  const add = (product, quantity = 1) =>
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === product.id);
      const wanted = Math.min((existing ? existing.quantity : 0) + quantity, product.stock, 10);
      const snapshot = {
        product_id: product.id,
        title: product.title,
        price: product.price,
        shipping_fee: product.shipping_fee,
        image_url: product.image_url,
        stock: product.stock,
        quantity: wanted,
      };
      return existing ? prev.map((i) => (i.product_id === product.id ? snapshot : i)) : [...prev, snapshot];
    });

  const setQuantity = (productId, quantity) =>
    setItems((prev) =>
      prev.map((i) => (i.product_id === productId ? { ...i, quantity: Math.max(1, Math.min(quantity, i.stock, 10)) } : i))
    );

  const remove = (productId) => setItems((prev) => prev.filter((i) => i.product_id !== productId));
  const clear = () => setItems([]);

  const count = items.reduce((n, i) => n + i.quantity, 0);
  const subtotal = items.reduce((n, i) => n + i.price * i.quantity, 0);
  const shipping = items.reduce((n, i) => n + i.shipping_fee, 0);

  return (
    <CartContext.Provider value={{ items, add, setQuantity, remove, clear, count, subtotal, shipping, total: subtotal + shipping }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
