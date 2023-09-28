<script>
  import { projectTypeSpecifications } from "./stores.js";

  let currentView = "shacl";

  const toggleSpecView = () => {
    if (currentView == "shacl") {
      currentView = "owl";
    } else if (currentView == "owl") {
      currentView = "shacl";
    }
  };
</script>

<div class="container-fluid">
  <div class="row justify-content-center mb-3">
    <div class="col-8">
      <h5 class="text-center">
        On this page, the available project types and the corresponding quality
        criteria can be reviewed.
      </h5>
    </div>
  </div>

  <div class="row justify-content-center mb-3">
    <div class="col">
      <button on:click={toggleSpecView} class="btn btn-primary"
        >Toggle OWL/SHACL Specifications</button
      >
    </div>
  </div>

  <div class="accordion" id="accordionExample">
    {#if currentView == "shacl"}
      <p>Project Type Specifications (SHACL Approach):</p>
      {#each Object.keys($projectTypeSpecifications[currentView]) as typeName, i}
        <div class="accordion-item">
          <h2 class="accordion-header" id="heading-{i}">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapse-{i}"
              aria-expanded="true"
              aria-controls="collapse-{i}"
            >
              {typeName}
            </button>
          </h2>
          <div
            id="collapse-{i}"
            class="accordion-collapse collapse"
            aria-labelledby="heading-{i}"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body">
              This project type has the following quality criteria:
              <ul>
                {#each $projectTypeSpecifications[currentView][typeName] as constraint, _}
                  <li>{constraint}</li>
                {/each}
              </ul>
            </div>
          </div>
        </div>
      {/each}
    {:else if currentView == "owl"}
      <p>Project Type Specifications (OWL Approach):</p>
      {#each Object.keys($projectTypeSpecifications[currentView]) as typeName, i}
        <div class="accordion-item">
          <h2 class="accordion-header" id="heading-{i}">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapse-{i}"
              aria-expanded="true"
              aria-controls="collapse-{i}"
            >
              {typeName}
            </button>
          </h2>
          <div
            id="collapse-{i}"
            class="accordion-collapse collapsed"
            aria-labelledby="heading-{i}"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body">
              This project type has the following quality criteria:
              <ul>
                {#each $projectTypeSpecifications[currentView][typeName] as constraint, _}
                  <li>{constraint}</li>
                {/each}
              </ul>
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>
