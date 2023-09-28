<script>
  import { selectedPage } from "./stores";

  const changePage = (event) => {
    document.querySelector(".nav-link.active").classList.remove("active");
    event.srcElement.classList.add("active");
    selectedPage.set(event.srcElement.textContent);
  };
</script>

<div class="container-fluid p-0">
  <div class="row">
    <div class="col">
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
          <span class="navbar-brand mb-0 h1">QuaRe</span>
          <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarSupportedContent"
            aria-controls="navbarSupportedContent"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span class="navbar-toggler-icon" />
          </button>
          <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav">
              <li class="nav-item">
                <a
                  class="nav-link active"
                  on:click={changePage}
                  href="#Validation">Validation</a
                >
              </li>
              <li class="nav-item">
                <a
                  class="nav-link"
                  on:click={changePage}
                  href="#Specification">Specification</a
                >
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </div>
  </div>
</div>
