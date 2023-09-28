<script>
  import Nav from "./Nav.svelte";
  import ValidationPage from "./ValidationPage.svelte";
  import SpecificationPage from "./SpecificationPage.svelte";

  import {
    projectTypeSpecifications,
    validationSettings,
    validationData,
    selectedPage,
  } from "./stores.js";

  let theSelectedPage;
  selectedPage.subscribe((value) => (theSelectedPage = value));

  // fetch the available repository types from the backend
  fetch("http://localhost:5000/project-types-specifications", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => (response = response.json()))
    .then((response) => {
      $projectTypeSpecifications = response.projectTypeSpecifications;
    })
    .catch((reason) => console.error(reason));

  if (localStorage.getItem("validationData")) {
    const rawRepoTypeMapping = localStorage.getItem("validationData");
    $validationData = JSON.parse(rawRepoTypeMapping);
  }

  // reset validation status
  for (const [key, value] of Object.entries($validationData)) {
    $validationData[key] = { ...value, status: "unknown" };
  }

  if (localStorage.getItem("validationSettings")) {
    const rawValidationSettings = localStorage.getItem("validationSettings");
    $validationSettings = JSON.parse(rawValidationSettings);
  }
</script>

<header>
  <Nav />
</header>

<main>
  {#if theSelectedPage == "Validation"}
    <div class="container container-fluid">
      <div class="row">
        <div class="col">
          <h1 class="mt-3 text-center">Validation</h1>
        </div>
      </div>
    </div>

    <ValidationPage />
  {:else if theSelectedPage == "Specification"}
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
