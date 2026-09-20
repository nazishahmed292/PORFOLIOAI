import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60svh] max-w-md flex-col items-start justify-center gap-4 px-4">
      <p className="text-sm font-medium text-muted-foreground">Error 404</p>
      <h1 className="text-3xl font-semibold">This page doesn't exist.</h1>
      <p className="text-muted-foreground">The link may be broken, or the page may have moved.</p>
      <Button asChild>
        <Link to="/">Go to the home page</Link>
      </Button>
    </div>
  );
}
