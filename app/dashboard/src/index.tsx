import { ChakraProvider, localStorageManager } from "@chakra-ui/react";
import dayjs from "dayjs";
import Duration from "dayjs/plugin/duration";
import LocalizedFormat from "dayjs/plugin/localizedFormat";
import RelativeTime from "dayjs/plugin/relativeTime";
import Timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import "locales/i18n";
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "react-query";
import { queryClient } from "utils/react-query";
import { updateThemeColor } from "utils/themeColor";
import { theme } from "../chakra.config";
import App from "./App";
import "index.scss";

// Log all fetch calls (browser console)
const originalFetch = window.fetch.bind(window);
window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const method = (init?.method || "GET").toUpperCase();
  const url = typeof input === "string" ? input : (input as URL).toString();
  const headers = new Headers(init?.headers || {});
  if (headers.has("authorization")) headers.set("authorization", "REDACTED");
  if (headers.has("Authorization")) headers.set("Authorization", "REDACTED");
  console.log("[FETCH]", method, url, { ...init, headers: Object.fromEntries(headers.entries()) });
  try {
    const res = await originalFetch(input, init);
    console.log("[FETCH OK]", method, url, res.status);
    return res;
  } catch (err) {
    console.error("[FETCH ERR]", method, url, err);
    throw err;
  }
};

dayjs.extend(Timezone);
dayjs.extend(LocalizedFormat);
dayjs.extend(utc);
dayjs.extend(RelativeTime);
dayjs.extend(Duration);

updateThemeColor(localStorageManager.get() || "light");

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ChakraProvider>
  </React.StrictMode>
);
