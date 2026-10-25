import { Link, useParams } from "react-router-dom";
import { Notice } from "../components/States";
import { FeatureTag } from "../components/Tag";

const POLICIES = {
  terms: {
    title: "Terms of use",
    body: [
      "Digi Karigari is a college demonstration project. It is not a real shop.",
      "Sample artisans and products are fictional. Do not enter real personal details or payment information.",
      "Artisans are responsible for the accuracy of their listings, including text suggested by the AI assistant.",
    ],
  },
  privacy: {
    title: "Privacy policy",
    body: [
      "This demo stores the details you enter (name, email, address, orders) in a local database on the computer running it.",
      "Passwords are stored as salted hashes, not as plain text. No data is sold or shared.",
      "When the AI assistant is in live mode, the product photo and notes are sent to the configured AI provider to produce suggestions.",
    ],
  },
  shipping: {
    title: "Shipping policy",
    body: [
      "Each artisan ships their own items. A shipping fee is set per product and charged once per product in your order.",
      "Artisans type the courier name and tracking ID by hand. The app does not connect to any courier service.",
    ],
  },
  refunds: {
    title: "Refund policy",
    body: [
      "No real payments happen in this demo, so there is nothing to refund.",
      "Refunds, disputes and reviews are planned features and are not implemented yet.",
    ],
  },
};

export default function Policy() {
  const { slug } = useParams();
  const policy = POLICIES[slug];
  if (!policy)
    return (
      <div className="container section">
        <Notice kind="error">Page not found.</Notice>
        <Link to="/">Home</Link>
      </div>
    );
  return (
    <div className="container narrow-lg section">
      <h1>{policy.title}</h1>
      <p>
        <FeatureTag status="demo-only" /> Placeholder text for the demo. It is not legal advice; a real launch needs reviewed policies.
      </p>
      {policy.body.map((p) => (
        <p key={p}>{p}</p>
      ))}
    </div>
  );
}
