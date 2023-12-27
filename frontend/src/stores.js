import { writable } from "svelte/store";

export const selectedPage = writable("Validation");
export const projectTypeSpecifications = writable({});

export const validationSettings = writable({
  accessToken: ""
});

export const validationData = writable({
  "0": {
    repoName: "",
    repoType: "",
    status: "unknown",
    numberOfCriteria: 0,
    numberOfFulfilledCriteria: undefined,
    report: "",
    verbalized: "",
  },
});
