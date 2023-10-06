<script>
  import * as bootstrap from "bootstrap";
  import {
    mode,
    projectTypeSpecifications,
    validationSettings,
    validationData,
  } from "../stores.js";
  import {
    CheckCircleIcon,
    AlertCircleIcon,
    CircleIcon,
  } from "svelte-feather-icons";

  export let revealValidationResult;

  const handleMinusButtonPress = () => {
    const currentLength = Object.keys($validationData).length;
    if (currentLength > 1) {
      delete $validationData[currentLength - 1];
      // required to trigger rerender
      $validationData = $validationData;
    }
  };

  const handlePlusButtonPress = () => {
    const currentLength = Object.keys($validationData).length;
    $validationData[currentLength] = {
      repoName: "",
      repoType: "",
      status: "unknown",
      report: "",
      verbalized: "",
    };
  };

  const handleSaveButtonPress = () => {
    localStorage.setItem("mode", JSON.stringify($mode));
    localStorage.setItem(
      "validationSettings",
      JSON.stringify($validationSettings)
    );
    localStorage.setItem("validationData", JSON.stringify($validationData));

    const statusToast = document.getElementById("liveToast");

    const toastBootstrap =
      bootstrap.Toast.getOrCreateInstance(statusToast);
    toastBootstrap.show();
  };

  const handleValidationRequest = () => {
    Object.keys($validationData).forEach((index) => {
      const request_body = {
        accessToken: $validationSettings["accessToken"],
        method: $mode,
        repoName: $validationData[index]["repoName"],
        repoType: $validationData[index]["repoType"],
      };

      $validationData[index]["status"] = "loading";

      fetch("http://localhost:5000/validate", {
        method: "POST",
        headers: {
          "Content-Type": "text/plain",
        },
        body: JSON.stringify(request_body),
      })
        .then((response) => response.json())
        .then((response) => {
          switch (response["returnCode"]) {
            case 0:
              $validationData[index]["status"] = "success";
              break;
            case 1:
              console.log(response);
              $validationData[index]["status"] = "failure";
              $validationData[index]["report"] = response["report"];
              $validationData[index]["verbalized"] = response["verbalized"];
              break;
            default:
              $validationData[index]["status"] = "unknown";
          }
        })
        .catch((reason) => console.error(reason));
    });
  };

  const handleResultButtonPress = (event) => {
    const index = event.srcElement.id.split("-")[2];
    revealValidationResult(
      $validationData[index]["report"],
      $validationData[index]["verbalized"]
    );
  };
</script>

<div class="row justify-content-center mb-3">
  <div class="col-8">
    <form
      id="validation-form"
      on:submit|preventDefault={handleValidationRequest}
    >
      <!-- GitHub access token can be specified only once -->
      <div class="row mb-3">
        <div class="col">
          <label for="validation-access-token" class="form-label"
            >GitHub Access Token</label
          >
          <input
            class="form-control"
            id="validation-access-token"
            type="password"
            bind:value={$validationSettings.accessToken}
          />
          <div id="passwordHelpBlock" class="form-text">
            Required for private repositories and higher rate limit.
          </div>
        </div>
      </div>

      <!-- one row for each repository to be validated -->
      {#each { length: Object.keys($validationData).length } as _, i}
        <div class="row mb-3">
          <div class="col">
            <label for="validation-repository-{i}" class="form-label"
              >Repository Name</label
            >
            <input
              class="form-control"
              id="validation-repository-{i}"
              type="text"
              bind:value={$validationData[i]["repoName"]}
              required
            />
          </div>
          <div class="col">
            <label for="validation-type-{i}" class="form-label"
              >Project Type</label
            >
            <select
              class="form-select"
              id="validation-type-{i}"
              bind:value={$validationData[i]["repoType"]}
              required
            >
              {#if $mode == "shacl"}
                {#each Object.keys($projectTypeSpecifications.shacl) as typeName, _}
                  <option>{typeName}</option>
                {/each}
              {:else}
                {#each Object.keys($projectTypeSpecifications.owl) as typeName, _}
                  <option>{typeName}</option>
                {/each}
              {/if}
            </select>
          </div>
          <div class="col-2">
            <div class="row justify-content-center">
              <p class="form-label">Result</p>
              <div class="btn-group" role="group">
                {#if $validationData[i]["status"] == "success"}
                  <button class="btn btn-success disabled">
                    <CheckCircleIcon size="20" />
                  </button>
                {:else if $validationData[i]["status"] == "failure"}
                  <button class="btn btn-danger disabled">
                    <AlertCircleIcon size="20" />
                  </button>
                  <button
                    on:click|preventDefault={handleResultButtonPress}
                    class="btn btn-outline-danger"
                    id="result-button-{i}"
                  >
                    View
                  </button>
                {:else if $validationData[i]["status"] == "loading"}
                  <button class="btn btn-secondary disabled">
                    <span
                      class="spinner-border spinner-border"
                      style="width: 1rem; height: 1rem;"
                      role="status"
                      aria-hidden="true"
                    />
                  </button>
                {:else if $validationData[i]["status"] == "unknown"}
                  <button class="btn btn-secondary disabled">
                    <CircleIcon size="20" />
                  </button>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/each}

      <!-- form buttons -->
      <div class="row">
        <div class="col-6">
          <div class="btn-group" role="group" aria-label="Form buttons">
            <!-- button for removing last form -->
            <button
              on:click|preventDefault={handleMinusButtonPress}
              class="btn btn-outline-secondary">-</button
            >
            <!-- button for adding another form -->
            <button
              on:click|preventDefault={handlePlusButtonPress}
              class="btn btn-outline-secondary">+</button
            >
            <!-- button for saving the form information -->
            <button
              on:click|preventDefault={handleSaveButtonPress}
              class="btn btn-outline-primary">Save Entries</button
            >
            <!-- submission button -->
            <button type="submit" class="btn btn-primary">Submit</button>
          </div>
        </div>
      </div>
    </form>
  </div>

  <!-- toast for status messages -->
  <div class="toast-container position-fixed bottom-0 end-0 p-3">
    <div
      id="liveToast"
      class="toast text-bg-success"
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div class="toast-header">
        <strong class="me-auto">Success</strong>
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="toast"
          aria-label="Close"
        />
      </div>
      <div class="toast-body">Entries have been saved!</div>
    </div>
  </div>
</div>
