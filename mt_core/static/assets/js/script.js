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
    const feeMessage = document.getElementById("fee-message");

    // Initialise Stripe
    const stripe = Stripe(window.STRIPE_PUBLIC_KEY);
    const elements = stripe.elements();

    const card = elements.create("card");
    card.mount("#card-element");


    // Amount selection
    amountButtons.forEach(button => {
        button.addEventListener("click", () => {
            selectedAmount = button.dataset.amount;

            amountButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            confirmationText.textContent =
                `You are tipping £${selectedAmount} to ${artistName}`;
            confirmationText.classList.remove("d-none");

            payButton.disabled = false;
            payButton.textContent = `Confirm and Tip £${selectedAmount}`;
            payConfirmation.textContent = `You are an absolute legend!\nThank you for supporting live music.`;

            if (feeMessage && feeMessage.textContent.trim() !== "") {
                feeMessage.classList.remove("d-none");
            }

            /* clearButton.classList.remove("d-none");*/
        });
    });

    // Clear selection
    /*clearButton.addEventListener("click", () => {
        selectedAmount = null;

        amountButtons.forEach(btn => btn.classList.remove("active"));
        confirmationText.classList.add("d-none");
        clearButton.classList.add("d-none");
    });*/

    // Pay button
    payButton.addEventListener("click", async () => {
        if (!selectedAmount) return;

        // If client secret already exists → confirm payment
        if (payButton.dataset.clientSecret) {
            payButton.disabled = true;
            payButton.textContent = "Processing...";

            const { error, paymentIntent } = await stripe.confirmCardPayment(
                payButton.dataset.clientSecret,
                {
                    payment_method: {
                        card: card
                    }
                }
            );

            if (error) {
                document.getElementById("card-errors").textContent = error.message;
                payButton.disabled = false;
                payButton.textContent = `Pay £${selectedAmount} Now`;
            } else if (paymentIntent.status === "succeeded") {
                payButton.textContent = "Payment Successful";

                // Hide card container
                document.getElementById("card-container").classList.add("d-none");

                // Show thank you message
                confirmationText.textContent = `Thank you for supporting ${artistName}!`;

                // Reset selection state
                selectedAmount = null;

                // Reset pay button
                payButton.disabled = true;
                payButton.textContent = "Select an Amount to Tip";
                delete payButton.dataset.clientSecret;

                // Re-enable amount buttons
                amountButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.classList.remove("active")
                });

                return;
            }
        }

        // Otherwise → create PaymentIntent first
        const response = await fetch(startUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                gig_id: tipSection.dataset.gigId,
                amount: parseInt(selectedAmount)
            })
        });

        const data = await response.json();
        console.log("Payment initiation response", data);

        if (data.client_secret) {
            payButton.textContent = `Pay £${selectedAmount} Now`;
            document.getElementById("card-container").classList.remove("d-none");
            payButton.dataset.clientSecret = data.client_secret;

            amountButtons.forEach(btn => btn.disabled = true);
        }
    });

});
