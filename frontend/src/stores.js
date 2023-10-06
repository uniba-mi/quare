import { writable } from "svelte/store";

export const mode = writable("shacl")

export const projectTypeSpecifications = writable({ owl: {}, shacl: {} });

export const validationSettings = writable({
  accessToken: ""
});

export const validationData = writable({
  "0": {
    repoName: "",
    repoType: "",
    status: "unknown",
    report: "",
    verbalized: "",
  },
});

export let selectedPage = writable("Validation");
