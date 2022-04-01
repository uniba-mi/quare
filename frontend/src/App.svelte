<script>
  import { navOptions } from "./Nav.svelte";
  import { projectTypeSpecifications, validationSettings, validationData } from "./stores.js";
  let selected = navOptions[0];
  let intSelected = 0;

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

  // change the selected component (the event.originalTarget.id is not accessible in Chrome so switched to event.srcElement.id)
  const changeComponent = (event) => {
    document.getElementById(intSelected).classList.remove("active");
    selected = navOptions[event.srcElement.id];
    intSelected = event.srcElement.id;
    event.srcElement.classList.add("active");
  };
</script>

<main>
  <!--app navigation -->
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <h1 class="display-2 navbar-brand">QuaRe</h1>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNavAltMarkup"
        aria-controls="navbarNavAltMarkup"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon" />
      </button>
      <div class="collapse navbar-collapse" id="navbarNavAltMarkup">
        <div class="navbar-nav">
          <a
            class="nav-link active"
            on:click={changeComponent}
            href="#{navOptions[0].page}"
            id="0">{navOptions[0].page}</a
          >
          {#each navOptions.slice(1) as option, i}
            <a
              class="nav-link"
              on:click={changeComponent}
              href="#{option.page}"
              id={i + 1}>{option.page}</a
            >
          {/each}
        </div>
      </div>
    </div>
  </nav>

  <!-- content wrapper -->
  <div class="container-fluid">
    <div class="row">
      <div class="col">
        <h1 class="mt-3 text-center">{selected.page}</h1>
      </div>
    </div>
    <!-- this is where the main content is placed -->
    <svelte:component this={selected.component} />
  </div>
</main>
