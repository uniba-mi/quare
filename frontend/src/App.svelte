<script>
  // has to stay to enable bootstrap js functionality
  // import * as bootstrap from "bootstrap";
  
  import Nav from "./Nav.svelte";
  import ValidationPage from "./ValidationPage.svelte";
  import SpecificationPage from "./SpecificationPage.svelte";

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
    .then((response) => (response.json()))
    .then((response) => {
      $projectTypeSpecifications = response.projectTypeSpecifications;
    })
    .catch((reason) => console.error(reason));

  // retrieve data from localStorage
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
    <div class="container container-fluid">
      <div class="row">
        <div class="col">
          <h1 class="mt-3 text-center">Validation</h1>
        </div>
      </div>
    </div>

    <ValidationPage />
  {:else if $selectedPage == "Specification"}
    <div class="container container-fluid">
      <div class="row">
        <div class="col">
          <h1 class="mt-3 text-center">Specification</h1>
        </div>
      </div>
    </div>

    <SpecificationPage />
  {:else}
    <div class="container container-fluid">
      <div class="row">
        <div class="col">
          <h1 class="mt-3 text-center">You should not be here!</h1>
        </div>
      </div>
    </div>
  {/if}
</main>
