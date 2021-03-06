<script>
  import {
    projectTypeSpecifications,
    validationSettings,
    validationData,
  } from "./stores.js";
  import {
    CheckCircleIcon,
    AlertCircleIcon,
    CircleIcon,
  } from "svelte-feather-icons";

  let validationResultMessage = "";
  let validationResultVerbalized = "";

  const handleMinusButtonPress = () => {
    const currentLength = Object.keys($validationData).length;
    if (currentLength > 1) {
      // in contrast to using delete, this results in a rerender
      const { [currentLength - 1]: _, ...rest } = $validationData;
      $validationData = rest;
    }
  };

  const handlePlusButtonPress = () => {
    const currentLength = Object.keys($validationData).length;
    $validationData[currentLength] = {
      repoName: "",
      repoType: "",
      status: "unknown",
      message: "",
      verbalized: "",
    };
  };

  const handleSaveButtonPress = () => {
    localStorage.setItem(
      "validationSettings",
      JSON.stringify($validationSettings)
    );
    localStorage.setItem("validationData", JSON.stringify($validationData));
  };

  const handleValidationRequest = () => {
    validationResultMessage = "";
    validationResultVerbalized = "";

    Object.keys($validationData).forEach((index) => {
      const request_body = {
        accessToken: $validationSettings["accessToken"],
        method: $validationSettings["method"],
        repoName: $validationData[index]["repoName"],
        repoType: $validationData[index]["repoType"],
      };

      console.log(request_body);

      $validationData[index]["status"] = "loading";

      fetch("http://localhost:5000/validate", {
        method: "POST",
        headers: {
          "Content-Type": "text/plain",
        },
        body: JSON.stringify(request_body),
      })
        .then((response) => (response = response.json()))
        .then((response) => {
          switch (response["returnCode"]) {
            case 0:
              $validationData[index]["status"] = "success";
              break;
            case 1:
              console.log(response);
              $validationData[index]["status"] = "failure";
              $validationData[index]["message"] = response["message"];
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
    validationResultMessage = $validationData[index]["message"];
    validationResultVerbalized = $validationData[index]["verbalized"];
  };
</script>

<div class="row justify-content-sm-center mb-3">
  <div class="col-sm-8">
    <h5 class="text-center">
      On this page, GitHub repositories can be validated against a predefined
      project type which corresponds to a set of quality criteria.
    </h5>
  </div>
</div>

<form
  class="row mb-3"
  id="validation-form"
  on:submit|preventDefault={handleValidationRequest}
>
  <!-- access can be specified only once -->
  <div class="mb-3 col-12">
    <label for="validation-access-token" class="form-label"
      >GitHub Access Token (required for private repositories)</label
    >
    <input
      class="form-control"
      id="validation-access-token"
      type="text"
      bind:value={$validationSettings.accessToken}
    />
  </div>

  {#each { length: Object.keys($validationData).length } as _, i}
    <div class="mb-3 col-5">
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
    <div class="mb-3 col-5">
      <label for="validation-type-{i}" class="form-label"
        >Which type should the repository have?</label
      >
      <select
        class="form-control"
        id="validation-type-{i}"
        bind:value={$validationData[i]["repoType"]}
        required
      >
        {#each Object.keys($projectTypeSpecifications.owl) as typeName, _}
          <option>{typeName}</option>
        {/each}
      </select>
    </div>
    <div class="mb-3 col-2">
      <div class="row justify-content-sm-center">
        <p class="form-label">Result:</p>
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
                class="spinner-border spinner-border-sm"
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
  {/each}
  <div class="row">
    <div class="col-sm-12">
      <div class="form-check form-check-inline">
        <!-- use the shacl validator -->
        <input
          type="radio"
          class="form-check-input"
          name="method"
          id="shacl"
          autocomplete="off"
          value="shacl"
          bind:group={$validationSettings["method"]}
        />
        <label class="form-check-label" for="shacl">SHACL</label>
      </div>
      <div class="form-check form-check-inline">
        <!-- use the owl validator -->
        <input
          type="radio"
          class="form-check-input"
          name="method"
          id="owl"
          autocomplete="off"
          value="owl"
          bind:group={$validationSettings["method"]}
        />
        <label class="form-check-label" for="owl">OWL</label>
      </div>
    </div>
  </div>

  <div class="btn-group col-sm-4" role="group" aria-label="Form buttons">
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
</form>

<div class="row justify-content-sm-center">
  {#if validationResultMessage}
    <div class="col-sm-6">
      <p>Raw Explanation:</p>
      <textarea class="form-control" rows="15" readonly>
        {validationResultMessage}
      </textarea>
    </div>
  {/if}
  {#if validationResultVerbalized}
    <div class="col-sm-6">
      <p>Verbalized Explanation:</p>
      <textarea class="form-control" rows="15" readonly>
        {validationResultVerbalized}
      </textarea>
    </div>
  {/if}
</div>

<style>
  textarea {
    font-size: 8pt;
  }
</style>
