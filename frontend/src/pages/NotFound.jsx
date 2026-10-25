import { EmptyState } from "../components/States";

export default function NotFound() {
  return (
    <div className="container section">
      <EmptyState title="Page not found" text="The page you are looking for does not exist." actionTo="/" actionLabel="Go home" />
    </div>
  );
}
