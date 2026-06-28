import { config } from "../config";
import { ExpiryApiClient } from "./generated/client";

let tokenProvider: () => Promise<string | null> = async () => null;

export function setTokenProvider(provider: () => Promise<string | null>) {
  tokenProvider = provider;
}

export const apiClient = new ExpiryApiClient(config.apiBaseUrl, () => tokenProvider());
