import React from "react";

export default function TrustTierBadge({ tier, showTooltip = true }) {
  const tiers = {
    master_artisan: {
      badge: "👑 Master Artisan",
      cls: "badge-master",
      label: "Master Heritage Artisan",
      desc: "Top artisan with 15+ orders, >=4.6 rating, and zero unresolved disputes.",
    },
    trusted_artisan: {
      badge: "⭐ Trusted Artisan",
      cls: "badge-trusted",
      label: "Trusted Artisan",
      desc: "Proven track record with 5+ completed orders, >=4.0 rating, and low dispute rate.",
    },
    verified_maker: {
      badge: "🛡️ Verified Maker",
      cls: "badge-verified-maker",
      label: "Verified Maker",
      desc: "Admin-verified identity, authentic handmade craft technique, and active listings.",
    },
    new_artisan: {
      badge: "🪴 New Maker",
      cls: "badge-new-artisan",
      label: "New Artisan",
      desc: "Recently joined artisan profile.",
    },
  };

  const info = tiers[tier] || tiers.new_artisan;

  return (
    <span
      className={`badge-tier ${info.cls}`}
      title={showTooltip ? `${info.label}: ${info.desc}` : undefined}
    >
      {info.badge}
    </span>
  );
}
