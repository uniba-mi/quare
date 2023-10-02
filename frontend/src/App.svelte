<script>
  import Nav from "./lib/Nav.svelte";
  import ValidationPage from "./lib/ValidationPage.svelte";
  import SpecificationPage from "./lib/SpecificationPage.svelte";

  import {
    mode,
    projectTypeSpecifications,
    validationSettings,
    validationData,
    selectedPage,
  } from "./stores.js";

  // fetch the available repository types from the backend
  fetch("http://localhost:5000/project-type-specifications", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((response) => {
      $projectTypeSpecifications = response.projectTypeSpecifications;
    })
    .catch((reason) => console.error(reason));

  // load data from localStorage
  if (localStorage.getItem("mode")) {
    const rawRepoTypeMapping = localStorage.getItem("mode");
    $mode = JSON.parse(rawRepoTypeMapping);
  }

  if (localStorage.getItem("validationData")) {
    const rawRepoTypeMapping = localStorage.getItem("validationData");
    $validationData = JSON.parse(rawRepoTypeMapping);
  }

  if (localStorage.getItem("validationSettings")) {
    const rawValidationSettings = localStorage.getItem("validationSettings");
    $validationSettings = JSON.parse(rawValidationSettings);
  }

  // reset validation status
  for (const [key, value] of Object.entries($validationData)) {
    $validationData[key] = { ...value, status: "unknown" };
  }
</script>

<header>
  <Nav />
</header>

<main>
  {#if $selectedPage == "Validation"}
    <ValidationPage />
  {:else if $selectedPage == "Specification"}
    <SpecificationPage />
  {/if}
</main>
