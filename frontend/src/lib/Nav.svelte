<script>
  import { selectedPage } from "../stores.js";

  const changePage = (event) => {
    document.querySelector(".nav-link.active").classList.remove("active");
    event.srcElement.classList.add("active");
    $selectedPage = event.srcElement.textContent;
  };
</script>

<div class="container-fluid p-0">
  <div class="row">
    <div class="col">
      <nav class="navbar navbar-expand navbar-dark bg-dark">
        <div class="container-fluid">
          <div class="collapse navbar-collapse">
            <span class="navbar-brand mb-0 h1">QuaRe</span>
            <ul class="navbar-nav">
              <li class="nav-item">
                <a
                  class="nav-link active"
                  on:click={changePage}
                  href="#Validation">Validation</a
                >
              </li>
              <li class="nav-item">
                <a class="nav-link" on:click={changePage} href="#Specification"
                  >Specification</a
                >
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </div>
  </div>
</div>
