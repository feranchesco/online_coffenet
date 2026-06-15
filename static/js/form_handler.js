const form = document.querySelector(".auth-form");
const submitBtn = document.getElementById("submitBtn");
const loadingBtn = document.getElementById("loadingBtn");
const textBtn = document.getElementById("textBtn");
const emailInput = document.getElementById("id_email")

const inputs = form.querySelectorAll("input");

function checkForm() {
    let allFilled = true;

    inputs.forEach(input => {
        if (input === emailInput) return;
        if (input.value.trim() === "") {
            allFilled = false;
        }
    });

    submitBtn.disabled = !allFilled;
}

// بررسی هنگام تایپ
inputs.forEach(input => {
    input.addEventListener("input", checkForm);
});

form.addEventListener("submit", function () {
    submitBtn.disabled = true;
    textBtn.style.display = "none";
    loadingBtn.style.display = "inline-flex";
});