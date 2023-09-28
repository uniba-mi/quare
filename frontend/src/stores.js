import { writable } from "svelte/store";

export const projectTypeSpecifications = writable({ owl: {}, shacl: {} });

export const validationSettings = writable({
  accessToken: "",
  method: "",
});

export const validationData = writable({
  "0": {
    repoName: "",
    repoType: "",
    status: "unknown",
    message: "",
    verbalized: "",
  },
});

export let selectedPage = writable("Validation");
