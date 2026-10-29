// English / Hindi labels (demo-level). Menus, buttons, headings and form labels are translated.
// NOT translated: text written by sellers, AI suggestions, error messages from the server,
// and the policy pages. Those stay in English for now.
//
// To translate more text: add the SAME key to both "en" and "hi", then use t("your.key") in a component.
import { createContext, useContext, useState } from "react";

const DICT = {
  en: {
    "common.loading": "Loading...",
    "common.tryAgain": "Try again",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.verified": "Verified",
    "common.by": "by",

    "nav.home": "Home",
    "nav.shop": "Shop",
    "nav.artisans": "Artisans",
    "nav.cart": "Cart",
    "nav.orders": "My orders",
    "nav.sell": "Seller dashboard",
    "nav.admin": "Admin",
    "nav.features": "Features",
    "nav.login": "Log in",
    "nav.register": "Sign up",
    "nav.logout": "Log out",

    "home.title": "Handmade by India's artisans",
    "home.subtitle": "Discover pottery, textiles, paintings and more, made by verified makers.",
    "home.cta": "Browse the shop",
    "home.featured": "Fresh from the workshop",
    "home.artisans": "Meet the makers",
    "home.viewAll": "View all",

    "shop.title": "Shop",
    "shop.search": "Search",
    "shop.searchPlaceholder": "Search handmade items...",
    "shop.category": "Category",
    "shop.allCategories": "All categories",
    "shop.minPrice": "Min price",
    "shop.maxPrice": "Max price",
    "shop.sort": "Sort by",
    "shop.sortNewest": "Newest",
    "shop.sortPriceLow": "Price: low to high",
    "shop.sortPriceHigh": "Price: high to low",
    "shop.apply": "Apply filters",
    "shop.clear": "Clear",
    "shop.emptyTitle": "No products found",
    "shop.emptyText": "Try a different search or clear the filters.",

    "product.addToCart": "Add to cart",
    "product.inStock": "in stock",
    "product.soldOut": "Sold out",
    "product.shipping": "Shipping",
    "product.soldBy": "Sold by",
    "product.similar": "You may also like",
    "product.quantity": "Quantity",
    "product.loginToBuy": "Log in as a buyer to purchase.",
    "product.added": "Added to cart.",

    "artisans.title": "Our artisans",
    "artisans.products": "products",
    "artisans.listingsBy": "Listings by",

    "auth.email": "Email",
    "auth.password": "Password",
    "auth.name": "Full name",
    "auth.iAm": "I want to",
    "auth.buyer": "Buy handmade items",
    "auth.artisan": "Sell my handmade items",
    "auth.craft": "Your craft",
    "auth.city": "City",
    "auth.state": "State",
    "auth.bio": "About you and your work",
    "auth.demoAccounts": "Demo accounts (password: demo1234)",
    "auth.noAccount": "New here?",
    "auth.haveAccount": "Already have an account?",
    "auth.createAccount": "Create account",

    "cart.title": "Your cart",
    "cart.emptyTitle": "Your cart is empty",
    "cart.emptyText": "Add some handmade items to get started.",
    "cart.subtotal": "Subtotal",
    "cart.shipping": "Shipping",
    "cart.total": "Total",
    "cart.checkout": "Proceed to checkout",
    "cart.remove": "Remove",
    "cart.estimate": "Prices are re-checked by the server when you place the order.",

    "checkout.title": "Checkout",
    "checkout.name": "Full name",
    "checkout.address": "Address",
    "checkout.city": "City",
    "checkout.pincode": "PIN code (6 digits)",
    "checkout.phone": "Phone (10 digits)",
    "checkout.payment": "Test payment",
    "checkout.paySuccess": "Simulate a successful payment",
    "checkout.payFail": "Simulate a failed payment",
    "checkout.place": "Place order (test payment)",

    "orders.title": "My orders",
    "orders.emptyTitle": "No orders yet",
    "orders.emptyText": "When you place an order it will show up here.",
    "orders.courier": "Courier",
    "orders.tracking": "Tracking ID",
    "orders.placedOn": "Placed on",
    "orders.customer": "Customer",

    "status.placed": "Order placed",
    "status.packed": "Packed",
    "status.processing": "Being prepared",
    "status.partially_shipped": "Partly shipped",
    "status.shipped": "Shipped",
    "status.delivered": "Delivered",

    "seller.title": "Seller dashboard",
    "seller.newListing": "+ New listing",
    "seller.listingsTab": "My listings",
    "seller.ordersTab": "Orders to ship",
    "seller.edit": "Edit",
    "seller.delete": "Delete",
    "seller.noListings": "You have no listings yet",
    "seller.noOrders": "No orders yet",
    "seller.updateStatus": "Update status",

    "listing.newTitle": "New listing",
    "listing.editTitle": "Edit listing",
    "listing.title": "Title",
    "listing.description": "Description",
    "listing.category": "Category",
    "listing.price": "Price (Rs)",
    "listing.stock": "Stock",
    "listing.shippingFee": "Shipping fee (Rs)",
    "listing.photos": "Photos (up to 5, JPG/PNG/WEBP, max 5 MB each)",
    "listing.aiHeading": "AI listing assistant",
    "listing.aiNotes": "Notes about your product (material, size, how it is made...)",
    "listing.aiButton": "Get AI suggestions",
    "listing.aiApply": "Use these suggestions in the form",
    "listing.aiPhotoAdvice": "Photo check (advisory)",
    "listing.confirm": "I have read and corrected the text above and confirm it is accurate.",
    "listing.publish": "Publish listing",
    "listing.saveChanges": "Save changes",

    "admin.title": "Admin panel",
    "admin.pending": "Pending",
    "admin.approved": "Approved",
    "admin.rejected": "Rejected",
    "admin.all": "All",
    "admin.approve": "Approve",
    "admin.reject": "Reject",
    "admin.reason": "Reason for rejection",
    "admin.none": "No artisans in this list",

    "features.title": "What works and what is planned",
    "features.intro": "Every feature is labelled honestly: implemented, demo-only or planned.",
  },
  hi: {
    "common.loading": "लोड हो रहा है...",
    "common.tryAgain": "फिर कोशिश करें",
    "common.save": "सहेजें",
    "common.cancel": "रद्द करें",
    "common.verified": "सत्यापित",
    "common.by": "द्वारा",

    "nav.home": "होम",
    "nav.shop": "दुकान",
    "nav.artisans": "कारीगर",
    "nav.cart": "कार्ट",
    "nav.orders": "मेरे ऑर्डर",
    "nav.sell": "विक्रेता डैशबोर्ड",
    "nav.admin": "एडमिन",
    "nav.features": "सुविधाएँ",
    "nav.login": "लॉग इन",
    "nav.register": "साइन अप",
    "nav.logout": "लॉग आउट",

    "home.title": "भारत के कारीगरों के हाथों से बना",
    "home.subtitle": "सत्यापित कारीगरों द्वारा बने मिट्टी के बर्तन, कपड़े, चित्र और बहुत कुछ खोजें।",
    "home.cta": "दुकान देखें",
    "home.featured": "कार्यशाला से ताज़ा",
    "home.artisans": "कारीगरों से मिलें",
    "home.viewAll": "सभी देखें",

    "shop.title": "दुकान",
    "shop.search": "खोजें",
    "shop.searchPlaceholder": "हस्तनिर्मित सामान खोजें...",
    "shop.category": "श्रेणी",
    "shop.allCategories": "सभी श्रेणियाँ",
    "shop.minPrice": "न्यूनतम मूल्य",
    "shop.maxPrice": "अधिकतम मूल्य",
    "shop.sort": "क्रमबद्ध करें",
    "shop.sortNewest": "सबसे नया",
    "shop.sortPriceLow": "मूल्य: कम से ज़्यादा",
    "shop.sortPriceHigh": "मूल्य: ज़्यादा से कम",
    "shop.apply": "फ़िल्टर लगाएँ",
    "shop.clear": "हटाएँ",
    "shop.emptyTitle": "कोई उत्पाद नहीं मिला",
    "shop.emptyText": "कोई दूसरा शब्द खोजें या फ़िल्टर हटाएँ।",

    "product.addToCart": "कार्ट में डालें",
    "product.inStock": "स्टॉक में",
    "product.soldOut": "बिक चुका",
    "product.shipping": "शिपिंग",
    "product.soldBy": "विक्रेता",
    "product.similar": "आपको ये भी पसंद आ सकते हैं",
    "product.quantity": "मात्रा",
    "product.loginToBuy": "खरीदने के लिए खरीदार के रूप में लॉग इन करें।",
    "product.added": "कार्ट में जोड़ दिया गया।",

    "artisans.title": "हमारे कारीगर",
    "artisans.products": "उत्पाद",
    "artisans.listingsBy": "इनके उत्पाद:",

    "auth.email": "ईमेल",
    "auth.password": "पासवर्ड",
    "auth.name": "पूरा नाम",
    "auth.iAm": "मैं चाहता/चाहती हूँ",
    "auth.buyer": "हस्तनिर्मित सामान खरीदना",
    "auth.artisan": "अपना हस्तनिर्मित सामान बेचना",
    "auth.craft": "आपकी कला",
    "auth.city": "शहर",
    "auth.state": "राज्य",
    "auth.bio": "आपके और आपके काम के बारे में",
    "auth.demoAccounts": "डेमो खाते (पासवर्ड: demo1234)",
    "auth.noAccount": "नए हैं?",
    "auth.haveAccount": "पहले से खाता है?",
    "auth.createAccount": "खाता बनाएँ",

    "cart.title": "आपका कार्ट",
    "cart.emptyTitle": "आपका कार्ट खाली है",
    "cart.emptyText": "शुरू करने के लिए कुछ हस्तनिर्मित सामान जोड़ें।",
    "cart.subtotal": "उप-योग",
    "cart.shipping": "शिपिंग",
    "cart.total": "कुल",
    "cart.checkout": "चेकआउट करें",
    "cart.remove": "हटाएँ",
    "cart.estimate": "ऑर्डर देते समय सर्वर कीमतें दोबारा जाँचता है।",

    "checkout.title": "चेकआउट",
    "checkout.name": "पूरा नाम",
    "checkout.address": "पता",
    "checkout.city": "शहर",
    "checkout.pincode": "पिन कोड (6 अंक)",
    "checkout.phone": "फ़ोन (10 अंक)",
    "checkout.payment": "टेस्ट भुगतान",
    "checkout.paySuccess": "सफल भुगतान का अनुकरण करें",
    "checkout.payFail": "असफल भुगतान का अनुकरण करें",
    "checkout.place": "ऑर्डर दें (टेस्ट भुगतान)",

    "orders.title": "मेरे ऑर्डर",
    "orders.emptyTitle": "अभी कोई ऑर्डर नहीं",
    "orders.emptyText": "ऑर्डर देने पर वह यहाँ दिखेगा।",
    "orders.courier": "कूरियर",
    "orders.tracking": "ट्रैकिंग आईडी",
    "orders.placedOn": "ऑर्डर की तारीख",
    "orders.customer": "ग्राहक",

    "status.placed": "ऑर्डर दिया गया",
    "status.packed": "पैक हो गया",
    "status.processing": "तैयारी में",
    "status.partially_shipped": "आंशिक रूप से भेजा गया",
    "status.shipped": "भेज दिया गया",
    "status.delivered": "पहुँच गया",

    "seller.title": "विक्रेता डैशबोर्ड",
    "seller.newListing": "+ नया उत्पाद",
    "seller.listingsTab": "मेरे उत्पाद",
    "seller.ordersTab": "भेजने वाले ऑर्डर",
    "seller.edit": "बदलें",
    "seller.delete": "हटाएँ",
    "seller.noListings": "अभी आपका कोई उत्पाद नहीं है",
    "seller.noOrders": "अभी कोई ऑर्डर नहीं",
    "seller.updateStatus": "स्थिति अपडेट करें",

    "listing.newTitle": "नया उत्पाद",
    "listing.editTitle": "उत्पाद बदलें",
    "listing.title": "शीर्षक",
    "listing.description": "विवरण",
    "listing.category": "श्रेणी",
    "listing.price": "मूल्य (रु)",
    "listing.stock": "स्टॉक",
    "listing.shippingFee": "शिपिंग शुल्क (रु)",
    "listing.photos": "फ़ोटो (अधिकतम 5, JPG/PNG/WEBP, प्रत्येक 5 MB तक)",
    "listing.aiHeading": "AI लिस्टिंग सहायक",
    "listing.aiNotes": "अपने उत्पाद के बारे में नोट्स (सामग्री, आकार, कैसे बना...)",
    "listing.aiButton": "AI सुझाव पाएँ",
    "listing.aiApply": "ये सुझाव फ़ॉर्म में भरें",
    "listing.aiPhotoAdvice": "फ़ोटो जाँच (सुझाव)",
    "listing.confirm": "मैंने ऊपर का पाठ पढ़कर ठीक कर लिया है और पुष्टि करता/करती हूँ कि यह सही है।",
    "listing.publish": "उत्पाद प्रकाशित करें",
    "listing.saveChanges": "बदलाव सहेजें",

    "admin.title": "एडमिन पैनल",
    "admin.pending": "लंबित",
    "admin.approved": "स्वीकृत",
    "admin.rejected": "अस्वीकृत",
    "admin.all": "सभी",
    "admin.approve": "स्वीकृत करें",
    "admin.reject": "अस्वीकार करें",
    "admin.reason": "अस्वीकार करने का कारण",
    "admin.none": "इस सूची में कोई कारीगर नहीं",

    "features.title": "क्या काम करता है और क्या आगे आएगा",
    "features.intro": "हर सुविधा पर ईमानदारी से लेबल है: implemented, demo-only या planned।",
  },
};

const LangContext = createContext(null);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => localStorage.getItem("dk_lang") || "en");
  // "chosen" becomes true once the visitor picks a language (the first-visit popup uses this).
  const [chosen, setChosen] = useState(() => {
    try {
      return Boolean(localStorage.getItem("dk_lang_chosen"));
    } catch {
      return true; // storage blocked: do not nag with a popup that can never be remembered
    }
  });
  const setLang = (l) => {
    try {
      localStorage.setItem("dk_lang", l);
      localStorage.setItem("dk_lang_chosen", "1");
    } catch {
      /* ignore: the choice just will not be remembered */
    }
    document.documentElement.lang = l;
    setLangState(l);
    setChosen(true);
  };
  // Falls back to English, then to the key itself, so a missing translation never breaks a page.
  const t = (key) => DICT[lang][key] || DICT.en[key] || key;
  return <LangContext.Provider value={{ lang, setLang, t, needsChoice: !chosen }}>{children}</LangContext.Provider>;
}

export const useLang = () => useContext(LangContext);
