import React from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
} from "react-router-dom";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import App from "./App";

import "./index.css";
import "./styles/motion.css";
import "./styles/responsive.css";
import "./styles/command-palette.css";

const queryClient =
  new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: 1,
        refetchOnWindowFocus:
          false,
      },
    },
  });

const rootElement =
  document.getElementById(
    "root",
  );

if (!rootElement) {
  throw new Error(
    "Root element not found",
  );
}

ReactDOM.createRoot(
  rootElement,
).render(
  <React.StrictMode>
    <QueryClientProvider
      client={queryClient}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
