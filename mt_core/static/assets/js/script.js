console.log("Script Loaded");

document.addEventListener("DOMContentLoaded", () => {
    const tipSection = document.getElementById("tip-section");
    if (!tipSection) return;

    let selectedAmount = null;
    const artistName = tipSection.dataset.artistName;
    const startUrl = tipSection.dataset.startUrl;
    const csrfToken = tipSection.dataset.csrf;

    const amountButtons = document.querySelectorAll(".tip-btn");
    const confirmationText = document.getElementById("tip-confirmation");
    const clearButton = document.getElementById("clear-tip");
    const payButton = document.getElementById("pay-btn");
    const payConfirmation = document.getElementById("pay-confirmation");

    // Amount selection
    amountButtons.forEach(button => {
        button.addEventListener("click", () => {
            selectedAmount = button.dataset.amount;

            amountButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            confirmationText.textContent =
                `You are tipping £${selectedAmount} to ${artistName}`;
            confirmationText.classList.remove("d-none");

            /* clearButton.classList.remove("d-none");*/

            payButton.disabled = false;
            payButton.textContent = `Confirm and Tip £${selectedAmount}`;
            payConfirmation.textContent = `You are an absolute legend!\nThank you for supporting live music.`;

        });
    });

    // Clear selection
    /*clearButton.addEventListener("click", () => {
        selectedAmount = null;

        amountButtons.forEach(btn => btn.classList.remove("active"));
        confirmationText.classList.add("d-none");
        clearButton.classList.add("d-none");
    });*/

    // Pay button (stubbed)
    payButton.addEventListener("click", () => {
        if (!selectedAmount) return;

        fetch(startUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                amount: selectedAmount
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Payment initiation response", data);
        })
        .catch(error => {
            console.error("Payment initiation error", error);
        });
    });

});
