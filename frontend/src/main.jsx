import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App.jsx";
import { Button, EmptyState } from "./components/ui.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import DocumentDetail from "./pages/DocumentDetail.jsx";
import Documents from "./pages/Documents.jsx";
import NewReview from "./pages/NewReview.jsx";
import NewRulebook from "./pages/NewRulebook.jsx";
import Review from "./pages/Review.jsx";
import RulebookDetail from "./pages/RulebookDetail.jsx";
import Rulebooks from "./pages/Rulebooks.jsx";
import "./index.css";

function NotFound() {
  return (
    <EmptyState icon="search" title="Page not found" action={<Button to="/">Go to the dashboard</Button>}>
      The link may be out of date.
    </EmptyState>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "new-review", element: <NewReview /> },
      { path: "reviews/:reviewId", element: <Review /> },
      { path: "documents", element: <Documents /> },
      { path: "documents/:documentId", element: <DocumentDetail /> },
      { path: "rulebooks", element: <Rulebooks /> },
      { path: "rulebooks/new", element: <NewRulebook /> },
      { path: "rulebooks/:key", element: <RulebookDetail /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
