<script>
  import { projectTypeSpecifications } from "../stores.js";
</script>

<div class="container-fluid">
  <div class="row">
    <div class="col">
      <h1 class="mt-3 text-center">Specification</h1>
    </div>
  </div>
  <div class="row justify-content-center mb-3">
    <div class="col-8">
      <h5 class="text-center">
        On this page, the available project types and the corresponding quality
        criteria can be reviewed.
      </h5>
    </div>
  </div>

  <div class="accordion" id="accordionExample">
    <p>Project Type Specifications:</p>
    {#each Object.keys($projectTypeSpecifications) as typeName, i}
      <div class="accordion-item">
        <h2 class="accordion-header" id="heading-{i}">
          <button
            class="accordion-button collapsed"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#collapse-{i}"
            aria-expanded="false"
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
              {#each $projectTypeSpecifications[typeName] as constraint}
                <li>{constraint}</li>
              {/each}
            </ul>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>
